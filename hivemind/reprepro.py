from fabric.api import (task, hosts, cd, run, hide)


def reprepro(command):
    with cd("/data/web/nectar-ubuntu"):
        run("reprepro {0}".format(command))


@task
@hosts("mirrors.melbourne.nectar.org.au")
def list(distribution):
    """List all packages in a distribution."""
    reprepro("list {0}".format(distribution))


@task
@hosts("mirrors.melbourne.nectar.org.au")
def ls(distribution):
    """List the package version across all distributions."""
    reprepro("ls {0}".format(distribution))


@task
@hosts("mirrors.melbourne.nectar.org.au")
def list_distributions():
    """List all the distributions."""
    with cd("/data/web/nectar-ubuntu/dists"):
        run("ls")

@task
@hosts("mirrors.melbourne.nectar.org.au")
def cp_package(package, source, dest):
    """List all the distributions."""
    with cd("/data/web/nectar-ubuntu"), hide("stdout"):
        packages = run("reprepro listfilter %s '$Source (==%s)' | awk '{print $2}' | sort | uniq" % (source, package))
        run("reprepro copy %s %s %s" % (dest, source, " ".join(packages.splitlines())))
