import os
import re
from pathlib import Path
from pydantic import BaseModel


def load_envstr(key: str, default: str | None = None):
    var = os.environ.get(key, default)
    assert isinstance(var, str) and len(var) > 0, f'{key}={var}: Should be str with length > 0'
    return var


def load_envbool(key: str, default: bool = False):
    var = load_envstr(key, 'true' if default else 'false')
    return var.isnumeric() and int(var) != 0 or var.lower() in 'true'


class Settings(BaseModel):
    PROJECT_TITLE: str = 'TransiSHOW'
    PROJECT_VERSION: str = '1.0.0'

    PRODUCTION_STAGE: str = load_envstr("TRANSISHOW_STAGE", 'dev')

    MAIL_USERNAME: str = load_envstr("MAIL_USERNAME")
    MAIL_PASSWORD: str = load_envstr("MAIL_PASSWORD")
    MAIL_FROM: str = load_envstr("MAIL_FROM")
    MAIL_PORT: int = int(load_envstr("MAIL_PORT"))
    MAIL_SERVER: str = load_envstr("MAIL_SERVER")

    TEMPLATE_FOLDER: Path = Path(load_envstr(
        "TEMPLATE_FOLDER",
        str(Path.cwd().absolute() / 'templates'),
    )).absolute()

    DATABASE_USER: str = load_envstr("POSTGRES_USER")
    DATABASE_PASSWORD: str = load_envstr("POSTGRES_PASSWORD")
    DATABASE_SERVER: str = load_envstr("POSTGRES_SERVER")
    DATABASE_PORT: int = int(load_envstr("POSTGRES_PORT"))
    DATABASE_NAME: str = load_envstr("POSTGRES_DB")
    DATABASE_URL: str = re.sub(r'\s+', '', f"""
        postgresql+psycopg2://
        {DATABASE_USER}:{DATABASE_PASSWORD}
        @{DATABASE_SERVER}:{DATABASE_PORT}
        /{DATABASE_NAME}
    """)

    SECRET_KEY: str = load_envstr("SECRET")
    ALGORITHM = "HS256"

    ACCESS_TOKEN_EXPIRY_SECONDS: int = 900
    REFRESH_TOKEN_EXPIRY_DAYS: int = 30
    EMAIL_TOKEN_EXPIRY_MINUTES: int = 30
    RESET_TOKEN_EXPIRY_MINUTES: int = 30

    FRONTEND_URL: str = load_envstr("FRONTEND_URL", default=None)

    @property
    def is_dev(self):
        return self.PRODUCTION_STAGE == "dev"

    @property
    def is_prod(self):
        return self.PRODUCTION_STAGE == "prod"


settings = Settings()

if settings.is_dev:
    settings.DATABASE_URL = 'sqlite:///:memory:'

if __name__ == '__main__':
    from rich import print
    print(settings)
