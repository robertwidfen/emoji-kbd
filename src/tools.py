import os
import subprocess
from typing import LiteralString
import urllib.request
import csv
import logging as log


def add_emoji_to_unicode_data(file_path: str):
    with (
        open(file_path, mode="r", encoding="utf-8") as csvfile,
        open(
            os.path.dirname(file_path) + f"/e{os.path.basename(file_path)}",
            mode="w",
            encoding="utf-8",
        ) as outfile,
    ):
        reader = csv.reader(csvfile, delimiter=";")
        for row in reader:
            if len(row) < 3:
                continue
            unicode = int(row[0], 16)
            if (
                (unicode >= 0x0 and unicode < 0x20)
                or (unicode >= 0x7F and unicode < 0xA0)
                or (unicode >= 0x400 and unicode < 0xF000)
                or unicode >= 0xF0000
                or unicode in (0x2029, 0x2029)
            ):
                continue
            char = chr(unicode)

            try:
                outfile.write(f"{char},{','.join(row)}\n")
            except:
                pass


def download(url, local_filename):
    try:
        log.info(f"Downloading '{url}'...")
        urllib.request.urlretrieve(url, local_filename)
        log.info(f"File '{local_filename}' downloaded successfully.")
    except Exception as e:
        log.error(f"Error downloading the file: {e}")
        raise e


def download_if_missing(url: str, local_filename: str):
    if not os.path.exists(local_filename):
        download(url, local_filename)
        return True
    return False


def run_command(command: list[str], input: str | None = None):
    try:
        encoded_input = input.encode() if input is not None else None
        subprocess.run(command, input=encoded_input, check=True)
    except FileNotFoundError:
        log.warning(f"{command} not found.")
    except Exception as e:
        log.error(f"{command} failed with: {e}")


if __name__ == "__main__":
    log.basicConfig(
        # filename='app.log',
        # filemode='a',
        level=log.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    add_emoji_to_unicode_data(".local/UnicodeData.txt")
