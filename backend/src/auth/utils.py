from passlib.context import CryptContext
from datetime import timedelta, datetime
import jwt
import uuid
from src.config import Config
import logging

ACCESS_TOKEN_EXPIRY = 3600

password_context = CryptContext(
    schemes=[
        'bcrypt'
    ],
    deprecated="auto"
)


def verify_password(password: str, password_hash: str) -> bool:
    return password == password_hash


def create_access_token(user_data: dict, expiry: timedelta = None, refresh: bool = False):
    payload = {}
    payload['user'] = user_data
    payload['exp'] = datetime.now() + (expiry if expiry is not None else timedelta(seconds=ACCESS_TOKEN_EXPIRY))
    payload['jti'] = str(uuid.uuid4())
    payload['refresh'] = refresh

    token = jwt.encode(
        payload=payload,
        key=Config.JWT_SECRET,
        algorithm=Config.JWT_ALGO
    )
    return token


def decode_token(token: str) -> dict:
    try:
        token_data = jwt.decode(
            jwt=token,
            key=Config.JWT_SECRET,
            algorithms=[Config.JWT_ALGO]
        )
        return token_data
    except jwt.PyJWTError as ex:
        logging.exception(ex)
        return None
