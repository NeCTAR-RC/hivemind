from collections import defaultdict
import pkg_resources
import sys

from fabric.api import env, puts
from fabric import main as fabric_main


def _load_fabfile(path, importer=None):
    all_tasks = defaultdict(dict)
    for entrypoint in pkg_resources.iter_entry_points(group='hivemind.tasks'):
        plugin = entrypoint.load()
        tasks = _load_tasks(plugin)
        for name, task in tasks.items():
            all_tasks[entrypoint.name].update({name: task})
    return None, all_tasks, None


def _load_tasks(imported):
    return fabric_main.extract_tasks(vars(imported).items())[0]


def main(filename=__file__):
    # work around for when python tries to use the byte compile version of the
    # fabfile.
    if filename.endswith('.pyc'):
        filename = filename.replace('.pyc', '.py')

    sys.argv = sys.argv[0:1] + ['-f', filename] + sys.argv[1:]
    sys.argv += ['--list-format=nested']
    if len(sys.argv) == 4 or '-l' in sys.argv:
        if env.roledefs:
            puts("Available roles:\n")
            for role, host_list in env.roledefs.items():
                puts("    %-15s %s" % (role, ",".join(host_list)))
        sys.argv = sys.argv + ["-l"]

    fabric_main.load_fabfile = _load_fabfile
    fabric_main.main()
