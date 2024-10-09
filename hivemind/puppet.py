import json

from hivemind.operations import run


LOCK_FILE = "/opt/puppetlabs/puppet/cache/state/agent_disabled.lock"


def disable_agent(reason):
    return run("puppet agent --disable '%s'" % reason)


def enable_agent():
    return run("puppet agent --enable")


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
    # is changed, if there is an error during a run 6 will be
    # returned, a 1 will be returned if another agent is currently
    # running, and 0 will be returned if nothing has changed
    return run("puppet agent -t", warn_only=True)


def is_disabled():
    """Check if the puppet agent is disabled.  If it is then return the
    reason.

    """
    output = run("cat %s 2>/dev/null || true" % LOCK_FILE)
    if not output:
        return False
    return json.loads(output)["disabled_message"]
