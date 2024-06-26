from enum import Enum


class Permission(Enum):
    GET_PUBLIC_EXHIBITS = "GET_PUBLIC_EXHIBITS"
    GET_PUBLIC_COMMENTS = "GET_PUBLIC_COMMENTS"

    # User
    GET_SELF_EXHIBITS = "GET_SELF_EXHIBITS"
    UPDATE_SELF_EXHIBITS = "UPDATE_SELF_EXHIBITS"
    DELETE_SELF_EXHIBITS = "DELETE_SELF_EXHIBITS"
    CREATE_SELF_EXHIBITS = "CREATE_SELF_EXHIBITS"

    CREATE_COMMENT = "CREATE_COMMENT"
    UPDATE_SELF_COMMENT = "UPDATE_SELF_COMMENT"
    DELETE_SELF_COMMENT = "DELETE_SELF_COMMENT"

    GET_SELF_NOTIFICATIONS = "GET_SELF_NOTIFICATIONS"
    DELETE_SELF_NOTIFICATION = "DELETE_SELF_NOTIFICATION"

    RATE_EXHIBITS = "RATE_EXHIBITS"

    # Superuser
    GET_PRIVATE_EXHIBITS = "GET_PRIVATE_EXHIBITS"
    UPDATE_USER_EXHIBITS = "UPDATE_USER_EXHIBITS"
    DELETE_USER_EXHIBITS = "DELETE_USER_EXHIBITS"

    DELETE_USER_COMMENT = "DELETE_USER_COMMENT"
    UPDATE_USER_COMMENT = "UPDATE_USER_COMMENT"
    GET_DELETED_COMMENTS = "GET_DELETED_COMMENTS"
