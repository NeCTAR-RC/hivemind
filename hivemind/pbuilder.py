"""
Build a package
"""

from os.path import expanduser
from fabric.api import task, local, hosts, get, settings, shell_env
from sixpack import ARCH, DIST


def build_trusted():
    db = "~/.trusted.gpg"
    local("touch {0}".format(db))
    local("apt-key --keyring {0} adv --keyserver keyserver.ubuntu.com --recv-keys 5EDB1B62EC4926EA".format(db))
    local("apt-key --keyring {0} adv --keyserver keyserver.ubuntu.com --recv-keys 40976EAF437D05B5".format(db))
    with settings(user='root'):
        get("/data/web/nectar-ubuntu/nectar-custom.gpg", "/tmp/nectar-custom.gpg")
    local("gpg --no-default-keyring --keyring /tmp/nectar-custom.gpg --export | gpg --no-default-keyring --keyring {0} --import".format(db))


@task
@hosts("mirrors.melbourne.nectar.org.au")
def create():
    """Create an environment for building packages."""
    build_trusted()
    keyring = expanduser("~/.trusted.gpg")
    mirror = "http://mirrors.melbourne.nectar.org.au/ubuntu-archive/ubuntu/"
    components = "main universe"
    mirrors = ["deb http://mirrors.melbourne.nectar.org.au/ubuntu-cloud/ubuntu precise-updates/grizzly main",
               "deb http://download.rc.nectar.org.au/nectar-ubuntu precise main",
               "deb http://download.rc.nectar.org.au/nectar-ubuntu precise-grizzly main",
               "deb http://download.rc.nectar.org.au/nectar-ubuntu precise-grizzly-testing main",
               "deb http://download.rc.nectar.org.au/nectar-ubuntu precise-testing main"]

    with shell_env(ARCH=ARCH, DIST=DIST):
        local('git-pbuilder create --mirror {mirror} --components "{components}" --othermirror "{mirrors}" --keyring {keyring} --debootstrapopts --keyring={keyring}'.format(
            mirror=mirror,
            components=components,
            mirrors="|".join(mirrors),
            keyring=keyring))


@task
def shell():
    """Open a shell in the packaging environment."""
    with shell_env(ARCH=ARCH, DIST=DIST):
        local("git-pbuilder login")


@task
def update():
    """Update the packaging environment."""
    with shell_env(ARCH=ARCH, DIST=DIST):
        local("git-pbuilder update")
