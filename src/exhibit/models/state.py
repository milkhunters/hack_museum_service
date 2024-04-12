from enum import Enum


class UserState(str, Enum):
    NOT_CONFIRMED = "NOT_CONFIRMED"
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    DELETED = "DELETED"


class ExhibitState(int, Enum):
    DRAFT = 0
    PUBLISHED = 1
    ARCHIVED = 2
    DELETED = 3


class CommentState(int, Enum):
    DELETED = 0
    PUBLISHED = 1


class NotificationType(int, Enum):
    COMMENT_ANSWER = 1


class RateState(int, Enum):
    NEUTRAL = 0
    LIKE = 1
