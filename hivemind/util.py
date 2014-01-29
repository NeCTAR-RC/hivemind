from contextlib import contextmanager
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
