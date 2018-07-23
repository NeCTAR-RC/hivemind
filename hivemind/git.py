from fabric.api import puts, local, abort, hide
from fabric.colors import green

import re
import util


def assert_in_repository():
    with hide("everything"):
        try:
            local("git rev-parse --git-dir")
        except Exception:
            abort("ERROR: Must be run from within a git repository.")


def assert_clean_repository():
    with hide("everything"):
        status = local("git status --porcelain", capture=True)
    if len(status) > 0:
        local("git status")
        abort("ERROR: This repository is dirty.")


GIT_VERSION_REGEX = re.compile(
    r"^git version ?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)")


def version():
    with hide("everything"):
        version_str = local("git version", capture=True)
        version = GIT_VERSION_REGEX.search(version_str)
        if not version:
            raise Exception("Unable to parse version %s" % version_str)
        return version.groupdict()


def describe():
    with hide("everything"):
        return local("git describe --tags", capture=True)


def head():
    with hide("everything"):
        return local("git rev-parse HEAD", capture=True)


def root_dir():
    with hide("everything"):
        return local("git rev-parse --show-toplevel", capture=True)


def current_branch():
    with hide("everything"):
        return local("git rev-parse --symbolic-full-name --abbrev-ref HEAD",
                     capture=True)


def branch_exists(branch_name):
    with util.hide_and_ignore():
        result = local("git show-ref --verify --quiet refs/heads/{0}"
                       .format(branch_name))
        return result.succeeded


class temporary_merge():
    def __init__(self, branch):
        assert_clean_repository()
        self.old_head = head()
        self.branch = branch

    def __enter__(self):
        puts("Merging {0}".format(green(self.branch)))
        with hide("everything"):
            git_version = version()
            args = ['-Xours', '--no-edit']
            if git_version['major'] >= 2 and git_version['minor'] >= 17:
                args.append('--allow-unrelated-histories')
            local("git merge {0} {1}".format(" ".join(args), self.branch))
        try:
            assert_clean_repository()
        except Exception:
            abort("ERROR: Can't do a clean merge with {0}."
                  .format(self.branch))
        return self

    def __exit__(self, type, value, traceback):
        puts("Reverting merge of {0}".format(green(self.branch)))
        with hide("everything"):
            local("git reset --hard {0}".format(self.old_head))
