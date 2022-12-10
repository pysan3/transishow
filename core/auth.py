import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from core.settings import settings
from models.users import Token
from .database import SessionLocal

db: Session = SessionLocal()


class AuthPayload(BaseModel):
    exp: datetime
    iat: datetime
    sub: EmailStr
    scope: str = 'access_token'

    def encode(self):
        return jwt.encode(self.dict(), key=settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @classmethod
    def decode(cls, token: str):
        return cls(**jwt.decode(token, key=settings.SECRET_KEY, algorithms=[settings.ALGORITHM]))


class Auth:
    hasher = CryptContext(schemes=['bcrypt'])
    secret = settings.SECRET_KEY

    def hash_password(self, password: str):
        return self.hasher.hash(password)

    def verify_password(self, password: str, encoded_password: str):
        return self.hasher.verify(password, encoded_password)

    def encode_token(self, username: EmailStr):
        payload = AuthPayload(
            exp=datetime.utcnow() + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRY_SECONDS),
            iat=datetime.utcnow(),
            sub=username
        )
        return payload.encode()

    def decode_token(self, token: str):
        try:
            payload = AuthPayload.decode(token)
            if payload.scope == 'access_token':
                return payload.sub
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Scope for the token is invalid")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token expired')
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')

    def encode_refresh_token(self, username: EmailStr):
        payload = AuthPayload(
            exp=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRY_DAYS),
            iat=datetime.utcnow(),
            sub=username
        )
        return payload.encode()

    def refresh_token(self, refresh_token: str):
        try:
            payload = AuthPayload.decode(refresh_token)
            if payload.scope == 'refresh_token':
                if db.query(Token).get(refresh_token):
                    raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Banned refresh token")
                tk_db = Token(id=refresh_token)
                db.add(tk_db)
                db.commit()
                username = payload.sub
                new_token = self.encode_token(username)
                new_refresh_token = self.encode_refresh_token(username)
                return new_token, new_refresh_token
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Invalid scope for token')
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Refresh token expired')
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Invalid refresh token')

    def encode_verification_token(self, username: EmailStr):
        payload = AuthPayload(
            exp=datetime.utcnow() + timedelta(minutes=settings.EMAIL_TOKEN_EXPIRY_MINUTES),
            iat=datetime.utcnow(),
            scope='email_verification',
            sub=username
        )
        return payload.encode()

    def verify_email(self, token: str):
        try:
            payload = AuthPayload.decode(token)
            if payload.scope == 'email_verification':
                if db.query(Token).get(token):
                    raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Email token has been used!")
                tk_db = Token(id=token)
                db.add(tk_db)
                db.commit()
                username = payload.sub
                return username
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid scope for token')
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Email token expired')
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid email token')

    def encode_reset_token(self, username: EmailStr):
        payload = AuthPayload(
            exp=datetime.utcnow() + timedelta(minutes=settings.RESET_TOKEN_EXPIRY_MINUTES),
            iat=datetime.utcnow(),
            scope='reset_token',
            sub=username
        )
        return payload.encode()

    def verify_reset_token(self, token: str):
        try:
            payload = AuthPayload.decode(token)
            if payload.scope == 'reset_token':
                if db.query(Token).get(token):
                    raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Reset token has been used!")
                tk_db = Token(id=token)
                db.add(tk_db)
                db.commit()
                username = payload.sub
                return username
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid scope for token')
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Reset token expired')
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid reset token')


auth = Auth()
