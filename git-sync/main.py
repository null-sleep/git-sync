import re
import os
import logging
import subprocess
import click


class GitSyncException(Exception):
    pass


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Hack to provide key using envvar
SSH_KEY_ENV_VAR = 'GIT_SYNC_SSH_KEY'
DEFAULT_SSH_PATH = '/etc/git-secret/ssh'

username = os.environ.get('GIT_SYNC_USERNAME')
password = os.environ.get('GIT_SYNC_PASSWORD')

#ssh = bool(strtobool(os.environ.get('GIT_SYNC_SSH', False)))
#ssh_file = os.environ.get('GIT_SSH_KEY_FILE', '/etc/git-secret/ssh')
#ssh_env = os.environ.get('GIT_SSH_ENV_VAR', 'GIT_SSH_KEY')

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
        with open(path, 'w+') as fh:
            fh.write(ssh_key)
        os.chmod(path, permission)
        logger.debug('Created ssh key file at: {path} with permission')
    except Exception as e:
        raise GitSyncException('Unable to create ssh key file') from e


def shell():
    pass


@click.command()
@click.option('--repo', envvar='GIT_SYNC_REPO', required=True)
@click.option('--branch', envvar='GIT_SYNC_BRANCH', default='master')
@click.option('--rev', envvar='GIT_SYNC_REV', default='HEAD')
@click.option('--depth', envvar='GIT_SYNC_DEPTH', type=int, default=0)
@click.option('--root', envvar='GIT_SYNC_ROOT')
@click.option('--dest', envvar='GIT_SYNC_DEST', default='')
@click.option('--wait', envvar='GIT_SYNC_WAIT', default=60)
@click.option('--one-time', envvar='GIT_SYNC_RUN_ONCE', type=bool, default=False)

def git_sync(repo, branch, rev, depth, root, dest, wait, one_time):
    home = os.path.expanduser('~')
    ssh_repo_url = get_ssh_url(repo)

    # print(f"{repo}, {branch}, {rev}, {depth}, {root}, {dest}, {wait}, {one_time}, {ssh_repo_url}")
    subprocess.run(['ls', '--all'], check=True, text=True)
    exit()

    if root is None:
        root = os.path.join(home, 'git/')

    dest = dest.rstrip('/')
    if len(dest.split('/')) > 1:
        raise GitSyncException('Destination must be a name')
    dest = os.path.join(root, dest)

    ssh_key = os.getenv(SSH_KEY_ENV_VAR)
    if ssh_key is None:
        raise GitSyncException('Missing environment variable: {SSH_KEY_ENV_VAR}')
    create_ssh_file(ssh_key, DEFAULT_SSH_PATH)

    #sync_repo(repo, branch, rev, depth, root, dest, DEFAULT_SSH_PATH)


if __name__ == '__main__':
    git_sync()
