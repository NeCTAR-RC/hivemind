import sys
from itertools import chain
from fabric.api import env, puts


def main(filename):
    # work around for when python tries to use the byte compile version of the
    # fabfile.
    if filename.endswith('.pyc'):
        filename = filename.replace('.pyc', '.py')

    sys.argv = sys.argv[0:1] + ['-f', filename] + sys.argv[1:]
    if len(sys.argv) == 3 or '-l' in sys.argv:
        if env.roledefs:
            puts("Available roles:\n")
            for role, host_list in env.roledefs.items():
                puts("    %-15s %s" % (role, ",".join(host_list)))
        sys.argv = sys.argv + ["-l"]
    elif '-R' not in sys.argv and '-H' not in sys.argv:
        puts("Running all hosts.")
        hosts = ",".join(chain(*env.roledefs.values()))
        if hosts:
            sys.argv = sys.argv + ["-H", hosts]

    from fabric.main import main
    main()
