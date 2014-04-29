"""
Help building packages.

Examples:

Uploading
sixpack uploadpackage:./packaging/cpuset_1.5.6-3.1~nectar0_amd64.changes

"""
import email
import os
import re

from debian import deb822
from fabric.api import task, local, hosts, run, execute

from hivemind import git
from hivemind import pbuilder
from hivemind.decorators import verbose
from hivemind.pbuilder import (OPENSTACK_RELEASES, STABLE_RELEASE, ARCH,
                               dist_from_release)
from hivemind import repo


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
    """Convert a git version to a debian one."""
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


def backport_version(version, revision=1):
    return "%s+nectar%s" % (version, revision)


def version_without_epoc(version):
    if ":" in version:
        return version.split(":")[1]
    return version


def dpkg_parsechangelog():
    res = local("dpkg-parsechangelog", capture=True)
    return email.message_from_string(res)


def package_filepath(source_package, extension):
    return "{0}/{1}_{2}_{3}.{4}".format(
        pbuilder.package_export_dir(),
        source_package["Source"],
        version_without_epoc(source_package["Version"]),
        ARCH,
        extension)


def changes_filepath(source_package):
    return package_filepath(source_package, 'changes')


def upload_filepath(source_package):
    return package_filepath(source_package, 'upload')


def pbuilder_buildpackage(release):
    with pbuilder.pbuilder_env(release):
        local("git-pbuilder -sa")


def git_buildpackage(current_branch, upstream_tree, release):
    with pbuilder.pbuilder_env(release):
        local("git-buildpackage -sa --git-debian-branch={0} "
              "--git-upstream-tree={1} --git-no-pristine-tar "
              "--git-force-create".format(current_branch, upstream_tree))


@task
@verbose
@hosts("repo@mirrors.melbourne.nectar.org.au")
def uploadpackage(changes, delete_existing=False):
    """Upload a package to the repository, using the changes file."""
    if delete_existing:
        data = open(changes).read()
        source_package = deb822.Changes(data)
        # Delete .upload file so dupload always refreshes the files.
        upload = upload_filepath(source_package)
        local("rm -f {0}".format(upload))
    local("dupload {0}".format(changes))
    if delete_existing:
        # Remove previous package from repository.
        distribution = "{0}-testing".format(source_package["Distribution"])
        execute(repo.rm_packages, distribution, source_package["Source"])
    # Import new packages into repository.
    run("import-new-debs.sh")


def get_debian_commit_number():
    upstream_date = local("git log -1 --pretty='%ci' ORIG_HEAD",
                          capture=True)
    command = "git log --oneline --no-merges --since='{0}' | wc -l".format(
        upstream_date)
    return local(command,  capture=True)


@task
@verbose
def buildpackage(release=None, upload=True):
    """Build a package for the current repository."""
    git.assert_in_repository()
    version = git_version()
    current_branch = git.current_branch()
    if release is None:
        release = parse_openstack_release(current_branch)

    if os.path.exists(os.path.join(git.root_dir(), 'debian/')):
        deb_branch = current_branch
    else:
        deb_branch = debian_branch(version)
        if not git.branch_exists(deb_branch):
            deb_branch = "debian/{0}".format(release)
        assert git.branch_exists(deb_branch), \
            "Debian branch %s doesn't exist" % deb_branch

    with git.temporary_merge(deb_branch) as merge:
        source_package = dpkg_parsechangelog()
        current_version = source_package["Version"]
        version['debian'] = get_debian_commit_number()
        release_version = debian_version(current_version, version)
        dist = dist_from_release(release)
        local("dch -v {0} -D {1}-{2} --force-distribution 'Released'"
              .format(release_version, dist, release))
        local("git add debian/changelog")
        local("git commit -m \"{0}\"".format("Updated Changelog"))
        git_buildpackage(current_branch, upstream_tree=merge.old_head,
                         release=release)
        # Regenerate the source package information since it's changed
        # since we updated the changelog.
        source_package = dpkg_parsechangelog()
        changes = changes_filepath(source_package)
    if upload:
        execute(uploadpackage, changes)


@task
@verbose
def buildbackport(release=None, revision=1, upload=True):
    """Build a package from a downloaded deb source."""
    assert os.path.exists('debian/'), "can't find debian directory."
    source_package = dpkg_parsechangelog()
    current_version = source_package["Version"]
    if not release:
        release = STABLE_RELEASE
    dist = dist_from_release(release)
    release_version = backport_version(current_version, revision)
    if 'nectar' not in current_version:
        local("dch -v {0} -D {1}-{2} --force-distribution 'Backported'"
              .format(release_version, dist, release))
    pbuilder_buildpackage(release=release)
    if upload:
        # Regenerate the source package information since it's changed
        # since we updated the changelog.
        source_package = dpkg_parsechangelog()
        changes = changes_filepath(source_package)
        execute(uploadpackage, changes)


@task
@verbose
def promote(package_name,
            release='%s-%s' % (dist_from_release(STABLE_RELEASE),
                               STABLE_RELEASE)):
    execute(repo.cp_package, package_name, release + '-testing', release)


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
