""" OTP api set """

from fastapi import APIRouter, Body, status
from api.otp.response_models import MISSMATCH_OTP_CONFIRMATION
from .utils import gen_alphanumeric, gen_numeric, slack_notify
from api.number.zend import zend_send_sms
from utils.db import Otp, db
from utils.api_responses import Status, ApiResponse, ApiException
from .additional_responses import request_otp, confirm_otp, verify_otp
import utils.regex as rgx

router = APIRouter()


@router.post(
    "/request",
    response_model=ApiResponse,
    response_model_exclude_none=True,
    responses=request_otp,
)
async def send_otp(
    msisdn: str = Body(..., embed=True, regex=rgx.MSISDN)
) -> ApiResponse:
    """Request new Otp"""

    # If a prior otp exists, delete it.
    otp = db.query(Otp).filter(Otp.msisdn == msisdn).first()
    if otp:
        db.delete(otp)
        db.commit()

    code = gen_numeric()
    otp = Otp(msisdn=msisdn, code=code)
    db.add(otp)
    db.commit()
    db.refresh(otp)
    zend_send_sms(msisdn, f"Your otp code is {code}")
    slack_notify(msisdn, code)
    return ApiResponse(status=Status.success)


@router.post(
    "/confirm",
    response_model=ApiResponse,
    response_model_exclude_none=True,
    responses=confirm_otp,
)
async def confirm(
    msisdn: str = Body(..., regex=rgx.MSISDN), code: str = Body(..., regex=rgx.DIGITS)
) -> ApiResponse:
    """Confirm Otp"""
    if otp := db.query(Otp).filter(Otp.msisdn == msisdn).first():
        otp.tries += 1
        db.commit()
        db.refresh(otp)
        if otp.code == code:
            otp.confirmation = gen_alphanumeric()
            db.commit()
            db.refresh(otp)
            return ApiResponse(
                status=Status.success, data={"confirmation": otp.confirmation}
            )
    raise ApiException(
        status_code=status.HTTP_400_BAD_REQUEST, error=MISSMATCH_OTP_CONFIRMATION
    )


@router.post(
    "/verify",
    response_model=ApiResponse,
    response_model_exclude_none=True,
    responses=verify_otp,
)
async def api_verify(
    msisdn: str = Body(..., regex=rgx.MSISDN),
    confirmation: str = Body(..., regex=rgx.STRING),
) -> ApiResponse:
    """Verify otp status (internal use)"""
    otp = db.query(Otp).filter(Otp.msisdn == msisdn).first()
    if otp and otp.confirmation and otp.confirmation == confirmation:
        return ApiResponse(status=Status.success)
    raise ApiException(
        status_code=status.HTTP_400_BAD_REQUEST, error=MISSMATCH_OTP_CONFIRMATION
    )
