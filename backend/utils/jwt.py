from black import err
import jwt
from time import time
from typing import Any, Optional
from fastapi import Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db.models import User
from utils.settings import settings
from api.models.response import ApiException
import api.models.errors as api_errors
from db import db


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True, fetch_user: bool = False):
        super().__init__(auto_error=auto_error)
        self.fetch_user = fetch_user

    async def __call__(self, request: Request) -> Optional[str]:
        try:
            credentials: Optional[
                HTTPAuthorizationCredentials
            ] = await super().__call__(request)
            if credentials and credentials.scheme == "Bearer":
                decoded_data = decode_jwt(credentials.credentials)
                if not decoded_data:
                    raise ApiException(
                        status.HTTP_401_UNAUTHORIZED, api_errors.EXPIRED_TOKEN
                    )
                msisdn = decoded_data.get("msisdn")

                if self.fetch_user:
                    if user := db.query(User).filter(User.msisdn == msisdn).first():
                        return user
                    # TODO User not found exception
                    raise

                return msisdn

        except:
            raise ApiException(
                status.HTTP_401_UNAUTHORIZED, api_errors.NOT_AUTHENTICATED
            )


def sign_jwt(data: dict, expires: int = 600) -> str:
    payload = {"data": data, "expires": time() + expires}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_jwt(token: str) -> dict:
    decoded_token = jwt.decode(
        token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
    )
    return decoded_token["data"] if decoded_token["expires"] >= time() else None


if __name__ == "__main__":
    import os
    import binascii

    # Generate secret
    print(binascii.hexlify(os.urandom(24)))
