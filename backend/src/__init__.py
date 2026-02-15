from fastapi import FastAPI
from .auth.auth_api import auth_router
from .otp.verification_api import otp_route
from contextlib import asynccontextmanager
from src.core.database.main import init_db
from src.errors.register_all_errors import register_all_errors
from src.middlewares.middleware import register_middleware
from src.core.exceptions.handlers import register_exception_handlers


@asynccontextmanager
async def life_span(app: FastAPI):
    await init_db()
    yield
    print("end")


version = "v1"

app = FastAPI(
    title="SEO content optimization",
    description="A REST API app for content generation",
    version=version,
    lifespan=life_span
)

register_exception_handlers(app)
register_all_errors(app)
register_middleware(app)

app.include_router(auth_router, prefix=f"/api/{version}/auth", tags=['auth'])
app.include_router(otp_route, prefix=f"/api/{version}/otp", tags=['auth'])
