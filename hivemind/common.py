import sys
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

    from fabric.main import main
    main()
