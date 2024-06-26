import uuid
from abc import ABC, abstractmethod

from starlette import authentication

from exhibit.models.permission import Permission
from exhibit.models.state import UserState


class BaseUser(ABC, authentication.BaseUser):

    @property
    @abstractmethod
    def id(self) -> uuid.UUID:
        pass

    @property
    @abstractmethod
    def permissions(self) -> set[str]:
        pass

    @property
    @abstractmethod
    def state(self) -> UserState | None:
        pass

    @property
    @abstractmethod
    def access_exp(self) -> int:
        pass

    @abstractmethod
    def __eq__(self, other):
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__}>({self.display_name})"


class AuthenticatedUser(BaseUser):
    def __init__(self, id: str, permissions: list[Permission], state: str, exp: int, **kwargs):
        self._id = uuid.UUID(id)
        self._permissions = permissions
        self._state = state
        self._exp = exp

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return str(self._id)

    @property
    def identity(self) -> uuid.UUID:
        return self._id

    @property
    def id(self) -> uuid.UUID:
        return self._id

    @property
    def permissions(self) -> set[Permission]:
        return set(self._permissions)

    @property
    def state(self) -> UserState:
        return UserState(self._state)

    @property
    def access_exp(self) -> int:
        return self._exp

    def __eq__(self, other):
        return isinstance(other, AuthenticatedUser) and self._id == other.id

    def __hash__(self):
        return hash(self._id)

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self._id})>"


class UnauthenticatedUser(BaseUser):
    def __init__(self, exp: int = None, **kwargs):
        self._exp = exp

    @property
    def is_authenticated(self) -> bool:
        return False

    @property
    def display_name(self) -> str:
        return "Guest"

    @property
    def identity(self) -> None:
        return None

    @property
    def id(self) -> None:
        return None

    @property
    def permissions(self) -> set[str]:
        return {
            Permission.GET_PUBLIC_EXHIBITS.value,
            Permission.GET_PUBLIC_COMMENTS.value,
        }

    @property
    def state(self) -> None:
        return None

    @property
    def access_exp(self) -> int | None:
        return self._exp

    def __eq__(self, other):
        return isinstance(other, UnauthenticatedUser)

    def __repr__(self):
        return f"<{self.__class__.__name__}>({self.display_name})"
