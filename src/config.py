from pydantic_settings import BaseSettings
from pydantic import ConfigDict, model_validator,EmailStr, BeforeValidator,AnyUrl,computed_field,HttpUrl
from typing import ClassVar, Literal,Annotated,Any
from typing_extensions import Self
import secrets
from kombu import Queue

def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)

def route_task(name, args, kwargs, options, task=None, **kw):
    if ":" in name:
        queue, _ = name.split(":")
        return {"queue": queue}
    return {"queue": "default"}

class Settings(BaseSettings):
    
    PROJECT_NAME: str = "La'akam"
    ENV: Literal["development", "staging", "production"] = "development"
    DATABASE_URL: str = "postgresql://user:paÒssword@127.0.0.1:5432/test"
    SECRET_KEY: str = secrets.token_urlsafe(32) 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES : int = 3600
    REFRESH_TOKEN_EXPIRE_MINUTES : int = 3600
    
    SENTRY_DSN: HttpUrl | None = None
    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []
    
    @computed_field  
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] 
    
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None

    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: str | None = None
    
    MAILGUN_DOMAIN : str =""
    MAILGUN_SECRET : str =""
    MAILGUN_ENDPOINT : str ="api.eu.mailgun.net"

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    
    LINKEDIN_CLIENT_ID : str = ""
    LINKEDIN_CLIENT_SECRET : str = ""
    LINKEDIN_REDIRECT_URL : str = "http://localhost:8000/api/v1/auth/linkedin/callback"

    GITHUB_CLIENT_ID : str = ""
    GITHUB_CLIENT_SECRET : str = ""
    GITHUB_REDIRECT_URL : str = "http://localhost:8000/api/v1/auth/github/callback"
    

    GOOGLE_CLIENT_ID : str = ""
    GOOGLE_CLIENT_SECRET : str = ""
    GOOGLE_REDIRECT_URL : str = "http://localhost:8000/api/v1/auth/google/callback"
    
    FACEBOOK_CLIENT_ID : str = ""
    FACEBOOK_CLIENT_SECRET : str = ""
    FACEBOOK_REDIRECT_URL : str = "http://localhost:8000/api/v1/auth/facebook/callback"
    
    POSTGRES_USER : str = ""
    POSTGRES_PASSWORD : str =""
    POSTGRES_DB : str = ""
    
    WEBSOCKET_HOST : str = "localhost:3000"
    WEBSOCKET_TOKEN : str = ""
    
    
    TOUPESU_WHATSAPP_CLIENT_ID : str = ""
    TOUPESU_WHATSAPP_CLIENT_SECRET : str = ""
    TOUPESU_WHATSAPP_URL : str = ""
    
    PUSHER_APP_ID : str = ""
    PUSHER_KEY : str = ""
    PUSHER_SECRET : str = ""
    PUSHER_CLUSTER : str = ""
    
    FCM_SERVER_KEY : str = ""
    
    CELERY_BROKER_URL: str = "redis://127.0.0.1:6379/0"
    CELERY_RESULT_BACKEND: str =  "redis://127.0.0.1:6379/0"
    
    CELERY_FLOWER_USER : str = "afrolancer"
    CELERY_FLOWER_PASSWORD: str =  "azerty"
    
    AWS_ACCESS_KEY_ID : str = ""
    AWS_SECRET_ACCESS_KEY : str = ""
    AWS_REGION : str = "us-east-1"
    AWS_BUCKET_NAME : str = "your-bucket-name"


    CELERY_BEAT_SCHEDULE: dict = {
        # "task-schedule-work": {
        #     "task": "task_schedule_work",
        #     "schedule": 5.0,  # five seconds
        # },
        
        # "task-schedule-work": {
        #     "task": "task_schedule_work",
        #     "schedule": crontab(minute="*/1"),
        # },
        # "task-schedule-work": {
        #     "task": "task_schedule_work",
        #     "schedule": crontab(minute="*/1"),
        # },
        
    }

    CELERY_TASK_DEFAULT_QUEUE: str = "default"

    # Force all queues to be explicitly listed in `CELERY_TASK_QUEUES` to help prevent typos
    CELERY_TASK_CREATE_MISSING_QUEUES: bool = False

    CELERY_TASK_QUEUES: list[Queue]  = [
        Queue("default"),
        Queue("high_priority"),
        Queue("low_priority"),
    ]

    CELERY_TASK_ROUTES: ClassVar[tuple] = (route_task,)
    
    
    ANT_MEDIA_URL : str = "http://127.0.0.1:5080/"
    ANT_MEDIA_TOKEN : str = ""

    model_config = ConfigDict(
        env_file = ".env",
        extra="ignore"
    )




settings = Settings()
