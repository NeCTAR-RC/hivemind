from StringIO import StringIO
from collections import defaultdict
from os import path
import ConfigParser
import argparse
import importlib
import os
import pdb
import pkg_resources
import pkgutil
import re
import sys
import traceback

from docutils import writers, nodes, io
from docutils.core import Publisher
import fabric.main
import fabric.state
import fabric.utils
from fabric.api import env, puts, output, execute
from fabric.api import task as fabric_task

import util

CONF = ConfigParser.ConfigParser()


class DocStringTranslator(nodes.GenericNodeVisitor):
    current_field = None

    def __init__(self, document):
        nodes.NodeVisitor.__init__(self, document)
        self.fields = {}
        self.docstring = StringIO()

    def default_visit(self, node):
        pass

    def default_departure(self, node):
        pass

    def visit_paragraph(self, node):
        if not self.current_field:
            self.docstring.write(node.astext())

    def visit_field(self, node):
        self.current_field = node

    def depart_field(self, node):
        self.current_field = None

    def visit_field_name(self, node):
        self.current_field = node.astext().split(" ")

    def visit_field_body(self, node):
        self.fields[self.current_field[2]] = (self.current_field[1],
                                              node.astext())


class Writer(writers.Writer):
    translator_class = DocStringTranslator

    def translate(self):
        self.visitor = visitor = self.translator_class(self.document)
        self.document.walkabout(visitor)
        self.output = (visitor.docstring, visitor.fields)


def parse_docstring(doc):
    p = Publisher(source=doc, source_class=io.StringInput)
    p.set_reader('standalone', p.parser, 'restructuredtext')
    p.writer = Writer()
    p.process_programmatic_settings(None, None, None)
    p.set_source(doc, None)
    return p.publish()


def _load_fabfile(path=None, importer=None):
    all_tasks = defaultdict(dict)

    for entrypoint in pkg_resources.iter_entry_points(
            group='hivemind.packages'):
        plugin = entrypoint.load()
        tasks = _load_package_tasks(plugin, entrypoint.name)
        for k, v in tasks.items():
            all_tasks[k].update(v)

    for entrypoint in pkg_resources.iter_entry_points(
            group='hivemind.modules'):
        plugin = entrypoint.load()
        tasks = _load_package_or_module_tasks(plugin, entrypoint.name)
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
        if module:
            importlib.import_module(modname)
    tasks = _load_package_or_module_tasks(package, universe)
    for k, v in tasks.items():
        all_tasks[k].update(v)
    return all_tasks


def _load_package_or_module_tasks(module, default_universe):
    # It's defaultdicts all the way down...
    all_tasks = defaultdict(lambda: defaultdict(dict))

    def update_package_task(namespace, name, task):
        try:
            # Maybe override the default namespace
            ns = task._hivemind['namespace']
        except Exception:
            ns = namespace
        all_tasks[default_universe][ns].update({name: task})

    def update_module_task(name, task):
        all_tasks[default_universe].update({name: task})

    def update_namespace(namespace, tasks):
        if isinstance(tasks, dict):
            for name, task in tasks.items():
                if isinstance(task, dict):
                    update_namespace(name, task)
                else:
                    # Only include tasks from this namespace.
                    if task.__module__.startswith(module.__name__):
                        update_package_task(namespace, name, task)
        else:
            update_module_task(namespace, tasks)

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
        default=os.environ.get('ROLES', []),
        action='append',
        metavar='ROLE',
        help='a role to operate on.'
    )

    parser.add_argument(
        '-H', '--hosts',
        default=os.environ.get('HOSTS', []),
        action='append',
        metavar='HOST',
        help="host to operate on."
    )

    parser.add_argument(
        '-X', '--exclude-hosts',
        default=os.environ.get('EXCLUDED_HOSTS', []),
        action='append',
        metavar='HOST',
        help="host to exclude."
    )

    parser.add_argument(
        '-I', '--instance-uuid',
        default=os.environ.get('INSTANCE_UUID', None),
        action='store',
        metavar='INSTANCE',
        help="UUID of instance to operate on."
    )

    parser.add_argument(
        '-T', '--tenant-uuid',
        default=os.environ.get('TENANT_UUID', None),
        action='store',
        metavar='TENANT',
        help="UUID of tenant to operate on."
    )

    parser.add_argument(
        '--pdb',
        default=False,
        action='store_true',
        help="Drop to pdb on error."
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
    """Return an argument tuple that contains both the long and short form
    of the argument e.g. ('--long', '-l')

    """
    long_name = "--" + name.replace('_', '-').lower()
    short_name = "-" + name[0].lower()
    if short_name[1].isalpha():
        return (long_name, short_name)
    return (long_name,)


def register_subcommand(subparsers, name, function):
    """Register a new subcommand.  Return the subcommand parser."""
    conf = command_config(name)
    doc, fields_doc = parse_docstring(function.__doc__ or "")
    doc.seek(0)
    doc = conf.get('@doc', doc.read())
    subcommand = subparsers.add_parser(name,
                                       help=doc,
                                       description=doc)
    args = util.func_args(function)

    # Add the arguments and the function for extraction later.
    subcommand.set_defaults(hivemind_func=function)

    class Nothing:
        pass

    # Pad out the default list with None
    defaults = ((
        Nothing(),) * (len(args.args) - len(args.defaults or tuple())) +
                (args.defaults or tuple()))

    used_short_args = set(['-h'])

    def args_to_options(arg, negative=False):
        options = argname_to_option_flags(arg)

        # Strip duplicate short arguments
        if options[-1] in used_short_args:
            options = options[:-1]
        # No short argument for negative arguments
        elif negative:
            options = options[:-1]
        else:
            used_short_args.add(options[-1])
        return options

    # A list of (argparse_arg, func_arg) mappings
    arg_mapping = []

    # Add all the inspected arguments as flags.
    for arg, default in zip(args.args, defaults):
        kwargs = {}
        if conf.get(arg):
            kwargs['default'] = conf.get(arg)
        elif not isinstance(default, Nothing):
            kwargs['default'] = default

        datatype, field_doc = fields_doc.get(arg, (None, ''))

        if default is True:
            del kwargs['default']
            narg = 'no_' + arg
            arg_mapping.append((narg, arg))
            subcommand.add_argument(
                *args_to_options(narg, negative=True),
                help=field_doc,
                action='store_false', **kwargs)
        elif default is False:
            arg_mapping.append((arg, arg))
            subcommand.add_argument(
                *args_to_options(arg),
                help=field_doc + " (default: %(default)s)",
                action='store_true', **kwargs)
        elif isinstance(default, list):
            arg_mapping.append((arg, arg))
            # If choices then use the first value from the list as the
            # default.
            if datatype == 'choices':
                kwargs['choices'] = kwargs['default']
                kwargs['default'] = kwargs['default'][0]
                action = 'store'
            else:
                action = 'append'
                # When loading default value, if it's as string
                # convert it to a list.
                if isinstance(kwargs['default'], (str, unicode)):
                    kwargs['default'] = kwargs['default'].split(',')

            subcommand.add_argument(
                *args_to_options(arg), action=action,
                help=field_doc + " (default: %(default)s)",
                **kwargs)
        else:
            arg_mapping.append((arg, arg))
            if 'default' in kwargs:
                subcommand.add_argument(
                    *args_to_options(arg), action='store',
                    help=field_doc + " (default: %(default)s)",
                    **kwargs)
            else:
                subcommand.add_argument(
                    arg, action='store',
                    help=field_doc,
                    **kwargs)

    subcommand.set_defaults(hivemind_arg_mapping=arg_mapping)

    return subcommand


def load_rc(program_name):
    """Load the users configuration file.
    Files are expected to exist in ~/.hivemind/(progname)/

    There are 2 files that are loaded.
    - config.ini
    - config.py
    """

    hivemind_config_dir = path.expanduser(path.join("~", ".hivemind"))
    filename = path.join(hivemind_config_dir, program_name)
    if not path.exists(filename):
        os.makedirs(filename)

    conf_filename = path.join(filename, "config.ini")
    if path.exists(conf_filename):
        load_config(conf_filename)
    else:
        # TODO make template based on existing tasks
        open(conf_filename, 'a').close()

    py_filename = path.join(filename, "config.py")
    if path.exists(py_filename):
        sys.path.append(hivemind_config_dir)
        try:
            config = importlib.import_module(
                '%s.%s' % (program_name, 'config'))
        except ImportError:
            execfile(py_filename, globals())
        try:
            config.configure(name=program_name)
        except Exception:
            pass
        sys.path.remove(hivemind_config_dir)
    else:
        # TODO make template
        open(py_filename, 'a').close()


def load_config(filename):
    conf = CONF
    conf.read(filename)


def filter_commands(commands):
    commands = commands.copy()
    try:
        conf = dict(CONF.items('commands'))
    except Exception:
        return commands
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
    except Exception:
        return {}


def flatten_dict_keys(dictionary, prefix=""):
    if isinstance(dictionary, dict):
        for key, subdict in dictionary.items():
            name = '.'.join([prefix, key]) if prefix else key
            for item in flatten_dict_keys(subdict, prefix=name):
                yield item
    else:
        yield prefix


def load_subcommands(commands, parser, prefix=""):
    for command in commands:
        config = command_config(command)
        if '@command' in config:
            alias = True
            function_path = config['@command']
        else:
            alias = False
            function_path = command

        functions = fabric.state.commands
        for cmd_segment in function_path.split('.'):
            try:
                functions = functions[cmd_segment]
            except:
                if alias:
                    print >> sys.stderr, "FAILED to find command for alias %s"\
                        % command
                else:
                    print >> sys.stderr, "FAILED unknown command %s in ini"\
                        % command
                functions = None
                break
        if functions:
            register_subcommand(parser, command, functions)


class HelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    def _metavar_formatter(self, action, default_metavar):
        if action.metavar is not None:
            result = action.metavar
        elif action.choices is not None:
            # NOTE return empty string to prevent printing all
            # subcommands.
            result = ''
        else:
            result = default_metavar

        def format(tuple_size):
            if isinstance(result, tuple):
                return result
            else:
                return (result, ) * tuple_size
        return format

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


def state_init():
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
    commands = set(s.split(':', 1)[1] for s in CONF.sections()
                   if s.startswith('cmd'))
    commands = commands.union(set(flatten_dict_keys(fabric.state.commands)))

    load_subcommands(sorted(list(commands)), subparsers)

    return parser


def execute_args(parser, argv=None):
    if argv is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(argv)

    fabric.state.env['hosts'] = args.hosts
    fabric.state.env['roles'] = args.roles
    fabric.state.env['exclude_hosts'] = args.exclude_hosts
    fabric.state.env['instance_uuid'] = args.instance_uuid
    fabric.state.env['tenant_uuid'] = args.tenant_uuid

    if args.verbose > 0:
        output['everything'] = True

    output['user'] = True

    if hasattr(args, 'hivemind_func'):
        kwargs = dict(
            (func_arg, getattr(args, argparser_arg))
            for (argparser_arg, func_arg) in args.hivemind_arg_mapping)
        execute(args.hivemind_func,
                **kwargs)
        return True
    return False


def list_commands():
    for key, value in fabric.state.commands.items():
        for cmd in value.keys():
            yield '%s.%s' % (key, cmd)


def list_arguments(cmd):
    namespace, command = cmd.split('.')
    command = fabric.state.commands[namespace][command]
    argspec = util.func_args(command)
    return argspec.args


def main_plus():
    from hivemind import shell
    try:
        parser = state_init()
        shell.shell(parser)
    except:
        if '--pdb' in sys.argv:
            type, value, tb = sys.exc_info()
            traceback.print_exc()
            pdb.post_mortem(tb)
        else:
            raise
