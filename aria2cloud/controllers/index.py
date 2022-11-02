import json
import os
import shutil
import traceback
from urllib.parse import quote, quote_plus

from flask import request, Response, render_template, send_from_directory

from .. import app
from ..models.aria2c.worker import Aria2cWorker
from ..models.utils import unpack_from_b64

A2DLH = Aria2cWorker()


@app.route("/download/<path:name>", methods=["GET", "POST"])
def download_from_aria2(name):
    return A2DLH.get_downloadable_file(name)


@app.route("/delete/<path:name>", methods=["POST"])
def delete_from_aria2(name):
    return A2DLH.delete_file(name)


@app.route("/status/<path:name>", methods=["POST"])
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


@app.route("/downloads", methods=["GET"])
def downloads():
    title = f"Aria2c Downloads"
    files = []

    for name in A2DLH.list_downloaded_files():
        filepath = f"{A2DLH.download_path}/{name}"

        if os.path.isfile(filepath):
            files.append({
                "url": f"/download/{os.path.splitext(name)[0]}",
                "name": name,
                "size": os.path.getsize(filepath)
            })

    return render_template("downloads.html", title=title, files=files)


@app.route("/ls_raze/<path:path>", methods=["GET"])
def ls_raze(path):
    title = f"{path}"
    files = []

    for name in os.listdir(path):
        filepath = f"{path}/{name}"

        files.append({
            "url": f"/dl_raze?dir={quote(path)}&name={quote(name)}",
            "name": name,
            "size": os.path.getsize(filepath)
        })

    return render_template("downloads.html", title=title, files=files)


@app.route('/dl_raze')
def dl_raze():
    args = request.args

    directory = args.get("dir")
    name = args.get("name")

    if directory and name:
        try:
            return send_from_directory(directory=directory, path=name, as_attachment=True)
        except Exception as e:
            return {"message": f"{e}"}

    return {"message": "missing parameters"}


@app.route("/health", methods=["GET", "HEAD"])
def heath():
    return "ok"


@app.route("/", methods=["GET"])
def index():
    current_dir = os.getcwd()
    total, used, free = shutil.disk_usage(current_dir)
    return f"{current_dir}<br><br>total={total:,}<br> used={used:,} <br>free={free:,}"
