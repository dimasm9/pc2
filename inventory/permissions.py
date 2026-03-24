from .models import Role


def user_role(user):
    if user.is_superuser:
        return Role.ADMIN
    return user.groups.first().name if user.groups.exists() else None


def role_in(user, allowed):
    return user_role(user) in allowed or user.is_superuser
