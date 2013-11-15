from collections import defaultdict
import ConfigParser
from os import path
import argparse
import functools
import inspect
import pkg_resources
import pkgutil
import re
import sys
import sys

import fabric.main
import fabric.state
import fabric.utils
from fabric.api import env, puts, output, execute
from fabric.api import task as fabric_task


CONF = ConfigParser.ConfigParser()


def _load_fabfile(path=None, importer=None):
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

    def update_task(namespace, name, task):
        try:
            # Maybe override the default namespace
            ns = task._hivemind['namespace']
        except Exception:
            ns = namespace
        all_tasks[default_universe][ns].update({name: task})

    def update_namespace(namespace, tasks):
        for name, task in tasks.items():
            if isinstance(task, dict):
                update_namespace(name, task)
            else:
                update_task(namespace, name, task)

    module_tasks = fabric.main.extract_tasks(vars(module).items())[0]
    for namespace, tasks in module_tasks.items():
        update_namespace(namespace, tasks)
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

    fabric.main.load_fabfile = _load_fabfile
    fabric.main.main()


def env_options(parser):
    """Generate environment dict argument parser."""

    parser.add_argument(
        '-R', '--roles',
        default=[],
        action='append',
        metavar='ROLE',
        help='a role to operate on.'
    )

    parser.add_argument(
        '-H', '--hosts',
        default=[],
        action='append',
        metavar='HOST',
        help="host to operate on."
    )

    parser.add_argument(
        '-X', '--exclude-hosts',
        default=[],
        action='append',
        metavar='HOST',
        help="host to exclude."
    )

    parser.add_argument(
        '-I', '--instance-uuid',
        default=None,
        action='store',
        metavar='INSTANCE',
        help="UUID of instance to operate on."
    )

    parser.add_argument(
        '-T', '--tenant-uuid',
        default=None,
        action='store',
        metavar='TENANT',
        help="UUID of tenant to operate on."
    )


def set_defaults():
    """Override some of the fabric defaults."""

    # Set the default output level.
    output['everything'] = False
    output['running'] = True
    output['warnings'] = True

    # Exit if there are no hosts specified.
    env['abort_on_prompts'] = True

    # Openstack Instance UUID
    env['instance_uuid'] = None

    # Openstack Tenant UUID
    env['tenant_uuid'] = None

    # Instead of offering heaps of ssh configuration options.  You
    # should configure ssh.
    env['use_ssh_config'] = True

    # Output prefix is disabled here because we add it back with the
    # python logging.
    env['output_prefix'] = False


def argname_to_option_flags(name):
    long_name = "--" + name.replace('_', '-').lower()
    short_name = "-" + name[0].lower()
    if short_name[1].isalpha():
        return (long_name, short_name)
    return (long_name,)


def register_subcommand(subparsers, name, function):
    """Register a new subcommand.  Return the subcommand parser."""
    doc = function.__doc__ or ""
    subcommand = subparsers.add_parser(name,
                                       help=doc,
                                       description=doc)
    args = func_args(function)

    # Add the arguments and the function for extraction later.
    subcommand.set_defaults(hivemind_func=function,
                            hivemind_args=args.args)

    class Nothing:
        pass

    # Pad out the default list with None
    defaults = ((Nothing(),) * (len(args.args) - len(args.defaults or tuple()))
                + (args.defaults or tuple()))

    conf = command_config(name)

    # Add all the inspected arguments as flags.
    for arg, default in zip(args.args, defaults):
        kwargs = {}
        if conf.get(arg):
            kwargs['default'] = conf.get(arg)
        elif not isinstance(default, Nothing):
            kwargs['default'] = default
        else:
            kwargs['required'] = True

        subcommand.add_argument(*argname_to_option_flags(arg),
                                action='store', **kwargs)

    return subcommand


def load_rc(program_name):
    """Load the users configuration file."""
    progrc = "." + program_name + "rc"
    filename = path.expanduser(path.join("~", progrc))
    if path.exists(filename):
        try:
            load_config(filename)
        except:
            execfile(filename, globals())


def load_config(filename):
    conf = CONF
    conf.read(filename)


def filter_commands(commands):
    commands = commands.copy()
    conf = dict(CONF.items('commands'))
    namespaces = conf.get('namespaces')
    exclusions = conf.get('exclude_namespaces', '')

    if namespaces:
        commands = {namespace: command for namespace, command in
            commands.items() if namespace in namespaces}
    for exclusion in exclusions.split(','):
        if exclusion:
            del commands[exclusion]
    return commands


def command_config(command_name):
    conf_section = 'cmd:%s' % command_name
    try:
        return dict(CONF.items(conf_section))
    except:
        return {}


def load_subcommands(mapping, parser, prefix=""):
    for command, value in sorted(mapping.items()):
        name = '.'.join([prefix, command]) if prefix else command
        if hasattr(value, 'items'):
            load_subcommands(value, parser, name)
        else:
            register_subcommand(parser, name, value)


def func_args(function):
    "Dig through the decorator wrappers to find the real function arguments."
    func = function
    while func.func_closure or hasattr(func, 'wrapped'):
        if hasattr(func, 'wrapped'):
            func = func.wrapped
            continue
        func = func.func_closure[0].cell_contents
    return inspect.getargspec(func)


class HelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    def _format_args(self, action, default_metavar):
        get_metavar = self._metavar_formatter(action, default_metavar)
        if action.nargs is None:
            result = '%s' % get_metavar(1)
        elif action.nargs == argparse.OPTIONAL:
            result = '[%s]' % get_metavar(1)
        elif action.nargs == argparse.ZERO_OR_MORE:
            result = '[%s [%s ...]]' % get_metavar(2)
        elif action.nargs == argparse.ONE_OR_MORE:
            result = '%s [%s ...]' % get_metavar(2)
        elif action.nargs == argparse.REMAINDER:
            result = '...'
        elif action.nargs == argparse.PARSER:
            result = '<SUBCOMMAND>'
        else:
            formats = ['%s' for _ in range(action.nargs)]
            result = ' '.join(formats) % get_metavar(action.nargs)
        return result


def main_plus():
    parser = argparse.ArgumentParser(formatter_class=HelpFormatter,
                                     conflict_handler='resolve')
    parser.add_argument('-v', '--verbose', action='count')
    subparsers = parser.add_subparsers()
    env_options(parser)

    # Setup environment
    set_defaults()

    # Load config
    load_rc(parser.prog)

    # Load tasks
    docstring, callables, default = _load_fabfile()

    # Filter tasks
    callables = filter_commands(callables)

    fabric.state.commands.update(callables)

    # Register subcommands
    load_subcommands(fabric.state.commands, subparsers)

    args = parser.parse_args()

    fabric.state.env['hosts'] = args.hosts
    fabric.state.env['roles'] = args.roles
    fabric.state.env['exclude_hosts'] = args.exclude_hosts
    fabric.state.env['instance_uuid'] = args.instance_uuid
    fabric.state.env['tenant_uuid'] = args.tenant_uuid

    if args.verbose > 0:
        output['everything'] = True

    if hasattr(args, 'hivemind_func'):

        kwargs = dict((arg, getattr(args, arg))
                      for arg in args.hivemind_args)
        execute(args.hivemind_func,
                **kwargs)
