"""Run yourself in Terminal; the mailbox password is never printed or saved locally."""
from pathlib import Path
import getpass
import json
import subprocess
import sys
import warnings


def main():
    if not sys.stdin.isatty():
        sys.exit('Run this command directly in Terminal so the password can be entered privately.')
    root = Path(__file__).resolve().parents[1]
    key = root / '.deploy-secrets/hostinger-demo-deploy'
    known_hosts = root / '.deploy-secrets/known_hosts'
    if not key.is_file() or not known_hosts.is_file():
        sys.exit('The verified deployment SSH key and known_hosts file are required in .deploy-secrets.')
    print('Connect hello@bleenky.com to the Bleenky contact form.')
    print('Your password stays hidden and travels only over the verified SSH connection.')
    with warnings.catch_warnings():
        warnings.simplefilter('error', getpass.GetPassWarning)
        password = getpass.getpass('Mailbox password (typing is hidden): ')
    if not password:
        sys.exit('No password entered. Nothing changed.')
    if password != getpass.getpass('Re-enter mailbox password: '):
        sys.exit('Passwords did not match. Nothing changed.')
    command = [
        'ssh', '-T', '-i', str(key), '-p', '65002',
        '-o', 'BatchMode=yes', '-o', 'IdentitiesOnly=yes',
        '-o', 'StrictHostKeyChecking=yes', '-o', f'UserKnownHostsFile={known_hosts}',
        'u496265211@145.223.107.92',
        'php /home/u496265211/.bleenky-mail/setup.php',
    ]
    try:
        result = subprocess.run(command, input=json.dumps({'username':'hello@bleenky.com','password':password}), text=True, timeout=75)
    except subprocess.TimeoutExpired:
        sys.exit('Connection timed out. Ask for a configuration status check before retrying.')
    finally:
        password = None
    sys.exit(result.returncode)


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError, getpass.GetPassWarning):
        sys.exit('\nCancelled. No credentials were submitted.')
