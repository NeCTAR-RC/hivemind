"""
Help building packages.

Examples:

Uploading
sixpack uploadpackage:./packaging/cpuset_1.5.6-3.1~nectar0_amd64.changes

"""
import ConfigParser
import email
import os
import re

from fabric.api import task, local, hosts, run, execute

from hivemind import git
from hivemind import pbuilder
from hivemind.decorators import verbose
from hivemind.pbuilder import OPENSTACK_RELEASES, STABLE_RELEASE, ARCH, DIST
from hivemind import reprepro


def debian_branch(version):
    return "debian/{major}.{minor}".format(**version)


def split_branch(branch):
    # Openstack style
    release = branch.split("/")
    if len(release) > 1:
        return release[1]

    # Nectar style
    release = branch.split("_")
    if len(release) > 1:
        return release[1]


def parse_openstack_release(branch):
    release = split_branch(branch)
    if release in OPENSTACK_RELEASES:
        return release
    return STABLE_RELEASE


GIT_DESCRIBE_VERSION_REGEX = re.compile(
    r"""
    ^(?P<major>\d+)\.
    (?P<minor>\d+)
    (?:\.(?P<patch>\d+)){0,1}
    (?:-(?P<commits>\d+)
    -g(?P<revision>[0-9a-f]+)){0,1}$""",
    re.VERBOSE)


def git_version():
    version = git.describe()
    match = GIT_DESCRIBE_VERSION_REGEX.search(version)
    if not match:
        raise Exception("Unable to parse version %s" % version)
    return match.groupdict()


def debian_version(old_version, version):
    """convert a git version to a debian one."""
    new_version = version.copy()
    deb_version = ""
    if ":" in old_version:  # version has epoc.
        epoc = old_version.split(":")[0] + ":"
        deb_version += epoc
    deb_version += "{major}.{minor}"
    if new_version['patch'] is not None:
        deb_version += ".{patch}"
    if new_version['revision'] is not None:
        deb_version += "+a{commits}~g{revision}"
    deb_version += "-{debian}"
    return deb_version.format(**new_version)


def version_without_epoc(version):
    if ":" in version:
        return version.split(":")[1]
    return version


def package_export_dir():
    config = ConfigParser.ConfigParser()
    config.read(os.path.expanduser('~/.gbp.conf'))
    return config.get('git-buildpackage', 'export-dir')


def dpkg_parsechangelog():
    res = local("dpkg-parsechangelog", capture=True)
    return email.message_from_string(res)


def package_changes(source_package):
    return "{0}_{1}_{2}.changes".format(
        source_package["Source"],
        version_without_epoc(source_package["Version"]),
        ARCH)


def git_buildpackage(current_branch, upstream_tree, release):
    with pbuilder.pbuilder_env(release):
        local("git-buildpackage -sa --git-debian-branch={0} "
              "--git-upstream-tree={1} --git-no-pristine-tar "
              "--git-force-create".format(current_branch, upstream_tree))


@task
@verbose
@hosts("repo@mirrors.melbourne.nectar.org.au")
def uploadpackage(package):
    """Upload a package to the repository, using the changes file."""
    local("dupload {0}".format(package))
    run("import-new-debs.sh")


@task
@verbose
def buildpackage(release=None):
    """Build a package for the current repository."""
    git.assert_in_repository()
    version = git_version()
    current_branch = git.current_branch()
    if release is None:
        release = parse_openstack_release(current_branch)
    deb_branch = debian_branch(version)
    if not git.branch_exists(deb_branch):
        deb_branch = "debian/{0}".format(release)

    with git.temporary_merge(deb_branch) as merge:
        source_package = dpkg_parsechangelog()
        current_version = source_package["Version"]
        upstream_date = local("git log -1 --pretty='%ci' ORIG_HEAD",
                              capture=True)
        command = "git log --oneline --no-merges --since='{0}' | wc -l".format(
            upstream_date)
        version['debian'] = local(command,  capture=True)
        release_version = debian_version(current_version, version)
        local("dch -v {0} -D precise-{1} --force-distribution 'Released'"
              .format(release_version, release))
        local("git add debian/changelog")
        local("git commit -m \"{0}\"".format("Updated Changelog."))
        git_buildpackage(current_branch, upstream_tree=merge.old_head,
                         release=release)
        # Regenerate the source package information since it's changed
        # since we updated the changelog.
        source_package = dpkg_parsechangelog()
        changes = package_changes(source_package)
    execute(uploadpackage, "{0}/{1}".format(package_export_dir(), changes))


@task
@verbose
def promote(package_name, release='%s-%s' % (DIST, STABLE_RELEASE)):
    execute(reprepro.cp_package, package_name, release + '-testing', release)


@task
@verbose
def create_deb_branch(branch_name, source_debian_dir):
    """Create a debian branch from a source debian directory."""
    # Make sure the repo is clean, since we run git clean later
    # without confirmation.
    git.assert_clean_repository()
    local("git symbolic-ref HEAD refs/heads/{0}".format(branch_name))
    local("rm .git/index")
    local("git clean -fdx")
    local("cp -r {0} debian".format(source_debian_dir))
    local("git add debian")
    local('git commit -m "Initial import of debian package"')