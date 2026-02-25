from .otp_repository import OtpRepository


async def provide_otp_repository() -> OtpRepository:
    return OtpRepository()


get_otp_repository = provide_otp_repository
