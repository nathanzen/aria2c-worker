import json
import os
import shutil
import traceback

from flask import request, Response, render_template

from .. import app
from ..models.aria2c.worker import Aria2cWorker
from ..models.utils import unpack_from_b64

A2DLH = Aria2cWorker()


@app.route("/download/<path:name>")
def download_from_aria2(name):
    return A2DLH.get_downloadable_file(name)


@app.route("/delete/<path:name>")
def delete_from_aria2(name):
    return A2DLH.delete_file(name)


@app.route("/status/<path:name>")
def status_from_aria2(name):
    return A2DLH.status(name)


@app.route("/download_task", methods=["POST"])
def download_all_aria2():
    try:
        compressed_dict = request.get_json(force=True)
        downloads = json.loads(unpack_from_b64(compressed_dict["cm"]))
        return A2DLH.download(compressed_dict["name"], downloads)
    except Exception:
        return Response(traceback.format_exc(), status=500)


@app.route("/downloads")
def downloads():
    title = f"Aria2c Downloads"
    files = []

    for name in A2DLH.list_downloaded_files():
        filepath = f"{A2DLH.download_path}/{name}"

        if os.path.isfile(filepath):
            files.append({
                "url": A2DLH.get_downloadable_file(os.path.splitext(name)[0]),
                "name": name,
                "size": os.path.getsize(filepath)
            })

    return render_template("downloads.html", title=title, files=files)


@app.route("/")
def index():
    current_dir = os.getcwd()
    total, used, free = shutil.disk_usage(current_dir)
    return f"{current_dir} = total={total:,}, used={used:.}, free={free,}"
