import logging as log
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, get_args, get_origin

from tools import get_conf_file


@dataclass
class BoardConfig:
    layout: str
    default: str
    locale: str


@dataclass
class TerminalConfig:
    width: int
    height: int
    font_size: int
    close_cmd: str


@dataclass
class GuiConfig:
    width: int
    height: int
    key_font_size: float
    mark_font_size: float
    emoji_font_size: float
    emoji_font_size2: float


@dataclass
class LayoutConfig:
    name: str
    char: str
    kbd: str


@dataclass
class SourcesConfig:
    noto_color_emoji: str
    noto_color_emoji_win32: str
    emojibase: str
    unicode_data: str
    unicode_annotations: str


@dataclass
class LoggingConfig:
    log_mode: Literal["w", "a"]
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


@dataclass
class Config:
    board: BoardConfig
    terminal: TerminalConfig
    gui: GuiConfig
    layout: list[LayoutConfig]
    sources: SourcesConfig
    logging: LoggingConfig

    def get_layout(self, name: str | None = None) -> str:
        if name is None:
            name = self.board.layout
        for layout in self.layout:
            if layout.name.lower() == name.lower():
                return layout.kbd
        raise ValueError(f"Layout '{name}' not found in configuration.")


config_path = get_conf_file("emoji-kbd.toml")
default_config_path = get_conf_file("emoji-kbd.toml", default=True)


def __load_config(config_path: str = config_path) -> Config:
    """Load configuration from TOML file.

    Raises:
        FileNotFoundError: If config file does not exist
        tomllib.TOMLDecodeError: If config file is malformed
        KeyError: If section/key does not exit
        ValueError: If field type does not match
    """
    # Load defaults from res/emoji-kbd.toml first
    default_config_data = {}
    path = Path(default_config_path)
    with open(path, "rb") as f:
        default_config_data = tomllib.load(f)

    # Load user config if present
    path = Path(config_path)
    if path.exists() and config_path != default_config_path:
        with open(path, "rb") as f:
            user_config_data = tomllib.load(f)

        # Merge: user config overrides defaults
        for key, value in user_config_data.items():
            if key == "layout" and key in default_config_data:
                # For layout, replace completely (user layouts override defaults)
                default_config_data[key] = value
            else:
                # For other sections, merge recursively
                if key in default_config_data and isinstance(default_config_data[key], dict):
                    default_config_data[key].update(value)
                else:
                    default_config_data[key] = value

    data = default_config_data
    config_dict = {}

    for key, value in data.items():
        if key not in Config.__dataclass_fields__:
            raise KeyError(f"Unknown config section '{key}'")
        field_type = Config.__dataclass_fields__[key].type
        if callable(field_type):  # dataclass
            if get_origin(field_type) is list:
                item_type = get_args(field_type)[0]
                items = []
                for item in value:
                    items.append(item_type(**item))
                config_dict[key] = items
            else:  # single dataclass
                for sub_key in value:
                    if sub_key not in field_type.__annotations__:
                        raise KeyError(f"Unknown key '{sub_key}' in section '{key}'")
                    expected_type = field_type.__annotations__[sub_key]
                    actual_value = value[sub_key]
                    origin = get_origin(expected_type)
                    if origin is Literal:
                        # For Literal types, check if value is one of the allowed values
                        allowed_values = get_args(expected_type)
                        if actual_value not in allowed_values:
                            raise ValueError(
                                f"Invalid value for key '{sub_key}' in section '{key}'. "
                                f"Expected one of {allowed_values}, got {actual_value}."
                            )
                    else:
                        if not isinstance(actual_value, expected_type):
                            raise ValueError(
                                f"Invalid type for key '{sub_key}' in section '{key}'. "
                                f"Expected {expected_type.__name__}, got {type(actual_value).__name__}."
                            )
                config_dict[key] = field_type(**value)
        else:
            config_dict[key] = value

    return Config(**config_dict)

def load_config(config_path: str = config_path) -> Config:
    try:
        return __load_config(config_path)
    except Exception as e:
        log.error(f"Failed to load configuration from {config_path}: {e}")
        raise

if __name__ == "__main__":
    import sys
    from pprint import pprint

    if len(sys.argv) < 2:
        # Pretty print entire config when no args
        config = load_config()
        pprint(config, width=100, sort_dicts=False)
    else:
        # Query mode: python config.py <path.to.value> [config_file]
        # Example: python config.py terminal.width
        # Example: python config.py layout[0].name
        query = sys.argv[1]
        config_file = sys.argv[2] if len(sys.argv) > 2 else config_path

        try:
            config = load_config(config_file)

            # Parse query path like "terminal.width" or "layout[0].name"
            parts = query.replace("[", ".").replace("]", "").split(".")
            value = config

            for part in parts:
                if part.isdigit():
                    value = value[int(part)]  # type: ignore
                else:
                    value = getattr(value, part)

            print(value)
        except (AttributeError, IndexError, KeyError):
            print(f"Error: Invalid query path '{query}'", file=sys.stderr)
            sys.exit(1)
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
