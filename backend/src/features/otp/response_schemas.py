from pydantic import BaseModel, Field


class EmailVerificationResponseSchema(BaseModel):
    message: str = Field(..., description="Success message")
    email_verified: bool = Field(default=True, description="Email verification status")

    model_config = {
        "json_schema_extra": {"examples": [{"message": "Email verified successfully.", "email_verified": True}]}
    }