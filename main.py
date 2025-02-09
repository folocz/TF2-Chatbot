#! /usr/bin/env python3

import pyinotify
import openai
import valve.rcon
import random
import time
from configparser import ConfigParser

# read config
config = ConfigParser()
config.read("config.ini")

host = config.get("tf2", "rcon_ip")
port = config.getint("tf2", "rcon_port")
rcon_password = config.get("tf2", "rcon_password")
log_file = config.get("tf2", "log_file")

gpt_api_key = config.get("gpt", "api_key")
gpt_model = config.get("gpt", "model")
max_tokens = config.getint("gpt", "max_tokens")
history_length = config.getint("gpt", "history_length")

welcome_message = config.get("misc", "welcome_message")
prefix = config.get("misc", "prefix")
owner_name = config.get("misc", "owner_name")
max_messages = config.getint("misc", "max_message_count")
max_message_length = config.getint("misc", "max_message_length")
unprompted_probability = config.getfloat("misc", "unprompted_probability")


client = openai.OpenAI(api_key=gpt_api_key)

history = []

def ask(question):
    history.append({
        "role": "user",
        "content": question,
    });
    if len(history) > history_length:
        history.pop(0)

    response = client.chat.completions.create(
        model=gpt_model,
        messages=history,
        max_tokens=max_tokens,  # Limit the number of tokens in the response
        temperature=1.0,  # Adjust the creativity of the response (0.0 to 1.0)
        store=True
    )

    resp = response.choices[0].message.content
    print(resp)
    history.append({ "role": "assistant", "content": resp })

    return resp


reading = False
with valve.rcon.RCON((host, port), rcon_password) as rcon:
    def say(message):
        command = f"say {prefix} {message}"
        rcon.execute(command.encode("utf-8"), timeout=1)

    def long_say(message, lim=1):
        if len(message) > max_message_length:
            say(message[:max_message_length - 10])
            time.sleep(1)
            if lim >= 2:
                long_say(message[max_message_length - 10:], lim-1)
        else:
            say(message)

    with open(log_file, "r") as log:
        log.seek(0, 2)
        class EventHandler(pyinotify.ProcessEvent):
            def process_IN_MODIFY(self, event):
                global reading
                if event.pathname != log_file: return
                if (reading): return

                reading = True
                while line := log.readline():
                    if (line.strip() == f"{owner_name} connected"):
                        time.sleep(5)
                        say(welcome_message)
                        continue

                    content = line.split(" :  ")
                    if len(content) != 2\
                        or content[1].startswith(prefix)\
                        or "(TEAM)" in content[0]:
                        continue
                    name, message = content
                    if owner_name in name and message.startswith("echo"):
                        time.sleep(1)
                        say(message)
                    elif "gpt" in message.lower() or (random.uniform(0, 1) < unprompted_probability and owner_name not in name):
                        try:
                            start = time.time()
                            resp = ask(message.strip())
                            mid = time.time()
                            long_say(resp, max_messages)
                            end = time.time()
                            print(f"gpt: {mid - start:.3f}, tf2: {end - mid:.3f}")
                            time.sleep(1)
                            if end - start > 15:
                                print("cleaning")
                                while log.readline(): pass
                                print("cleared")
                                time.sleep(5)
                        except Exception as e:
                            print(e)
                            while log.readline(): pass # clear backlog
                            pass
                reading = False

        wm = pyinotify.WatchManager()
        notifier = pyinotify.Notifier(wm, EventHandler())
        wm.add_watch(log_file, pyinotify.IN_MODIFY)
        notifier.loop()


