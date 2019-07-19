import re
import os
import time
import logging
import subprocess
from datetime import datetime
import click


class GitSyncException(Exception):
    pass


VAULT_SSH_KEY_FIELD = 'GIT_SYNC_SSH_KEY'
SSH_FILE_PATH = '~/git-secret/git_sync_ssh'
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


# Valid git urls
# git@github.com:jlowin/git-sync.git
# https://github.com/jlowin/git-sync.git
def get_ssh_url(repo):
    match_ssh = re.match(r'git@github.com:(.+?)/(.+?)\.git', repo)
    match_http = re.match(r'https://github.com/(.+?)/(.+?)\.git', repo)
    if match_ssh is not None:
        return repo
    if match_http is not None:
        user = match_http.group(1)
        project = match_http.group(2)
        return f'git@github.com:{user}/{project}.git'

    raise GitSyncException(f'Invalid git repo url: {repo}')


# permission expects an octal
def create_ssh_file(ssh_key, path, permission=0o600):
    logger.info('Setting up ssh key file')
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w+') as fh:
            fh.write(ssh_key)
        os.chmod(path, permission)
        logger.debug('Created ssh key file at: {path} with permission')
    except Exception as e:
        raise GitSyncException('Unable to create ssh key file') from e


def shell(cmd, output=False):
    logger.info(f'Running shell command: {cmd}')
    stdout = subprocess.PIPE if output else subprocess.DEVNULL 
    proc = subprocess.run(cmd, check=True, stdout=stdout, stderr=subprocess.DEVNULL)
    if output:
        return proc.stdout.decode('utf-8') if proc.stdout is not None else ''


def setup_ssh(ssh_file_path='/etc/git-secret/ssh'):
    vault_cmd = ['fetch_vault_secret.sh', 'secret/lemuria/github', VAULT_SSH_KEY_FIELD]
    ssh_key = shell(vault_cmd, output=True)
    if ssh_key is None:
        raise GitSyncException('Missing environment variable: {SSH_KEY_ENV_VAR}')
    if not ssh_key.endswith('\n'):
        ssh_key += '\n'
    create_ssh_file(ssh_key, ssh_file_path)
    disable_host_check = '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
    git_cmd = ['git', 'config', '--global', 'core.sshCommand', f"'ssh {disable_host_check} -i {ssh_file_path}'"]
    try:
        shell(git_cmd)
        logger.debug('Configured git to use ssh key')
    except subprocess.CalledProcessError as e:
        raise GitSyncException('Could not configure git to use ssh file') from e


def clone_repo(repo, branch, sync_dest):
    git_cmd = ['git', 'clone', repo, '--no-checkout', '-b', branch, sync_dest]
    if os.path.exists(sync_dest):
        raise GitSyncException(f'Sync destination already exists: {sync_dest}')
    try:
        shell(git_cmd)
        logger.debug(f'Repo cloned at: {sync_dest}')
    except subprocess.CalledProcessError as e:
        raise GitSyncException('Could not clone repository') from e


def sync_repo(repo, branch, sync_dest):
    git_fetch = ['git', '-C', sync_dest, 'fetch', 'origin', branch]
    git_prune = ['git', '-C', sync_dest, 'gc', '--prune=all']
    git_reset = ['git', '-C', sync_dest, 'rest', '--hard', f'origin/{branch}']
    try:
        shell(git_fetch)
        shell(git_prune)
        shell(git_reset)
        logger.debug(f'Synced at {datetime.now()}')
    except subprocess.CalledProcessError as e:
        raise GitSyncException('Could not sync repository') from e

@click.command()
@click.option('--repo', envvar='GIT_SYNC_REPO', required=True)
@click.option('--branch', envvar='GIT_SYNC_BRANCH', default='master')
@click.option('--root', envvar='GIT_SYNC_ROOT')
@click.option('--dest', envvar='GIT_SYNC_DEST', default='')
@click.option('--wait', envvar='GIT_SYNC_WAIT', default=60)
@click.option('--one-time', envvar='GIT_SYNC_RUN_ONCE', type=bool, default=False)
@click.option('--debug', envvar='GIT_SYNC_DEBUG', is_flag=True)
def git_sync(repo, branch, root, dest, wait, one_time, debug):
    if debug:
        logger.setLevel(logging.INFO)
    ssh_repo_url = get_ssh_url(repo)

    if root is None:
        root = os.path.join('~', 'git/')
    root = os.path.expanduser(root)

    dest = dest.rstrip('/')
    if len(dest.split('/')) > 1:
        raise GitSyncException('Destination must be a name')
    sync_dest = os.path.join(root, dest)

    setup_ssh()
    clone_repo(ssh_repo_url, branch, sync_dest)
    while True:
        sync_repo(ssh_repo_url, branch, sync_dest)
        if one_time:
            break
        time.sleep(wait)


if __name__ == '__main__':
    git_sync() # pylint: disable=no-value-for-parameter
