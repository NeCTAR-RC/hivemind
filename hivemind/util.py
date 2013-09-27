import os
import socket

from fabric.api import env


def local_user():
    return os.environ.get("USERNAME")


def local_host():
    return socket.getfqdn()


def current_host():
    return env.host_string.split(".")[0]
