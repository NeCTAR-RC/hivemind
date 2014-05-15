import os
from fabric.api import (env, task, local)

from hivemind.decorators import verbose
from hivemind import util, git


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
def clone(project_name):
    """Clone a repository from gerrit.

       :param str project_name: The name of the repository you wish to
         clone. (e.g NeCTAR-RC/puppet-openstack)

    """
    user = gitreview_username()
    project = project_name.split('/')[-1]
    local('git clone ssh://%s@review.rc.nectar.org.au:29418/%s %s' % (
          user, project_name, project))


@task
@verbose
def checkout_config(project_name, remote='origin'):
    """Checkout a projects configuration branch.

    """
    git.assert_in_repository()
    local('git fetch %(remote)s '
          'refs/meta/config:refs/remotes/%(remote)s/meta/config' %
          {'remote': remote})
    local('git checkout meta/config')


@task
@verbose
def push_config(project_name, remote='origin'):
    """Push a projects configuration branch.

    """
    git.assert_in_repository()
    local('git push %s meta/config:refs/for/refs/meta/config' % remote)


@task
@verbose
def push_without_review(project_name, branch):
    """Push the given git branch to a remote gerrit repo."""
    git.assert_in_repository()
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
