from collections import defaultdict
import functools
import pkg_resources
import sys

from fabric.api import env, puts
from fabric.api import task as fabric_task
from fabric import main as fabric_main


def _load_fabfile(path, importer=None):
    all_tasks = defaultdict(dict)
    for entrypoint in pkg_resources.iter_entry_points(group='hivemind.tasks'):
        plugin = entrypoint.load()
        tasks = _load_tasks(plugin)
        for name, task in tasks.items():
            all_tasks[entrypoint.name].update({name: task})
            try:
                namespace = task.wrapped._hivemind['namespace']
            except Exception:
                namespace = entrypoint.name
            all_tasks[namespace].update({name: task})
    return None, all_tasks, None


def _load_tasks(imported):
    return fabric_main.extract_tasks(vars(imported).items())[0]


def task(namespace=None, *args, **kwargs):
    def decorator(func):
        t = fabric_task(*args, **kwargs)
        wrapper = t(func)
        if namespace is not None:
            if not hasattr(wrapper, '_hivemind'):
                wrapper._hivemind = {}
            wrapper._hivemind['namespace'] = namespace
        return wrapper
    return decorator


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
