import os
from time import sleep
import requests
from datetime import datetime, timedelta

import lxml.etree
import cssselect
from fabric.api import env, puts

CMD_SCHEDULE_HOST_SVC_DOWNTIME = 86

COMMIT = 2
SUCCESS = "Your command request was successfully" + \
          " submitted to Nagios for processing."


def format_time(date):
    return date.strftime("%Y-%m-%d %H:%M:%S")


def host_maintenance(comment, start_time=None,
                     hours=2, minutes=0, fixed=False):
    if not env.nagios:
        puts("No Nagios service for environment.")
    if not start_time:
        start_time = datetime.now()
    end_time = datetime.now() + timedelta(hours=hours, minutes=minutes)
    resp = requests.post(env.nagios + "cmd.cgi",
                         auth=env.nagios_auth,
                         data={"cmd_typ": CMD_SCHEDULE_HOST_SVC_DOWNTIME,
                               "cmd_mod": COMMIT,
                               "com_author": os.environ.get("USERNAME"),
                               "com_data": comment,
                               "start_time": format_time(start_time),
                               "end_time": format_time(end_time),
                               "fixed": int(fixed),
                               "hours": int(hours),
                               "minutes": int(minutes),
                               "host": env.host_string})
    assert SUCCESS in resp.text


def cancel_service_maintenance(downtime_id):
    resp = requests.post(env.nagios + "cmd.cgi",
                         auth=env.nagios_auth,
                         data={"cmd_typ": 79,
                               "cmd_mod": COMMIT,
                               "down_id": int(downtime_id)})
    assert SUCCESS in resp.text


def cancel_host_maintenance(reason):
    for service in services_in_maintenance():
        if not service["host"] == env.host_string:
            continue
        if not service["reason"] == reason:
            continue
        cancel_service_maintenance(service["id"])


def services_in_maintenance():
    resp = requests.get(env.nagios + "extinfo.cgi?type=6",
                        auth=env.nagios_auth)
    h = lxml.etree.HTML(resp.text)
    tr = cssselect.GenericTranslator()
    nodes = h.xpath(tr.css_to_xpath("table.downtime"))
    services = []

    if len(nodes) < 2:
        return services

    for tr in nodes[1]:
        if tr.getchildren()[0].tag == "th":
            continue
        if tr.getchildren()[0].text\
           == 'There are no services with scheduled downtime':
            continue
        host = tr.getchildren()[0].getchildren()[0].text
        service = tr.getchildren()[1].getchildren()[0].text
        reason = tr.getchildren()[4].text
        down_id = tr.getchildren()[9].text
        services.append({"host": host, "service": service,
                         "reason": reason, "id": down_id})
    return services


def host_is_in_maintenance(reason):
    for service in services_in_maintenance():
        if not service["host"] == env.host_string:
            continue
        if not service["reason"] == reason:
            continue
        return True
    return False


def ensure_host_maintenance(comment, start_time=None,
                            hours=2, minutes=0, fixed=False):

    if not host_is_in_maintenance(comment):
        host_maintenance(comment, hours=1)
    attempts = 0
    while True:
        if host_is_in_maintenance(comment):
            break
        if attempts > 5:
            raise Exception("Can't trigger maintenance in Nagios")
        attempts += 1
        sleep(5)
    return True
