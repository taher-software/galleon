from fastapi import status
from typing import Dict, Any

from api.otp.response_models import (
    OTPRequestErrorResponseInvalidMSISDN,
    OTPRequestErrorResponseErrorSMS,
    OTPRequestErrorResponseErrorSMTP,
    OTPRequestErrorResponseInvalidOTPFormat,
    OTPRequestErrorResponseInvalidRequestID,
    OTPRequestErrorResponseMissmatchOTPCOnfirmation,
)

request_otp: Dict[int | str, Dict[str, Any]] = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": OTPRequestErrorResponseInvalidMSISDN,
        "description": "Invalid MSISDN or Email.",
    },
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": OTPRequestErrorResponseErrorSMS,
        "description": "SMS GW server down or not configured.",
    },
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": OTPRequestErrorResponseErrorSMTP,
        "description": "SMTP GW server down or not configured.",
    },
}

confirm_otp: Dict[int | str, Dict[str, Any]] = {
    **request_otp,
    status.HTTP_400_BAD_REQUEST: {
        "model": OTPRequestErrorResponseInvalidRequestID,
        "description": "Invalid OTP request Id.",
    },
    status.HTTP_400_BAD_REQUEST: {
        "model": OTPRequestErrorResponseInvalidOTPFormat,
        "description": "Invalid OTP format.",
    },
}

verify_otp: Dict[int | str, Dict[str, Any]] = {
    **request_otp,
    status.HTTP_400_BAD_REQUEST: {
        "model": OTPRequestErrorResponseMissmatchOTPCOnfirmation,
        "description": "Missmatch OTP confirmation Id",
    },
}