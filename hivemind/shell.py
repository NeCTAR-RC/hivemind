import cmd2 as cmd
import shlex
import sys

from hivemind import common


class Shell(cmd.Cmd, object):
    prompt = 'hivemind> '
    abbrev = False

    def __init__(self, hivemind, *args, **kwargs):
        super(Shell, self).__init__(*args, **kwargs)
        self.hivemind = hivemind
        for cmd in hivemind.command_list():
            setattr(self.__class__, 'do_%s' % cmd, self._make_cmd(cmd))
            setattr(self.__class__, 'complete_%s' % cmd.split('.')[0],
                    self._make_complete())

    @staticmethod
    def _make_cmd(name):
        def handler(self, line):
            args = shlex.split(line)
            return self.hivemind.execute([name] + args)
        return handler

    @staticmethod
    def _make_complete():
        def handler(self, text, line, begidx, endidx):
            name = line.split()[0]
            args = self.hivemind.argument_list(name)
            def filter_args(arg):
                return arg.startswith(text) and arg not in line
            comps = filter(filter_args, args)
            prefix = 2 - line[begidx - 2:begidx].count('-')
            return map(lambda c: '-' * prefix + c + ' ', comps)
        return handler

    def default(self, line):
        args = shlex.split(line)
        return self.hivemind.execute(args)

    def emptyline(self):
        pass


class HivemindState(object):
    def __init__(self, state):
        self.state = state

    def execute(self, cmd):
        return common.execute_args(self.state, cmd)

    def command_list(self):
        return common.list_commands()

    def argument_list(self, cmd):
        return common.list_arguments(cmd)


def shell(state):
    hivemind_state = HivemindState(state)
    sh = Shell(hivemind_state)
    while True:
        try:
            result = sh.cmdloop()
            if result is None:
                return
        except KeyboardInterrupt:
            sys.exit(0)
        except:
            continue
