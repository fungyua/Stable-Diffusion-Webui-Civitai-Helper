# -*- coding: UTF-8 -*-
# handle msg between js and python side
import json
from . import util

# action list
js_actions = ("open_url", "add_trigger_words", "use_preview_prompt", "delete_model", "dl_model_new_version")
py_actions = ("open_url", "delete_model")


# handle request from javascript
# parameter: msg - msg from js as string in a hidden textbox
# return: dict for result
def parse_js_msg(msg):
    msg_dict = json.loads(msg)

    # in case client side run 'JSON.stringify' twice
    if type(msg_dict) is str:
        msg_dict = json.loads(msg_dict)

    if "action" not in msg_dict.keys():
        util.printD("Can not find action from js request")
        return

    action = msg_dict["action"]
    if not action:
        util.printD("Action from js request is None")
        return

    if action not in js_actions:
        util.printD("Unknown action: " + action)
        return

    util.printD("End parse js msg")

    return msg_dict


# build python side msg for sending to js
# parameter: content dict
# return: msg as string, to fill into a hidden textbox
def build_py_msg(action: str, content: dict):
    if not content:
        util.printD("Content is None")
        return

    if not action:
        util.printD("Action is None")
        return

    if action not in py_actions:
        util.printD("Unknown action: " + action)
        return

    return json.dumps({
        "action": action,
        "content": content
    })
