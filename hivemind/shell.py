import cmd2 as cmd
import os
import re
import shlex
import sys

from hivemind import common


class Shell(cmd.Cmd, object):
    abbrev = False

    def __init__(self, hivemind, *args, **kwargs):
        super(Shell, self).__init__(*args, **kwargs)
        self.hivemind = hivemind
        self.prompt = '%s> ' % os.path.basename(sys.argv[0])
        for cmd in hivemind.command_list():
            setattr(self.__class__, 'do_%s' % cmd, self._make_cmd(cmd))
            setattr(self.__class__, 'complete_%s' % cmd.split('.')[0],
                    self._make_complete())

    @staticmethod
    def _make_cmd(name):
        def handler(self, line):
            args = shlex.split(line)
            success = self.hivemind.execute([name] + args)
            return not success
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

    def cmdloop(self):
        try:
            if sys.argv[1:]:
                self.hivemind.execute()
            else:
                self._cmdloop()
                print
        except KeyboardInterrupt:
            pass

    def _execute(self, line=''):
        args = shlex.split(line)
        return not self.hivemind.execute(args)

    def default(self, line):
        line = re.sub(r'\?$', ' -h', line.strip())
        return self._execute(line)

    def do_help(self, line):
        return self._execute(line + ' -h')

    def emptyline(self):
        pass


class HivemindState(object):
    def __init__(self, state):
        self.state = state

    def execute(self, cmd=None):
        return common.execute_args(self.state, cmd)

    def command_list(self):
        return common.list_commands()

    def argument_list(self, cmd):
        return common.list_arguments(cmd)


def shell(state):
    hivemind_state = HivemindState(state)
    sh = Shell(hivemind_state)
    sh.cmdloop()
