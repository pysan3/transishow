from fastapi import FastAPI
from fastapi.routing import APIRoute
from rich import print

from models.base import Base
from core.database import engine
from core.settings import settings
from v1.api import api_router


def include_router(app: FastAPI):
    app.include_router(api_router)


def create_db():
    Base.metadata.create_all(bind=engine)


def custom_generate_unique_id(route: APIRoute):
    return f"{route.tags[0]}-{route.name}"


def start_application():
    app = FastAPI(
        title=settings.PROJECT_TITLE,
        version=settings.PROJECT_VERSION,
        generate_unique_id_function=custom_generate_unique_id
    )
    include_router(app)
    create_db()
    return app


print(settings)
app = start_application()
