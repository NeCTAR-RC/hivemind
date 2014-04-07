import os
from fabric.api import (env, task, local)

from hivemind.decorators import verbose
from hivemind import util


def gitreview_username():
    with util.hide_and_ignore():
        username = local('git config --get gitreview.username', capture=True)
    return username or os.environ['USER']


# Gerrit doesn't allow shell access, so run() doesn't work here.
def gerrit(command):
    cmd('gerrit', command)


def cmd(*args):
    user = gitreview_username()
    command = ' '.join(args)
    local('ssh -p 29418 %s@review.rc.nectar.org.au %s' % (
        user, command))


@task
@verbose
def ls():
    """List projects in gerrit."""
    gerrit('ls-projects')


@task
@verbose
def create(name):
    """Create a new project in gerrit."""
    gerrit('create-project --name %s' % name)


@task
@verbose
def push_without_review(project_name, branch):
    """Push the given git branch to a remote gerrit repo."""
    user = gitreview_username()
    local('git push ssh://%s@review.rc.nectar.org.au:29418/%s %s:refs/heads/%s' % (
          user, project_name, branch, branch))


@task
@verbose
def replicate(url=None):
    """Replicate projects to external repositories.

    Replicates all project by default.
    Use --url to restrict by target repository URL substring.
    """
    if url is None:
        arg = '--all'
    else:
        arg = '--url %s' % url
    cmd('replication start', arg)
