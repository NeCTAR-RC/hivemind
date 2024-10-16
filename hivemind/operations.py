from fabric.api import env
from fabric.api import puts
from fabric.api import run as fabric_run
from fabric.colors import green
from fabric.colors import red

from hivemind import log


def run(
    command,
    shell=True,
    pty=True,
    combine_stderr=None,
    quiet=False,
    warn_only=False,
    stdout=None,
    stderr=None,
    timeout=None,
    shell_escape=None,
):
    result = None

    env.disable_known_hosts = True

    if (not stdout) and (not stderr):
        stdout, stderr = log.stdio()
    try:
        result = fabric_run(
            command,
            shell=shell,
            pty=pty,
            combine_stderr=combine_stderr,
            quiet=quiet,
            warn_only=warn_only,
            stdout=stdout,
            stderr=stderr,
            timeout=timeout,
            shell_escape=shell_escape,
        )

    except Exception:
        puts("[{}] {} {}".format(env.host_string, command, red("failed")))
        if hasattr(stdout, "print_recent"):
            stdout.print_recent()
        raise
    else:
        puts("[{}] {} {}".format(env.host_string, command, green("success")))

    return result
