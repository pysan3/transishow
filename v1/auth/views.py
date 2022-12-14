from fastapi import BackgroundTasks, HTTPException, status, Request, Response
from pydantic import EmailStr
from sqlalchemy.orm import Session

from core.auth import auth
from core.mail import send_mail
from core.settings import settings
from models.users import User
from schemas.users import UserCreate
from schemas.auth import LoginDetails, RefreshDetails, Token, EmailSchema, ResetPasswordDetails


def get_user_by_email(email: EmailStr, db: Session) -> User | None:
    email = EmailStr(email.lower())
    user = db.query(User).filter_by(email=email).first()
    return user


def generate_verification_email_link(request: Request, email):
    email_token = auth.encode_verification_token(email)
    base_url = request.base_url
    frontend_url = settings.FRONTEND_URL
    verification_link = f"{frontend_url or base_url}v1/auth/email-verify?token={email_token}"
    return verification_link


def send_verification_email(background_tasks: BackgroundTasks, email: EmailStr, request: Request):
    verification_link = generate_verification_email_link(request, email=email)
    email_schema = EmailSchema(emails=[email],
                               body={"verification_link": verification_link, "company_name": settings.PROJECT_TITLE})
    send_mail(background_tasks=background_tasks, subject=f"{settings.PROJECT_TITLE} email confirmation",
              emails=email_schema, template_name="email_verification.html")


def create_user(user_details: UserCreate, db: Session, background_tasks: BackgroundTasks, request: Request):
    user_details.email = EmailStr(user_details.email.lower())
    old_user = get_user_by_email(email=user_details.email, db=db)
    if old_user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "User with this email already exists")
    user_details_dict = user_details.dict()
    del user_details_dict['password']
    new_user = User(**user_details_dict, password=auth.hash_password(user_details.password))
    db.add(new_user)
    send_verification_email(background_tasks, email=user_details.email, request=request)
    db.commit()
    db.refresh(new_user)
    return new_user


def login_user(user_details: LoginDetails, db: Session, bg_tasks: BackgroundTasks,
               request: Request, response: Response):
    user_details.email = EmailStr(user_details.email.lower())
    user = get_user_by_email(email=user_details.email, db=db)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User with this email doesn't exist!")
    if not auth.verify_password(user_details.password, str(user.password)):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect password!")
    if not user.email_verified:
        send_verification_email(bg_tasks, user_details.email, request)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email isn't verified. Check your mail.")

    access_token = auth.encode_token(EmailStr(user.email))
    refresh_token = auth.encode_refresh_token(EmailStr(user.email))
    response.set_cookie(key='refresh_token', value=refresh_token,
                        httponly=True, secure=True, samesite='none')
    return Token(access_token=access_token, token_type="bearer")


def refresh_token(response: Response, request: Request):
    former_token = request.cookies.get('refresh_token')
    if former_token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token is wrong.")
    new_access_token, new_refresh_token = auth.refresh_token(former_token)
    response.set_cookie(key='refresh_token', value=new_refresh_token, httponly=True, secure=True, samesite='none')
    return Token(access_token=new_access_token, token_type="bearer")


def logout_user(response: Response):
    response.delete_cookie('refresh_token')
    return {"msg": "Okay"}


def verify_email(token: str, db: Session):
    email = auth.verify_email(token)
    user = get_user_by_email(email, db)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid user... Please create an account")
    if user.email_verified:
        raise HTTPException(status.HTTP_304_NOT_MODIFIED, "User email already verified!")
    user.email_verified = True
    user.is_active = True
    db.commit()
    return {"msg": "Email verified successfully"}


def resend_verification_email(email: EmailStr, bg_tasks: BackgroundTasks, request: Request, db: Session):
    user = get_user_by_email(email, db)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User with this email doesn't exist!")
    if user.email_verified:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already verified!")
    send_verification_email(bg_tasks, email, request)
    return {"msg": "Verification mail has been resent!"}


def reset_password(email: EmailStr, bg_tasks: BackgroundTasks, request: Request, db: Session):
    user = get_user_by_email(email, db)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User account not found")
    token = auth.encode_reset_token(email)
    emails = EmailSchema(emails=[email, ], body={
        "reset_link": f"{settings.FRONTEND_URL or request.base_url}reset-password-confirm?token={token}",
        "company_name": settings.PROJECT_TITLE
    })
    send_mail(background_tasks=bg_tasks, subject=f"{settings.PROJECT_TITLE} Password Reset",
              emails=emails, template_name="reset_password.html")
    return True


def reset_password_verification(body: ResetPasswordDetails, request: Request, bg_tasks: BackgroundTasks, db: Session):
    email = auth.verify_reset_token(body.token)
    user = get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "User not found.")
    if body.password != body.re_password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Passwords aren't equal!")
    if auth.verify_password(body.password, str(user.password)):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot used same password as before!")
    user.password = auth.hash_password(body.password)  # type: ignore
    db.commit()

    token = auth.encode_refresh_token(EmailStr(user.email))
    emails = EmailSchema(emails=[email], body={
        "reset_link": f"{settings.FRONTEND_URL or request.base_url}reset-password-confirm?token={token}",
        "company_name": settings.PROJECT_TITLE
    })
    send_mail(background_tasks=bg_tasks, subject=f"{settings.PROJECT_TITLE} Password Reset",
              emails=emails, template_name="reset_password_confirmation.html")

    return True
