from itertools import chain
import re

from fabric.api import env
from fabric.api import parallel
from fabric.api import puts
from fabric.api import shell_env

from hivemind import nagios
from hivemind.operations import run
from hivemind import puppet
from hivemind import util


package_upgrade = re.compile(r'   ([^\s]+) \(([^\s]+) => ([^\s]+)\)')
package_install = re.compile(r'   ([^\s]+) \(([^\s]+)\)')


@parallel(pool_size=20)
def update():
    # update to get latest list
    return run("apt-get update")


@parallel(pool_size=20)
def autoremove():
    # run apt autoremove
    with shell_env(DEBIAN_FRONTEND='noninteractive'):
        run("apt-get autoremove -y -o Dpkg::Options::='--force-confold'")


@parallel(pool_size=10)
def upgrade(packages=[]):
    outage = "Package Upgrade (%s@%s)." % (util.local_user(),
                                           util.local_host())
    if isinstance(packages, dict):
        packages = packages[env.host_string]
    if not packages:
        return
    nagios.ensure_host_maintenance(outage)

    # Disable services
    puppet.disable_agent(outage)

    # Do upgrade
    with shell_env(DEBIAN_FRONTEND='noninteractive'):
        run("apt-get install -y -o Dpkg::Options::='--force-confold' %s" %
            " ".join(packages))

    # Enable services
    if puppet.is_disabled() == outage:
        puppet.enable_agent()
    nagios.cancel_host_maintenance(outage)


def run_upgrade(packages, force_default_config=True):
    if force_default_config:
        options = '--force-confold'
    else:
        options = '--force-confdef'

    with shell_env(DEBIAN_FRONTEND='noninteractive'):
        run("apt-get install -y -o Dpkg::Options::='%s' %s" %
            (options, " ".join(packages)))


@parallel(pool_size=20)
def update_packages():
    result = run("apt-get upgrade --assume-no -V", warn_only=True, quiet=True)
    return result


@parallel(pool_size=20)
def verify():
    result = run("apt-get dist-upgrade --assume-no -V", warn_only=True,
                 quiet=True)
    versions = {}
    install_versions = False
    upgrade_versions = False
    for line in result.split("\n"):
        if not line.startswith(" "):
            upgrade_versions = False
            install_versions = False
        if upgrade_versions:
            match = package_upgrade.match(line)
            match = match.groups()
            versions[match[0]] = (match[1], match[2])
        if install_versions:
            match = package_install.match(line)
            match = match.groups()
            versions[match[0]] = ('not currently installed', match[1])
        if line.startswith("The following packages will be upgraded:"):
            upgrade_versions = True
        if line.startswith("The following NEW packages will be installed:"):
            install_versions = True
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
    puts("\nThe following packages will be upgraded")
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
