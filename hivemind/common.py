from collections import defaultdict
import functools
import pkg_resources
import pkgutil
import re
import sys

from fabric.api import env, puts
from fabric.api import task as fabric_task
from fabric import main as fabric_main


def _load_fabfile(path, importer=None):
    all_tasks = defaultdict(dict)
    for entrypoint in pkg_resources.iter_entry_points(group='hivemind.packages'):
        plugin = entrypoint.load()
        tasks = _load_package_tasks(plugin, entrypoint.name)
        for k, v in tasks.items():
            all_tasks[k].update(v)

    for k, v in all_tasks['default'].items():
        all_tasks[k].update(v)
    del all_tasks['default']

    return None, all_tasks, None


def _load_package_tasks(package, universe):
    all_tasks = defaultdict(dict)
    package_iter = pkgutil.walk_packages(
        path=package.__path__,
        prefix=package.__name__+'.',
        onerror=lambda x: None)
    for importer, modname, ispkg in package_iter:
        if re.search(r'.*\.tests.*', modname):
            continue
        module = importer.find_module(modname)
        module = __import__(modname)
        tasks = _load_module_tasks(module, universe)
        for k, v in tasks.items():
            all_tasks[k].update(v)
    return all_tasks


def _load_module_tasks(module, default_universe):
    # It's defaultdicts all the way down...
    all_tasks = defaultdict(lambda: defaultdict(dict))
    module_tasks = fabric_main.extract_tasks(vars(module).items())[0]
    for namespace, tasks in module_tasks.items():
        for name, task in tasks.items():
            try:
                # Maybe override the default namespace
                ns = task._hivemind['namespace']
            except Exception:
                ns = namespace
            all_tasks[default_universe][ns].update({name: task})
    return all_tasks


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
