from pydantic import BaseModel, Field


class EmailVerificationResponseSchema(BaseModel):
    message: str = Field(..., description="Success message")
    email_verified: bool = Field(default=True, description="Email verification status")

    model_config = {
        "json_schema_extra": {"examples": [{"message": "Email verified successfully.", "email_verified": True}]}
    }


class ResendOTPResponse(BaseModel):
    message: str = Field(..., description="Human-readable message")
    active_otp: bool | None = Field(default=None, description="Whether an active OTP exists")
    cooldown_remaining_seconds: int | None = Field(default=None, description="Seconds until resend is allowed")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Verification code sent to your email.",
                    "expires_in_seconds": 300,
                    "active_otp": False,
                },
            ]
        }
    }
