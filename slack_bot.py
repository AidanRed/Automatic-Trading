"""
 - Clean up variables (use more constants and make them more dynamic - must work on Raspberry Pi)
 - Move more of this file to CryptoBot so that it can be maintained and updated easily (all that needs to be in this file is a runner and reloader)
   since updating the module while it's running isn't a problem as it's kept in memory
"""

from slackclient import SlackClient
import json
import requests
import importlib
import subprocess
from . import config
from os import path

TOKEN = config.MY_ACCOUNT["slack_token"]
slack_client = SlackClient(TOKEN)

REPOSITORY = "git@bitbucket.org:AidanRed/cryptobot.git"
REPO_NAME = "CryptoBot"

user_list = slack_client.api_call("users.list")
for user in user_list.get("members"):
    if user.get("name") == "pibot":
        slack_user_id = user.get("id")
        break

if slack_client.rtm_connect():
    print("Connected!")


def send_message(message, channel):
    slack_client.api_call("chat.postMessage", channel=channel, text=message, as_user=True)


def receive_file(url):
    local_filename = url.split('/')[-1]
    r = requests.get(url, headers={"Authorization": f"Bearer {TOKEN}"}, stream=True)

    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)

    return local_filename


def update(revision=None):
    # TODO: This requires a password (use popen communicate? Subprocess.run? Send encrypted passphrase?)
    repo_folder = path.join(".", REPO_NAME)
    if path.exists(repo_folder):
        subprocess.Popen(["rm", "-rf", repo_folder])

    subprocess.Popen(["git", "clone", REPOSITORY])
    if revision is not None:
        subprocess.Popen(["git", "reset", "--hard", revision], cwd=repo_folder)

    importlib.reload(command_interpreter)

"""
def update():
    git = sh.git.bake(_cwd=".")
    git.checkout("-b", "master")
"""