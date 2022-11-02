import base64
import json
import os
import zlib


def create_folder(path: str):
    if not os.path.exists(path):
        os.makedirs(path)

    return path


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        if isinstance(content, dict):
            json.dump(content, f)
        elif isinstance(content, list):
            json.dump(content, f)
        else:
            f.write(content)

    return path


def read_file(path, as_json=False):
    if os.path.exists(path):
        with open(path) as f:
            content = f.read()

        if as_json:
            content = json.loads(content)

        return content


def unpack_from_b64(b64):
    return zlib.decompress(base64.b64decode(b64.encode())).decode()
