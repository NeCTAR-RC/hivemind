from contextlib import contextmanager
import inspect
import os
import socket

from fabric import api
from fabric.api import env


def local_user():
    return os.environ.get("USERNAME")


def local_host():
    return socket.getfqdn()


def current_host():
    return env.host_string.split(".")[0]


@contextmanager
def hide_and_ignore():
    with api.hide('everything'), api.settings(warn_only=True):
        yield


def func_args(function):
    "Dig through the decorator wrappers to find the real function arguments."
    func = function
    while getattr(func, '__closure__', None) or hasattr(func, 'wrapped'):
        if hasattr(func, 'wrapped'):
            func = func.wrapped
            continue
        func = func.__closure__[0].cell_contents
    return inspect.getfullargspec(func)
