from functools import wraps
from fabric.api import env


def _has_role(host, roles):
    for role, hosts in env.roledefs.items():
        if role not in roles:
            continue
        if host in hosts:
            return True
    return False


def only_for(*role_list):
    """Decorator preventing wrapped function from running if the targeted
    host doesn't have one of the listed roles.

    """
    def _only_for(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if _has_role(env.host_string, role_list):
                func(*args, **kwargs)
            return
        return wrapper
    return _only_for
