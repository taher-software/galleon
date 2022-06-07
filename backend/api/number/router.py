"""
BSS : Business Support Systems
This is the middle-ware that connects with
zain backend systems (aka zain-backend)
"""

from fastapi import APIRouter, Body, Query, Depends, status
from api.number.models.response import SubaccountsResponse
from api.otp.models.errors import INVALID_MSISDN_MISSMATCH
from .balance import get_wallet
from .sim import get_sim_details
from .subscriptions import get_subscriptions, zend_subscriptions
from .zend import (
    recharge_voucher,
    change_supplementary_offering,
    get_free_units,
    query_bill,
)
from sqlalchemy.orm import Session
from db.main import get_db
from utils.jwt import JWTBearer
from utils.settings import settings
import utils.regex as rgx
from db.models import User
from api.number.models.response import (
    RetrieveStatusResponse,
    SubscriptionsResponse,
    WalletResponse,
)
from api.models.response import ApiException, ApiResponse

router = APIRouter()


@router.get(
    "/status",
    response_model=RetrieveStatusResponse,
)
async def retrieve_status(
    msisdn: str = Query(..., regex=rgx.MSISDN, example="7839921514"),
    db: Session = Depends(get_db),
) -> RetrieveStatusResponse:
    """Retrieve SIM status"""
    sim_details = get_sim_details(msisdn)
    sim_details.associated_with_user = (
        db.query(User).filter(User.msisdn == msisdn).first() is not None
    )

    return RetrieveStatusResponse(data=sim_details)


@router.get(
    "/subscriptions",
    response_model=SubscriptionsResponse,
)
async def retrieve_subscriptions(
    msisdn: str = Query(..., regex=rgx.MSISDN, example="7839921514"),
    session_msisdn=Depends(JWTBearer()),
) -> SubscriptionsResponse:
    """Retrieve subscriptions list"""
    return SubscriptionsResponse(data=get_subscriptions(msisdn))


@router.get("/subaccounts", response_model=SubaccountsResponse)
async def retrieve_subaccounts(
    msisdn: str = Query(..., regex=rgx.MSISDN, example="7839921514"),
    session_msisdn=Depends(JWTBearer()),
) -> SubaccountsResponse:
    return SubaccountsResponse(data=get_free_units(msisdn))


@router.get(
    "/wallet",
    response_model=WalletResponse,
)
async def retrieve_wallet(
    msisdn: str = Query(..., regex=rgx.MSISDN, example="7839921514"),
    session_msisdn=Depends(JWTBearer()),
) -> WalletResponse:
    """Retrieve customer wallet's details (balance and load)"""
    return WalletResponse(data=get_wallet(msisdn))
    # assert msisdn == session_msisdn


@router.post(
    "/redeem-registration-gift",
    response_model=ApiResponse,
)
async def redeem_registration_gift(
    msisdn: str = Body(..., embed=True, regex=rgx.MSISDN, example="7839921514"),
    session_msisdn=Depends(JWTBearer()),
) -> ApiResponse:
    return change_supplementary_offering(
        msisdn, settings.registration_gift_offer_id, True
    )


@router.post(
    "/charge-voucher",
    response_model=ApiResponse,
)
async def charge_voucher(
    msisdn: str = Body(..., regex=rgx.MSISDN, example="7839921514"),
    pincode: str = Body(..., regex=rgx.DIGITS, max_length=20, example="123456"),
    session_msisdn=Depends(JWTBearer()),
) -> ApiResponse:
    return recharge_voucher(msisdn, pincode)


@router.get("/query-bill", response_model=ApiResponse)
async def api_query_bill(
    msisdn: str = Query(..., regex=rgx.MSISDN, example="7839921514"),
    session_msisdn=Depends(JWTBearer()),
) -> ApiResponse:
    """Check bill for postpaid msisdn"""
    if msisdn != session_msisdn:
        raise ApiException(status_code=99, error=INVALID_MSISDN_MISSMATCH)
    return query_bill(msisdn)


@router.post("/subscribe", response_model=ApiResponse)
async def api_subscribe(
    msisdn: str = Body(..., regex=rgx.MSISDN, example="7839921514"),
    offer_id: str = Body(..., example=1000),
    session_msisdn=Depends(JWTBearer()),
) -> ApiResponse:
    """Adds or removes the bundle with CRM offer ID provided to/from MSISDN provided"""
    if msisdn != session_msisdn:
        raise ApiException(status.HTTP_401_UNAUTHORIZED, INVALID_MSISDN_MISSMATCH)
    return zend_subscriptions(msisdn, offer_id, True)


@router.post("/unsubscribe", response_model=ApiResponse)
async def api_unsubscribe(
    msisdn: str = Body(..., regex=rgx.MSISDN, example="7839921514"),
    offer_id: str = Body(..., example=1000),
    session_msisdn=Depends(JWTBearer()),
) -> ApiResponse:
    """Adds or removes the bundle with CRM offer ID provided to/from MSISDN provided"""
    if msisdn != session_msisdn:
        raise ApiException(status.HTTP_401_UNAUTHORIZED, INVALID_MSISDN_MISSMATCH)
    return zend_subscriptions(msisdn, offer_id, False)
