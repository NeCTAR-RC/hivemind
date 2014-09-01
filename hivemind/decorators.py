from functools import wraps
from fabric.api import env, show
from common import CONF
import util


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
                return func(*args, **kwargs)
        return wrapper
    return _only_for


def verbose(func):
    """Make the output of this task print stdout and stderr by
    default.

    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        with show('stdout', 'stderr'):
            return func(*args, **kwargs)
    return wrapper


def conf_section(module, name):
    return 'cfg:%s.%s' % (module, name)


def func_config(section):
    try:
        return dict(CONF.items(section))
    except Exception:
        return {}


def configurable(name):
    """Decorator that makes all options for the function configurable
    within the settings file.

       :param str name: The name given to the config section

    """
    def _configurable(func):
        # If there is a . assume that the name is fully qualified.
        if '.' in name:
            conf_name = conf_section(*name.split('.', 1))
        else:
            conf_name = conf_section(func.__module__, name)
        conf = func_config(conf_name)
        args_list = util.func_args(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            filtered_defaults = dict((a, conf.get(a))
                                     for a in args_list.args if a in conf)
            arguments = dict(zip(reversed(args_list.args),
                                 args_list.defaults or []))
            arguments.update(dict(zip(args_list.args, args)))
            arguments.update(kwargs)
            arguments.update(filtered_defaults)
            missing_args = [arg for arg in args_list.args
                            if arg not in arguments]
            if missing_args:
                raise Exception(
                    'Configuration section %s is missing values for %s' %
                    (conf_name, missing_args))

            return func(**arguments)
        return wrapper
    return _configurable
