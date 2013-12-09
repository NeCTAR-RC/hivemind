import os
from fabric.api import (env, task, local)

from hivemind.decorators import verbose


# This isn't ideal.
USER = os.environ['USER']


# Gerrit doesn't allow shell access, so run() doesn't work here.
def gerrit(command):
    local('ssh -p 29418 %s@review.rc.nectar.org.au gerrit %s' % (
        USER, command))

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
def push_to(remote_path):
    """Push the current git repository to a gerrit repo."""
    local('git push ssh://%s@review.rc.nectar.org.au:29418/%s *:*' % (
        USER, remote_path))
