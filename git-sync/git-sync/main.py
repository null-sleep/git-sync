import os
import logging
from distutils.util import strtobool


class GitSyncException(Exception):
    pass


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

home = os.environ.get('HOME')
repo = os.environ.get('GIT_SYNC_REPO')
branch = os.environ.get('GIT_SYNC_BRANCH', 'master')
rev = os.environ.get('GIT_SYNC_REV', 'HEAD')
depth = int(os.environ.get('GIT_SYNC_DEPTH', 0))
root = os.environ.get('GIT_SYNC_ROOT', os.path.join(home, 'git/'))
dest = os.environ.get('GIT_SYNC_DEST', '')
wait = os.environ.get('GIT_SYNC_WAIT', 0)
sync_timeout = int(os.environ.get('GIT_SYNC_TIMEOUT', 120))
one_time = bool(strtobool(os.environ.get('GIT_SYNC_ONE_TIME', False)))
max_failures = int(os.environ.get('GIT_SYNC_MAX_SYNC_FAILURES', 0))
chmod = int(os.environ.get('GIT_SYNC_PERMISSIONS'))

username = os.environ.get('GIT_SYNC_USERNAME')
password = os.environ.get('GIT_SYNC_PASSWORD')

ssh = bool(strtobool(os.environ.get('GIT_SYNC_SSH', False)))
ssh_file = os.environ.get('GIT_SSH_KEY_FILE', '/etc/git-secret/ssh')
ssh_env = os.environ.get('GIT_SSH_ENV_VAR', 'GIT_SSH_KEY')
# TODO Host Files

# repo = os.environ.get('')

def git_sync():
    if repo is None:
        raise GitSyncException('$GIT_SYNC_REPO must be provided')
    if ssh:
        setup_git_ssh(ssh_file)
