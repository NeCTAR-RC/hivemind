import re
from itertools import chain
from fabric.api import shell_env, parallel, puts, env
from operations import run
import util
import nagios
import puppet
import nova

package_version = re.compile(r'   ([^\s]+) \(([^\s]+) => ([^\s]+)\)')


@parallel(pool_size=20)
def update():
    run("apt-get update")


@parallel(pool_size=10)
def upgrade(packages=[]):
    outage = "Package Upgrade (%s@%s)." % (util.local_user(),
                                           util.local_host())
    if isinstance(packages, dict):
        packages = packages[env.host_string]
    if not packages:
        return
    nagios.ensure_host_maintence(outage)

    # Disable services
    puppet.disable_agent(outage)
    nova.disable_host_services()

    # Do upgrade
    with shell_env(DEBIAN_FRONTEND='non-interactive'):
        run("apt-get install -o Dpkg::Options::='--force-confold' %s" %
            " ".join(packages))

    # Enable services
    if puppet.is_disabled() == outage:
        puppet.enable_agent()
    nova.enable_host_services()
    nagios.cancel_host_maintence(outage)


@parallel(pool_size=20)
def verify():
    result = run("apt-get upgrade --assume-no -V", warn_only=True, quiet=True)
    versions = {}
    read_versions = False
    for line in result.split("\n"):
        if not line.startswith(" "):
            read_versions = False
        if read_versions:
            match = package_version.match(line)
            match = match.groups()
            versions[match[0]] = (match[1], match[2])
        if line.startswith("The following packages will be upgraded:"):
            read_versions = True
    return versions


def filter_packages(host_packages, exclude=[]):
    for packages in host_packages.values():
        for epackage in exclude:
            if epackage in packages:
                del packages[epackage]


def print_changes(host_packages):
    packages = list(set(chain(*[packages.keys()
                                for packages in host_packages.values()])))
    packages.sort()
    puts("\nThe following packages will be upgraded:")
    for package in packages:
        package_versions = [p.get(package) for p in host_packages.values()]
        package_versions = [pv for pv in package_versions if pv is not None]
        from_versions = set([f for f, t in package_versions])
        to_versions = set([t for f, t in package_versions])
        puts("%s (%s) => (%s)" % (package,
                                  ", ".join(from_versions),
                                  ", ".join(to_versions)))
    puts("\n")


def print_changes_perhost(host_packages):
    for host, packages in host_packages.items():
        puts("\n[%s] The following packages will be upgraded:" % host)
        for package, versions in sorted(packages.items()):
            from_versions, to_versions = versions
            puts("%s (%s) => (%s)" % (package, from_versions, to_versions))
    puts("\n\n")
