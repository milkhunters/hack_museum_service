from jose import JWTError, jwt

from exhibit.config import JWTConfig
from exhibit.models.schemas import TokenPayload


class JWTManager:
    algorithm = "ES256"

    COOKIE_PATH = "/api"
    COOKIE_DOMAIN = None
    COOKIE_ACCESS_KEY = "access_token"
    COOKIE_REFRESH_KEY = "refresh_token"

    def __init__(self, config: JWTConfig):
        self.public_key = config.PUBLIC_KEY

    def is_valid_token(self, token: str) -> bool:
        try:
            TokenPayload(**jwt.decode(
                token, self.public_key, algorithms=[self.algorithm],
            ))
        except (JWTError, ValueError, AttributeError):
            return False
        return True

    def decode_jwt(self, token: str) -> TokenPayload:
        """
        param: token: токен
        :return: payload
        """
        return TokenPayload(**jwt.decode(
            token, self.public_key, algorithms=[self.algorithm],
        ))
