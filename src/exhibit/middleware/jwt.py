from starlette.authentication import AuthCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.exceptions import ExceptionMiddleware

from fastapi.requests import Request

from exhibit.models.schemas import Tokens
from exhibit.models.auth import AuthenticatedUser, UnauthenticatedUser
from exhibit.services.auth import JWTManager


class JWTMiddlewareHTTP(BaseHTTPMiddleware):

    def __init__(self, app: ExceptionMiddleware):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        jwt = JWTManager(config=request.app.state.config.JWT)
        reauth_session_dict = request.app.state.reauth_session_dict

        # States
        session_id = request.cookies.get("session_id")
        current_tokens = Tokens(
            access_token=request.cookies.get(jwt.COOKIE_ACCESS_KEY),
            refresh_token=request.cookies.get(jwt.COOKIE_REFRESH_KEY)
        )
        is_valid_session = False

        # ----- pre_process -----
        is_valid_access_token = jwt.is_valid_token(current_tokens.access_token)
        is_valid_refresh_token = jwt.is_valid_token(current_tokens.refresh_token)

        if session_id and current_tokens.refresh_token:

            # Если требуется обновить данные пользователя, то запрещаем
            # авторизацию по старому refresh токену, из-за чего пользователю
            # придется обновить токены или дождаться истечения access токена

            bad_ref_token = reauth_session_dict.get(session_id)
            is_valid_session = (bad_ref_token != current_tokens.refresh_token)

        is_auth = (is_valid_access_token and is_valid_refresh_token and is_valid_session)

        # Установка данных авторизации
        if is_auth:
            payload = jwt.decode_jwt(current_tokens.access_token)
            request.scope["user"] = AuthenticatedUser(**payload.model_dump())
            request.scope["auth"] = AuthCredentials(["authenticated"])
        else:
            request.scope["user"] = UnauthenticatedUser()
            request.scope["auth"] = AuthCredentials()

        response = await call_next(request)

        # ----- post_process -----

        return response
