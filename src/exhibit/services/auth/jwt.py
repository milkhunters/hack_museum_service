import jwt
from fastapi import Request
from pydantic import ValidationError

from exhibit.config import JWTConfig
from exhibit.models import schemas


class JWTManager:
    ALGORITHM = "ES256"

    COOKIE_PATH = "/api"
    COOKIE_DOMAIN = None
    COOKIE_ACCESS_KEY = "access_token"
    COOKIE_REFRESH_KEY = "refresh_token"

    def __init__(self, config: JWTConfig):
        self.JWT_PUBLIC_KEY = config.PUBLIC_KEY

    def get_jwt_cookie(self, req_obj: Request) -> schemas.Tokens:
        """
        Получает из кук access и refresh-токены
        :param req_obj:
        :return: None или Tokens
        """
        access_token = req_obj.cookies.get(self.COOKIE_ACCESS_KEY)
        refresh_token = req_obj.cookies.get(self.COOKIE_REFRESH_KEY)
        return schemas.Tokens(access_token=access_token, refresh_token=refresh_token)

    def is_valid_token(self, token: str) -> bool:
        try:
            data = jwt.decode(token, self.JWT_PUBLIC_KEY, algorithms=self.ALGORITHM)
            schemas.TokenPayload.model_validate(data)
        except (
                jwt.exceptions.InvalidTokenError,
                jwt.exceptions.ExpiredSignatureError,
                jwt.exceptions.DecodeError,
                ValidationError
        ):
            return False
        return True

    def decode_jwt(self, token: str) -> schemas.TokenPayload:
        """
        param: token: токен
        :return: payload
        """
        return schemas.TokenPayload.model_validate(jwt.decode(
            token,
            self.JWT_PUBLIC_KEY,
            algorithms=self.ALGORITHM,
            options={"verify_signature": False}
        ))
