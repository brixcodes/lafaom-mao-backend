from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError,HTTPException
from fastapi.responses import JSONResponse
from src.config import settings
from src.api.user.router import router as user_router
from src.api.auth.router import router as auth_router
import firebase_admin
from firebase_admin import credentials
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import sentry_sdk
from src.celery_utils import create_celery
from src.helper.schemas import BaseOutFail, ErrorMessage
# Initialize Firebase Admin SDK
if firebase_admin._apps:
    firebase_admin.delete_app(firebase_admin.get_app())
cred = credentials.Certificate("src/laakam.json")
firebase_admin.initialize_app(credential=cred)

if settings.SENTRY_DSN and settings.ENV != "development":
    sentry_sdk.init(
        dsn= settings.SENTRY_DSN,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for tracing.
        traces_sample_rate=1.0,
        _experiments={
            # Set continuous_profiling_auto_start to True
            # to automatically start the profiler on when
            # possible.
            "continuous_profiling_auto_start": True,
        },)



app = FastAPI(title=settings.PROJECT_NAME)
celery = create_celery()
app.celery_app = celery

base_url = "/api/v1"

app.mount("/static", StaticFiles(directory="src/static"), name="static")

app.include_router(auth_router, prefix=base_url + "/auth", tags=["Auth"])
app.include_router(user_router, prefix=base_url )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    simplified_errors = [{"loc": err["loc"], "msg": err["msg"]} for err in errors]
    try :
        return JSONResponse(
            status_code=422,
            content= {   
                        "message": "Validation error",
                        "error_code" : "validation_error",
                        "data" : exc.body,
                        "error":simplified_errors,
                        "success": False
                    }, 
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=422,
            content= {"message": "Validation error","error_code" : "validation_error","error":simplified_errors,"success": False}
        )
    

@app.exception_handler(HTTPException)
async def validation_exception_handler(request: Request, exc: HTTPException):
    
    
    
    if isinstance(exc.detail, str):
        if exc.status_code == 403:
            return JSONResponse(
                status_code=403,
                content=BaseOutFail(
                    message=ErrorMessage.NOT_AUTHENTICATED.description,
                    error_code=ErrorMessage.NOT_AUTHENTICATED.value).model_dump()
            )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail" : exc.detail}, 
        )
    else:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail, 
        )
        


origins = [
    "http://localhost",
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "http://127.0.0.1:5500",
    "https://laakam.com",
    "https://api.laakam.com",
    "https://www.laakam.com",
    
]

@app.get("/", tags=["Root"])
async def root() -> dict:
    
    return {
        "message": "Welcome to La'akam IAM API ",
        "documentation": "/docs",
        "Environment": settings.ENV
    }

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)  
