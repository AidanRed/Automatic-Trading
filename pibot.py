from slackclient import SlackClient
import json
import requests
import command_interpreter
import importlib
import os

TOKEN = "xoxb-288758600325-3YEA3d5q9xjbouBax8WQFymf"
slack_client = SlackClient(TOKEN)

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

def update():
    os.system("git pull")
    importlib.reload(command_interpreter)

"""
def update():
    git = sh.git.bake(_cwd=".")
    git.checkout("-b", "master")
"""

while True:
    for message in slack_client.rtm_read():
        tag = f"<@{slack_user_id}>"
        if "text" in message and message["text"].startswith(tag):
            print(f"Message received: {json.dumps(message, indent=2)}")

            message_text = message["text"].split(tag)[1].strip()

            if message_text == "update":
                update()

            else:
                command_interpreter.interpret(message_text)