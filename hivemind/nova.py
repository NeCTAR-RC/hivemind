import os

from novaclient import client as nova_client

from decorators import only_for
from operations import run
from util import current_host


def client():
    url = os.environ['OS_AUTH_URL']
    username = os.environ['OS_USERNAME']
    password = os.environ['OS_PASSWORD']
    tenant = os.environ['OS_TENANT_NAME']
    return nova_client.Client('2',
                              username=username, api_key=password,
                              project_id=tenant, auth_url=url)


def list_services():
    output = run("nova-manage service list 2>/dev/null")
    services = []
    header = None
    for line in output.split("\n"):
        if not header:
            header = [l.lower() for l in line.split()]
            continue
        services.append(dict(zip(header, line.split())))
    return services


def host_services(host=None):
    if not host:
        host = current_host()
    return [service for service in list_services()
            if service["host"] == host]


@only_for("nova-node", "nova-controller")
def disable_host_services(host=None):
    if not host:
        host = current_host()
    for service in host_services(host):
        run("nova-manage service disable --host %s --service %s" %
            (service["host"], service["binary"]))


@only_for("nova-node", "nova-controller")
def enable_host_services(host=None):
    if not host:
        host = current_host()
    for service in host_services(host):
        run("nova-manage service enable --host %s --service %s" %
            (service["host"], service["binary"]))
