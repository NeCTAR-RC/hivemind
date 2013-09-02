import re
import os.path
import logging
import logging.handlers
from collections import deque

from fabric.api import env, puts

console = logging.StreamHandler()
console.setLevel(logging.ERROR)
logging.root.addHandler(console)

handler = logging.handlers.RotatingFileHandler(
    os.path.expanduser('~/.sixpack.log'),
    maxBytes=10 * 1024 * 1024,
    backupCount=5)

logger = logging.getLogger('paramiko.transport')
logger.setLevel(logging.WARNING)
logger = logging.getLogger('paramiko.hostkeys')
logger.setLevel(logging.WARNING)

formatter = logging.Formatter('%(asctime)s %(name)-35s: %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logging.root.addHandler(handler)
logging.root.setLevel(logging.INFO)
ansi_escape = re.compile(r'\x1b[^m]*m')


class StreamLogger(object):
    def __init__(self):
        self.logger = logging.getLogger(env.host_string)
        self.linebuf = ''
        self.last_line = ""
        self.line_count = 0
        self.recent_lines = deque(maxlen=10)

    def write(self, buf):
        """Write output to logfile, try and reduce the number of duplicated
        lines.

        """
        for line in buf.rstrip().splitlines():
            self.recent_lines.append(line)
            line = line.rstrip()
            line = ansi_escape.sub('', line)
            if line == self.last_line:
                self.line_count += 1
                continue
            if self.line_count > 0:
                self.logger.info("Previous Line [%s times]", self.line_count)
                self.line_count = 0
            else:
                self.logger.info("%s", line)
                self.last_line = line

    def flush(self):
        pass

    def print_recent(self):
        for line in self.recent_lines:
            puts("[%s] %s" % (env.host_string, line))


def stdio():
    stdout = StreamLogger()
    stderr = StreamLogger()
    stderr.recent_lines = stdout.recent_lines
    return stdout, stderr


def msg(message, *args, **kwargs):
    log = logging.getLogger(env.host_string)
    log.info(message, *args, **kwargs)


def err(message, *args, **kwargs):
    log = logging.getLogger(env.host_string)
    log.info(message, *args, **kwargs)
