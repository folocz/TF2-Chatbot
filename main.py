#! /usr/bin/env python3

import pyinotify
import openai
import valve.rcon
import random
import time

MAX_TOKENS = 40
HISTORY_LEN = 4
MAX_MESSAGES = 3
RESP_PROB = 1.5
log_file = '/media/hdd/SteamLibrary/steamapps/common/Team Fortress 2/tf/console.log'
host = "0.0.0.0"
port = 27015
rcon_password = "<password>"
ignored_username = "Chatbot"


# setup gpt
api_key = ""
with open("api_key") as file:
    api_key = file.readline().strip()

client = openai.OpenAI(
    api_key=api_key
)

history = []

def ask(question):
    history.append({
        "role": "user",
        "content": question,
    });
    if (len(history) > HISTORY_LEN): history.pop(0)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=history,
        max_tokens=MAX_TOKENS,  # Limit the number of tokens in the response
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
        command = f"say [GPT] {message}"
        rcon.execute(command.encode("utf-8"), timeout=1)

    def long_say(message, lim=1):
        if len(message) > 65:
            say(message[:60])
            time.sleep(1)
            if lim >= 2:
                long_say(message[60:], lim-1)
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
                    content = line.split(" :  ")
                    if len(content) != 2\
                        or content[1].startswith("[GPT]")\
                        or "(TEAM)" in content[0]:
                        continue
                    name, message = content
                    if ignored_username in name and message.startswith("echo"):
                        time.sleep(1)
                        say(message)
                    elif "gpt" in message.lower() or (random.uniform(0, 1) < RESP_PROB and ignored_username not in name):
                        try:
                            start = time.time()
                            resp = ask(message.strip())
                            mid = time.time()
                            long_say(resp, MAX_MESSAGES)
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


