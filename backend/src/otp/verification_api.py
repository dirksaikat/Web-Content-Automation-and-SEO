from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.main import get_session
from .schemas import AccountVerificationSchema


otp_route = APIRouter()


@otp_route.post("/verify-account")
async def verify_account(data: AccountVerificationSchema, session: AsyncSession = Depends(get_session)):
    pass
