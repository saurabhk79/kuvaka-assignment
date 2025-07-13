from pydantic import BaseModel, Field

class UserRegister(BaseModel):
    mobile_number: str = Field(pattern=r"^\+?\d{10,15}$", description="Mobile number with optional international prefix")
    password: str = Field(min_length=6, max_length=50)

class SendOTPRequest(BaseModel):
    mobile_number: str = Field(pattern=r"^\+?\d{10,15}$")

class VerifyOTPRequest(BaseModel):
    mobile_number: str = Field(pattern=r"^\+?\d{10,15}$")
    otp_code: str = Field(min_length=6, max_length=6)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=50)

class ForgotPasswordRequest(BaseModel):
    mobile_number: str = Field(pattern=r"^\+?\d{10,15}$")

class ResetPasswordRequest(BaseModel):
    mobile_number: str = Field(pattern=r"^\+?\d{10,15}$")
    otp_code: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=6, max_length=50)