import json
from operations import run

LOCK_FILE = "/var/lib/puppet/state/agent_disabled.lock"


def disable_agent(reason):
    run("puppet agent --disable '%s'" % reason)


def enable_agent():
    run("puppet agent --enable")


class disabled():
    """Disable a puppet agent for the duration of the with context:

    >>> from hivemind import puppet
    >>> with puppet.disabled('Software Upgrade'):
    ...    # ... Perform upgrade ...
    ...    pass
    """
    def __init__(self, reason):
        self.reason = reason

    def __enter__(self):
        disable_agent(self.reason)

    def __exit__(self, type, value, traceback):
        enable_agent()


def stop_service():
    run("service puppet stop")


def start_service():
    run("service puppet start")


def run_agent():
    run("puppet agent -t")


# TODO does not with puppet 2
def is_disabled():
    """Check if the puppet agent is disabled.  If it is then return the
    reason.

    """
    output = run("cat %s 2>/dev/null || true" % LOCK_FILE)
    if not output:
        return False
    return json.loads(output)["disabled_message"]