"""
Build a package
"""
import ConfigParser
import os
from os.path import expanduser

from fabric.api import task, local, get, settings, shell_env

from hivemind.decorators import verbose

DIST = "precise"
ARCH = "amd64"

STABLE_RELEASE = "havana"
OPENSTACK_RELEASES = ['havana', 'grizzly']


def build_trusted():
    db = "~/.trusted.gpg"
    local("touch {0}".format(db))
    local("apt-key --keyring {0} adv --keyserver keyserver.ubuntu.com --recv-keys 5EDB1B62EC4926EA".format(db))
    local("apt-key --keyring {0} adv --keyserver keyserver.ubuntu.com --recv-keys 40976EAF437D05B5".format(db))
    with settings(user='root'):
        get("/data/web/nectar-ubuntu/nectar-custom.gpg", "/tmp/nectar-custom.gpg")
    local("gpg --no-default-keyring --keyring /tmp/nectar-custom.gpg --export | gpg --no-default-keyring --keyring {0} --import".format(db))


mirrors = {
    'grizzly': ["deb http://mirrors.melbourne.nectar.org.au/ubuntu-cloud/ubuntu precise-updates/grizzly main",
                "deb http://download.rc.nectar.org.au/nectar-ubuntu precise main",
                "deb http://download.rc.nectar.org.au/nectar-ubuntu precise-grizzly main",
                "deb http://download.rc.nectar.org.au/nectar-ubuntu precise-grizzly-testing main",
                "deb http://download.rc.nectar.org.au/nectar-ubuntu precise-testing main"],
    'havana': ["deb http://mirrors.melbourne.nectar.org.au/ubuntu-cloud/ubuntu precise-updates/havana main",
                "deb http://download.rc.nectar.org.au/nectar-ubuntu precise main",
                "deb http://download.rc.nectar.org.au/nectar-ubuntu precise-havana main",
                "deb http://download.rc.nectar.org.au/nectar-ubuntu precise-havana-testing main",
                "deb http://download.rc.nectar.org.au/nectar-ubuntu precise-testing main"],
}


def package_export_dir():
    config = ConfigParser.ConfigParser()
    config.read(os.path.expanduser('~/.gbp.conf'))
    return os.path.abspath(config.get('git-buildpackage', 'export-dir'))


def pbuilder_env(os_release):
    dist_release = '{0}-{1}'.format(DIST, os_release)
    return shell_env(ARCH=ARCH, DIST=dist_release,
                     GIT_PBUILDER_OUTPUT_DIR=package_export_dir())


@task
@verbose
def create(os_release=STABLE_RELEASE):
    """Create an environment for building packages."""
    build_trusted()
    keyring = expanduser("~/.trusted.gpg")
    mirror = "http://mirrors.melbourne.nectar.org.au/ubuntu-archive/ubuntu/"
    components = "main universe"

    other_mirrors = mirrors[os_release]

    with shell_env(ARCH=ARCH, DIST=DIST):
        local('git-pbuilder create --mirror {mirror} --components "{components}" --othermirror "{mirrors}" --keyring {keyring} --debootstrapopts --keyring={keyring}'.format(
            mirror=mirror,
            components=components,
            mirrors="|".join(other_mirrors),
            keyring=keyring))


@task
@verbose
def shell(os_release=STABLE_RELEASE):
    """Open a shell in the packaging environment."""
    with pbuilder_env(os_release):
        local("git-pbuilder login")


@task
@verbose
def update(os_release=STABLE_RELEASE):
    """Update the packaging environment."""
    with pbuilder_env(os_release):
        local("git-pbuilder update")
