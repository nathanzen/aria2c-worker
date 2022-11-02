import os
import traceback
from threading import Thread

from flask import jsonify, send_from_directory

from . import DOWNLOAD_PATH, create_folder
from .status import Aria2Status

from .main import Aria2c
from .exceptions import Aria2cError


class Aria2cWorker:
    def __init__(self):
        self.download_path = DOWNLOAD_PATH

        self.download_threads = {}
        self.remote_upload_threads = {}

        self.download_status = {}

    def get_path(self, name):
        download_path = create_folder(f"{self.download_path}/{name}")
        zipfile_path = f"{download_path}.zip"

        return download_path, zipfile_path

    def status(self, name: str):
        # check if status data for 'name' is exists, otherwise it will return the error status

        status = self.download_status.get(name)

        if not status:
            new_status = Aria2Status()
            new_status.set_message(f"{name} doesn't exists.")
            new_status.set_error(True)

            response = jsonify(new_status.get_dict())
            response.status_code = 404
            return response

        return status.get_dict()

    def list_downloaded_files(self):
        return os.listdir(self.download_path)

    def get_downloadable_file(self, name):
        download_path, zipfile_path = self.get_path(name)

        if not os.path.exists(zipfile_path):
            new_status = Aria2Status(f"{name} doesn't exists.")
            new_status.set_error(True)

            response = jsonify(new_status.get_dict())
            response.status_code = 404
            return response

        zipfile_name = os.path.basename(zipfile_path)
        print(f"downloading file {zipfile_name}")
        return send_from_directory(directory=self.download_path, path=zipfile_name, as_attachment=True)

    def delete_file(self, name):
        download_path, zipfile_path = self.get_path(name)

        if not os.path.exists(zipfile_path):
            new_status = Aria2Status(f"{name} doesn't exists")
            new_status.set_error(True)

            response = jsonify(new_status.get_dict())
            response.status_code = 404
            return response

        zipfile_name = os.path.basename(zipfile_path)
        print(f"deleting file {zipfile_name}")
        os.remove(f"{zipfile_path}")

        # and also delete the existing status
        if self.download_status.get(name):
            del self.download_status[name]

        new_status = Aria2Status(f"delete file {zipfile_name} success.")
        new_status.set_done(True)
        return new_status.get_dict()

    def download_task(self, name: str, config: dict):
        status: Aria2Status = self.download_status[name]

        print(f"downloading {name}")
        download_path, zipfile_path = self.get_path(name)

        try:
            status.set_message("downloading files...")

            aria = Aria2c(download_path)
            aria.append(config)
            try:
                aria.download()
                status.set_message("packing files...")
            except Aria2cError:
                status.set_message("[E] packing files...")

            os.system(f'zip -0 -r "{zipfile_path}" "{download_path}"')
            os.system(f'rm -r "{download_path}"')

            status.set_done(True)
            status.set_args(name=name, size=os.path.getsize(zipfile_path))
            status.set_message("success")
        except Exception:
            status.set_message(traceback.format_exc())
            status.set_error(True)
            status.set_args(name=name)

        if self.download_threads.get(name):
            del self.download_threads[name]

    def download(self, name, config):
        download_path, zipfile_path = self.get_path(name)

        if os.path.exists(zipfile_path):
            new_status = Aria2Status(f"{name} exists. please delete or download file.")
            new_status.set_error(True)

            response = jsonify(new_status.get_dict())
            response.status_code = 500
            return response

        if name in self.download_status:
            new_status = Aria2Status(f"{name} is occupied, please use another name.")
            new_status.set_error(True)

            response = jsonify(new_status.get_dict())
            response.status_code = 500
            return response

        download_thread = self.download_threads.get(name)
        if download_thread:
            if download_thread.is_alive():
                new_status = Aria2Status("download_thread is still alive, please wait...")
                return new_status.get_dict()

        self.download_status[name] = Aria2Status()
        self.download_threads[name] = Thread(target=self.download_task, args=(name, config))
        self.download_threads[name].start()

        return Aria2Status("download_thread is now running").get_dict()