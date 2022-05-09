""" 
BSS : Business Support Systems
This is the middle-ware that connects with
zain backend systems (aka zain-backend)
"""

from fastapi import APIRouter, Body
from fastapi import Depends

from .balance import get_wallet, Wallet
from .sim import get_sim_details, Sim 
from .subscriptions import get_subscriptions, Subscription
from .zend import recharge_voucher
from ..user.router import JWTBearer

router = APIRouter()

@router.get('/sim-status/{msisdn}', response_model=Sim)
async def retrieve_status(msisdn : str, session_msisdn = Depends(JWTBearer())) -> Sim:
    """ Retrieve SIM status """
    assert msisdn == session_msisdn
    return get_sim_details(msisdn)

@router.get('/subscriptions/{msisdn}', response_model = list[Subscription])
async def retrieve_subscriptions(msisdn : str, session_msisdn = Depends(JWTBearer())) -> list[Subscription]:
    """ Retrieve subscriptions list """
    assert msisdn == session_msisdn
    return get_subscriptions(msisdn)

@router.get('/wallet/{msisdn}', response_model = Wallet)
async def retrieve_wallet(msisdn : str, session_msisdn = Depends(JWTBearer())):
    """ Retrieve customer wallet's details (balance and load) """
    assert msisdn == session_msisdn
    return get_wallet(msisdn)

@router.post('/charge-voucher')
async def api_charge_voucher(msisdn = Body(...), pincode : str = Body(...), session_msisdn = Depends(JWTBearer())):
    assert msisdn == session_msisdn
    return recharge_voucher(msisdn, pincode)
