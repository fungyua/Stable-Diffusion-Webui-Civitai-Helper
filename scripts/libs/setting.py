# -*- coding: UTF-8 -*-
# collecting settings to here
import json
import modules.scripts as scripts
import os
from . import util

name = "setting.json"
path = os.path.join(scripts.basedir(), name)

data = {
    "model": {
        "max_size_preview": True,
        "skip_nsfw_preview": False
    },
    "general": {
        "open_url_with_js": True,
        "base_url": ""
    },
    "tool": {
        "aria2rpc": {
            "enable": False,
            "host": "localhost",
            "port": 6800,
            "secret": ""
        }
    }
}


# save setting
# return output msg for log
def save():
    print("Saving setting to: " + path)

    json_data = json.dumps(data, indent=4)

    # write to file
    try:
        with open(path, 'w') as f:
            f.write(json_data)
    except Exception as e:
        util.printD("Error when writing file:" + path)
        output = str(e)
        util.printD(str(e))
        return output

    output = "Setting saved to: " + path
    util.printD(output)

    return output


# load setting to global data
def load():
    # load data into global data
    global data

    util.printD("Load setting from: " + path)

    if not os.path.isfile(path):
        return

    with open(path, 'r') as f:
        json_data = json.load(f)

    # check error
    if not json_data:
        util.printD("load setting file failed")
        return

    data = json_data

    return


# save setting from parameter
def save_from_input(max_size_preview, skip_nsfw_preview, open_url_with_js, base_url,
                    aria2rpc_enable, aria2rpc_host, aria2rpc_port, aria2rpc_secret):
    global data
    data = {
        "model": {
            "max_size_preview": max_size_preview,
            "skip_nsfw_preview": skip_nsfw_preview
        },
        "general": {
            "open_url_with_js": open_url_with_js,
            "base_url": base_url
        },
        "tool": {
            "aria2rpc": {
                "enable": aria2rpc_enable,
                "host": aria2rpc_host,
                "port": aria2rpc_port,
                "secret": aria2rpc_secret
            }
        }
    }

    return save()
