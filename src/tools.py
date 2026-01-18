import csv
import logging as log
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path


def add_emoji_to_unicode_data(file_path: str):
    with (
        open(file_path, encoding="utf-8") as csvfile,
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
            except UnicodeEncodeError:
                log.error(f"Encoding error at '{unicode}'.")


def download(url, local_filename):
    try:
        log.info(f"Downloading '{url}'...")
        urllib.request.urlretrieve(url, local_filename)
        log.info(f"File '{local_filename}' downloaded successfully.")
    except Exception as e:
        log.error(f"Error downloading the file: {e}")
        raise e


def download_if_missing(url: str, local_filename: str) -> bool:
    if not os.path.exists(local_filename):
        download(url, local_filename)
    return os.path.exists(local_filename)


def run_command(command: list[str], input: str | None = None):
    try:
        encoded_input = input.encode() if input is not None else None
        subprocess.run(command, input=encoded_input, check=True)
    except FileNotFoundError:
        log.warning(f"{command} not found.")
    except Exception as e:
        log.error(f"{command} failed with: {e}")


def get_conf_file(filename: str) -> str:
    if os.environ.get("EMOJI_KBD_DEV"):
        return str(Path("res") / filename)
    config_dir = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "emoji-kbd"
    config_dir.mkdir(parents=True, exist_ok=True)
    default_config = Path(__file__).parent.parent / "res" / filename
    if not (config_dir / filename).exists() and default_config.exists():
        shutil.copy(default_config, config_dir / filename)
        log.info(f"Copied default config from {default_config}")
    path = str(config_dir / filename)
    log.info(f"Config file: {path}")
    return path


def get_state_file(filename: str) -> str:
    if os.environ.get("EMOJI_KBD_DEV"):
        return str(Path(".local") / filename)
    state_dir = Path(os.getenv("XDG_STATE_HOME", Path.home() / ".local/state")) / "emoji-kbd"
    state_dir.mkdir(parents=True, exist_ok=True)
    path = str(state_dir / filename)
    log.info(f"State file: {path}")
    return path


def get_cache_file(filename: str) -> str:
    if os.environ.get("EMOJI_KBD_DEV"):
        return str(Path(".local") / filename)
    cache_dir = Path(os.getenv("XDG_CACHE_HOME", Path.home() / ".cache")) / "emoji-kbd"
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = str(cache_dir / filename)
    log.info(f"Cache file: {path}")
    return path


if __name__ == "__main__":
    log.basicConfig(
        level=log.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    add_emoji_to_unicode_data(".local/UnicodeData.txt")
