""" User management apis """

from pydantic import BaseModel, Field
from fastapi import APIRouter, Body, Header, HTTPException, status, Request, Depends
from typing import Optional, Any, Annotated
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from utils.jwt import decode_jwt, sign_jwt
from utils.db import db, User, Otp
from utils.password_hashing import verify_password, hash_password
import utils.regex as rgx


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        try:
            credentials: Optional[HTTPAuthorizationCredentials] = await super(
                JWTBearer, self
            ).__call__(request)
            if credentials and credentials.scheme == "Bearer":
                return decode_jwt(credentials.credentials)["msisdn"]
        except:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
            )


router = APIRouter()


class UserCreate(BaseModel):
    msisdn: str = Field(..., regex=rgx.DIGITS)
    name: str = Field(..., regex=rgx.TITLE)
    password: str = Field(..., regex=rgx.PASSWORD)
    email: str = Field(None, regex=rgx.EMAIL)
    profile_pic_url: str = Field(None, regex=rgx.URL)
    otp_confirmation: str = Field(..., regex=rgx.STRING)


class UserUpdate(BaseModel):
    name: str = Field(None, regex=rgx.TITLE)
    password: str = Field(None, regex=rgx.PASSWORD)
    profile_pic_url: str = Field(None, regex=rgx.URL)
    email: str = Field(None, regex=rgx.EMAIL)


class UserRetrieve(BaseModel):
    id: int
    status: str
    name: Optional[str]
    email: Optional[str]
    profile_pic_url: Optional[str]


class LoginOut(BaseModel):
    status: str
    refresh_token: dict
    access_token: dict


class UserExistsErr(BaseModel):
    status: str = "error"
    code: int = 201
    message: str = "Sorry the msisdn is already registered."


class InvalidOTPErr(BaseModel):
    status: str = "error"
    code: int = 202
    message: str = "The confirmation provided is not valid please try again."


class CreateUser(BaseModel):
    """Create User Response Model"""

    id: int
    msisdn: str
    name: str
    email: Optional[str]
    profile_pic_url: Optional[str]


@router.post(
    "/create",
    response_model=CreateUser,
    responses={
        403: {
            "model": UserExistsErr,
            "description": "User already exists.",
        },
        409: {
            "model": InvalidOTPErr,
            "description": "Invalid Otp Confirmation.",
        },
    },
)
async def create_user(new_user: UserCreate) -> CreateUser:
    """Register a new user"""
    user = db.query(User).filter(User.msisdn == new_user.msisdn).first()
    if user:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN, content=UserExistsErr().dict()
        )

    otp = db.query(Otp).filter(Otp.msisdn == new_user.msisdn).first()
    if not (otp and otp.confirmation and otp.confirmation == new_user.otp_confirmation):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT, content=InvalidOTPErr().dict()
        )

    user = User(
        msisdn=new_user.msisdn,
        name=new_user.name,
        password=hash_password(new_user.password),
        email=new_user.email,
        profile_pic_url=new_user.profile_pic_url,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return CreateUser(**user.serialize)


@router.get(
    "/profile",
    response_model=UserRetrieve,
    response_model_exclude_none=True,
)
async def get_profile(msisdn=Depends(JWTBearer())) -> UserRetrieve:
    """Get user profile"""
    user = db.query(User).filter(User.msisdn == msisdn).first()

    return UserRetrieve(
        status="success",
        id=user.id,
        name=user.name,
        email=user.email,
        profile_pic_url=user.profile_pic_url,
    )


@router.patch("/profile", response_model=UserRetrieve)
async def update_profile(user_profile: UserUpdate, msisdn=Depends(JWTBearer())):
    """Update user profile"""
    user = db.query(User).filter(User.msisdn == msisdn).first()

    if user_profile.name:
        user.name = user_profile.name
    if user_profile.password:
        user.password = hash_password(user_profile.password)
    if user_profile.email:
        user.email = user_profile.email
    if user_profile.profile_pic_url:
        user.profile_pic_url = user_profile.profile_pic_url
    db.commit()
    db.refresh(user)

    return UserRetrieve(
        status="success",
        id=user.id,
        name=user.name,
        email=user.email,
        profile_pic_url=user.profile_pic_url,
    )


@router.post("/login", response_model=LoginOut)
async def login(
    msisdn: str = Body(..., regex=rgx.DIGITS),
    password: str = Body(..., regex=rgx.PASSWORD),
) -> dict:
    """Login and generate refresh token"""
    user = db.query(User).filter(User.msisdn == msisdn).first()
    if user and verify_password(password, user.password):
        access_token = sign_jwt({"msisdn": msisdn})
        refresh_token = sign_jwt({"msisdn": msisdn, "grant_type": "refresh"}, 86400)
        user.refresh_token = refresh_token["token"]
        db.commit()

        return LoginOut(
            status="success", refresh_token=refresh_token, access_token=access_token
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong credentials."
    )


@router.post("/logout")
async def logout(msisdn=Depends(JWTBearer())):
    """Logout (aka delete refresh token)"""
    user = db.query(User).filter(User.msisdn == msisdn).first()
    if user and user.refresh_token:
        user.refresh_token = None
        db.commit()
    return {"status": "success"}


@router.post("/token")
async def gen_access_token(refresh_token: Optional[str] = Header(None)):
    """Generate access token from provided refresh token"""

    if refresh_token is not None:
        data = decode_jwt(refresh_token)
        if "msisdn" in data:
            msisdn = data["msisdn"]
            user = db.query(User).filter(User.msisdn == "msisdn").first()
            if user is not None:
                return {
                    "status": "success",
                    "access_token": sign_jwt({"msisdn": msisdn}),
                }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"message": "failed", "code": "99"},
    )


@router.post("/delete")
async def delete(msisdn=Depends(JWTBearer())):
    """Delete user"""
    user = db.query(User).filter(User.msisdn == msisdn).first()
    assert user
    db.delete(user)
    db.commit()
    return {"status": "success"}
