# -*- coding: UTF-8 -*-
import sys
import time

import os
import requests
import shutil
from modules import shared
from requests.adapters import HTTPAdapter, Retry
from . import util

dl_ext = ".downloading"

# disable ssl warning info
requests.packages.urllib3.disable_warnings()


# output is downloaded file path
def download(url, path):

    r = util.request(url, token=False, prefix=True, verify=False, stream=True)

    # write to file
    with open(os.path.realpath(path), 'wb') as f:
        r.raw.decode_content = True
        shutil.copyfileobj(r.raw, f)

    return path


# output is downloaded file path
def dl(url, folder, filename=None, filepath=None):
    # resolve filepath
    if not filepath:
        # if filepath is not in parameter, then the folder must be in parameter
        if not folder:
            util.printD("folder is none")
            return

        if not os.path.isdir(folder):
            util.printD("folder does not exist: " + folder)
            return

        if filename:
            filepath = os.path.join(folder, filename)

    if shared.opts.data.get("ch_aria2rpc_enable", False):
        url = util.get_url_from_base_url(url)
        util.printD("Start downloading: " + url)
        aria2rpc_url = f"http://{shared.opts.data.get('ch_aria2rpc_host')}:{shared.opts.data.get('ch_aria2rpc_port')}/jsonrpc"
        params = {
            "id": "civitai",
            "jsonrpc": "2.0",
            "method": "aria2.addUri",
            "params": [
                f"token:{shared.opts.data.get('ch_aria2rpc_secret')}",
                [url],
                {
                    "out": filename,
                    "dir": folder
                }
            ]
        }
        try:
            gid = requests.post(aria2rpc_url, json=params).json()["result"]
            params["params"] = params["params"][:1]
            params["params"].append(gid)
            params["params"].append(["status", "totalLength", "completedLength", "downloadSpeed", "files"])
            params["method"] = "aria2.tellStatus"
            while True:
                try:
                    print()
                    request = requests.post(aria2rpc_url, json=params).json()
                    result = request["result"]
                    if "error" in request or result["status"] == "error":
                        filepath = result["files"][0]["path"]
                        util.printD(f"Oops! file downloading incomplete: {filepath}")
                        return
                    total_size = int(result["totalLength"])
                    downloaded_size = int(result["completedLength"])
                    if 0 < total_size == downloaded_size:
                        filepath = result["files"][0]["path"]
                        break
                    download_speed = round(int(result["downloadSpeed"]) / 1000 / 1000, 1)
                    # progress
                    terminal_size = os.get_terminal_size().columns - 8
                    ratio = downloaded_size / total_size
                    progress = int(100 * ratio)
                    # print("\r%d%%|%s%s|\t%d MB" % (
                    #     progress, '█' * int(ratio * terminal_size), ' ' * int((1 - ratio) * terminal_size),
                    #     download_speed))
                    time.sleep(1)
                except Exception:
                    continue
        except Exception as e:
            util.printD(e)
    else:
        filename, total_size, cd = get_size_and_name(url)

        if total_size < 0:
            util.printD(
                'This model requires an API key to download. More info: https://github.com/butaixianran/Stable-Diffusion-Webui-Civitai-Helper#civitai-api-key')
            return

        if not filepath and not filename:
            util.printD("Fail to get file name from Content-Disposition: " + cd)
            return

        # with folder and filename, now we have the full file path
        filepath = os.path.join(folder, filename)

        util.printD(f"File size: {util.hr_size(total_size)}")
        util.printD("Target filepath: " + filepath)
        base, ext = os.path.splitext(filepath)

        dl_filepath, filepath = resolve_dl_filepath(base, ext, filepath)
        # util.printD(f"Temp file: {dl_filepath}")

        # create header range
        headers = util.def_headers.copy()

        # check if downloading file exists
        downloaded_size = 0
        if os.path.exists(dl_filepath):
            downloaded_size = os.path.getsize(dl_filepath)
            if downloaded_size > 0:
                headers['Range'] = f"bytes={downloaded_size}-"
                util.printD(f"Downloaded size: {util.hr_size(downloaded_size)}")

        try:
            r = util.request(url, stream=True, download_tip=True)
        except Exception:
            util.printD("The model download request failed")
            return

        # write to file
        with open(dl_filepath, "ab") as f:
            # sys.stdout.reconfigure(encoding='utf-8')

            for chunk in r.iter_content(chunk_size=4096):
                downloaded_size += len(chunk)
                f.write(chunk)

                # progress
                terminal_size = os.get_terminal_size().columns - 8
                ratio = downloaded_size / total_size
                progress = int(100 * ratio)
                sys.stdout.write("\r%d%%|%s%s|" % (
                    progress, '█' * int(ratio * terminal_size), ' ' * int((1 - ratio) * terminal_size)))
                sys.stdout.flush()

        # check if this file is downloading complete, by comparing it is size
        if downloaded_size < total_size:
            print()
            util.printD(f"Oops! file downloading incomplete: {filename}")
            return

        # rename file
        os.rename(dl_filepath, filepath)

    util.printD(f"File saved: {filepath}")
    return filepath


def resolve_dl_filepath(base, ext, filepath):
    # check if the file already exists
    count = 2
    new_base = base
    while os.path.isfile(filepath):
        util.printD("File exists: " + util.shorten_path(filepath))
        # re-name
        new_base = base + "_" + str(count)
        filepath = new_base + ext
        count += 1
    # use a temp file for downloading
    dl_file_path = new_base + dl_ext
    return dl_file_path, filepath


def get_size_and_name(url):
    # first request for header
    r = util.request(url, stream=True)
    # get file size
    total_size = int(r.headers.get('Content-Length', -1))
    # headers default is decoded with latin1, so need to re-decode it with utf-8
    cd = r.headers["Content-Disposition"].encode('latin1').decode('utf-8', errors='ignore')
    server_filename = filename_from_content_disposition(cd)

    return server_filename, total_size, cd


def filename_from_content_disposition(cd):
    """
    Extract the filename from the header "Content-Disposition"
    patterns are like: "attachment;filename=FileName.txt"
    in case "" is in CD filename is start and end, need to strip them out
    """
    server_filename = cd.split("=")[1].strip('"')
    return server_filename.encode("ISO-8859-1").decode()
