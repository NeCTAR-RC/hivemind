import re

from fabric.api import abort
from fabric.api import hide
from fabric.api import local
from fabric.api import puts
from fabric.colors import green

from hivemind import util


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
    r"^git version ?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
)


def version():
    with hide("everything"):
        version_str = local("git version", capture=True)
        version = GIT_VERSION_REGEX.search(version_str)
        if not version:
            raise Exception(f"Unable to parse version {version_str}")
        return version.groupdict()


def describe():
    with hide("everything"):
        return local(
            "git describe --tags --match '[0-9]*.[0-9]*' "
            "--match 'v[0-9]*.[0-9]*'",
            capture=True,
        )


def head():
    with hide("everything"):
        return local("git rev-parse HEAD", capture=True)


def root_dir():
    with hide("everything"):
        return local("git rev-parse --show-toplevel", capture=True)


def current_branch():
    with hide("everything"):
        return local(
            "git rev-parse --symbolic-full-name --abbrev-ref HEAD",
            capture=True,
        )


def branch_exists(branch_name):
    with util.hide_and_ignore():
        result = local(
            f"git show-ref --verify --quiet refs/heads/{branch_name}"
        )
        return result.succeeded


class temporary_merge:
    def __init__(self, branch):
        assert_clean_repository()
        self.old_head = head()
        self.branch = branch

    def __enter__(self):
        puts(f"Merging {green(self.branch)}")
        with hide("everything"):
            gv = version()
            args = ['-Xours', '--no-edit']
            if int(gv['major']) >= 2 and int(gv['minor']) >= 17:
                args.append('--allow-unrelated-histories')
            local("git merge {} {}".format(" ".join(args), self.branch))
        try:
            assert_clean_repository()
        except Exception:
            abort(f"ERROR: Can't do a clean merge with {self.branch}.")
        return self

    def __exit__(self, type, value, traceback):
        puts(f"Reverting merge of {green(self.branch)}")
        with hide("everything"):
            local(f"git reset --hard {self.old_head}")
