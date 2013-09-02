from fabric.api import puts, local, abort, hide
from fabric.colors import green


def assert_in_repository():
    with hide("everything"):
        try:
            local("git rev-parse --git-dir")
        except:
            abort("ERROR: Must be run from within a git repository.")


def assert_clean_repository():
    with hide("everything"):
        status = local("git status --porcelain", capture=True)
    if len(status) > 0:
        local("git status")
        abort("ERROR: This repository is dirty.")


def describe():
    with hide("everything"):
        return local("git describe", capture=True)


def head():
    with hide("everything"):
        return local("git rev-parse HEAD", capture=True)


def current_branch():
    with hide("everything"):
        return local("git rev-parse --symbolic-full-name --abbrev-ref HEAD", capture=True)


class temporary_merge():
    def __init__(self, branch):
        assert_clean_repository()
        self.old_head = head()
        self.branch = branch

    def __enter__(self):
        puts("Merging {0}".format(green(self.branch)))
        with hide("everything"):
            local("git merge -Xours --no-edit {0}".format(self.branch))
        try:
            assert_clean_repository()
        except:
            abort("ERROR: Can't do a clean merge with {0}.".format(self.branch))
        return self

    def __exit__(self, type, value, traceback):
        puts("Reverting merge of {0}".format(green(self.branch)))
        with hide("everything"):
            local("git reset --hard {0}".format(self.old_head))
