import os

from pathvalidate import sanitize_filepath

from .exceptions import Aria2cError
from ..utils import create_folder, write_file


class Aria2c:
    ERROR = 12
    SUCCESS = 0
    WARNING = 13
    DOWNLOAD_EXISTS = 3328

    def __init__(self, directory=os.getcwd()):
        self.directory = create_folder(directory)
        self.aria2c_dump = create_folder(directory)
        self.download_list = []

    def append(self, config):
        native_config = []

        if isinstance(config, str):
            native_config.extend([{"dir": self.directory, "url": config}])
        elif isinstance(config, dict):
            directory = config.get("dir", self.directory)

            if not os.path.isabs(directory):
                directory = sanitize_filepath(os.path.join(self.directory, directory), platform="auto")

            url, urls = config.get("url"), config.get("urls")

            if url:
                native_config.extend([{"dir": directory, "url": url}])
            elif urls:
                native_config.extend([{"dir": directory, "url": url} for url in urls])
        elif isinstance(config, list):
            for conf in config:
                self.append(conf)

        self.download_list.extend(native_config)

    def download(self):
        if not self.download_list:
            print("aria2c: no files to download")
            return

        aria2c_config = ""

        for config in self.download_list:
            aria2c_config += f"{config.pop('url')}\n"
            for option, arg in config.items():
                aria2c_config += f" {option}={arg}\n"
            aria2c_config += "\n"

        exists_checker = ["--continue=true", "--auto-file-renaming=false"][0]

        path = write_file(f"{self.aria2c_dump}/urls.txt", aria2c_config)
        return_code = os.system(f"./aria2c -x 8 -j 8 --check-certificate=false {exists_checker} -i \"{path}\"")
        os.remove(path)

        if return_code not in [self.SUCCESS, self.WARNING, self.DOWNLOAD_EXISTS]:
            raise Aria2cError

        return return_code
