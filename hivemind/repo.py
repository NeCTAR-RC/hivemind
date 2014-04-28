from fabric.api import (task, hosts, cd, run, hide)

from hivemind.decorators import verbose


def reprepro(command):
    with cd("/data/web/nectar-ubuntu"):
        run("reprepro {0}".format(command))


@task
@verbose
@hosts("repo@mirrors.melbourne.nectar.org.au")
def list(distribution):
    """List all packages in a distribution."""
    reprepro("list {0}".format(distribution))


@task
@verbose
@hosts("repo@mirrors.melbourne.nectar.org.au")
def ls(package):
    """List the package version across all distributions."""
    reprepro("ls {0}".format(package))


@task
@verbose
@hosts("repo@mirrors.melbourne.nectar.org.au")
def list_distributions():
    """List all the distributions."""
    with cd("/data/web/nectar-ubuntu/dists"):
        run("ls")


@task
@verbose
@hosts("repo@mirrors.melbourne.nectar.org.au")
def cp_package(package, source, dest):
    """Copy a package from a source to a destination distribution."""
    with cd("/data/web/nectar-ubuntu"), hide("stdout"):
        packages = run("reprepro listfilter %s '$Source (==%s)' | awk '{print $2}' | sort | uniq" % (source, package))
        run("reprepro copy %s %s %s" % (dest, source, " ".join(packages.splitlines())))


@task
@verbose
@hosts("repo@mirrors.melbourne.nectar.org.au")
def rm_packages(distribution, source_package):
    """Remove distribution packages that belong to the given source package."""
    reprepro("removesrc {0} {1}".format(distribution, source_package))
