# Emoji Kbd <img src="res/emoji-kbd.svg" alt="Emoji Kbd" width="32" style="vertical-align: bottom; padding-bottom: 4px"/>

## 🚀 Features

- Packed with 3940 emojis 🤩 including 2030 skin tone variants and 5249 symbols Ω in 35 groups ⯒.
- Fast keyboard ⌨️ and mouse 🖱️ navigation.
- Combined favorites ⭐️ and recent ⟲ list.
- Powerful search 🔎.
- Grouping of people emojis differing just by gender 🎅🤶🧑‍🎄 
- Terminal 📟️ version available.
- Localization 🏳️‍🌈 where available.
- Cross ⚔️ platform.

## 🎯 Why Choose Emoji Kbd?

It is all about efficiency - the fewer keys you need to type the better.
Emoji Kbd is made for efficiency.

Three key presses are enough to get an emoji from the recent list:

1. Press <kbd>Win-.</kbd> to open Emoji Kbd.
2. Press the associated <kbd>key</kbd> of an emoji.
3. Press <kbd>Enter</kbd> to close and insert.

## 🖼️ Screenshots

The GUI with DE layout

<video src="https://github.com/user-attachments/assets/93a74a6d-8692-4574-b4c1-11c6136bea9f" width="500" alt="GUI Demo" controls></video>

Terminal - use kitty for best results - other terminals do not handle all graphemes,
e.g ghostty works mostly, alacritty not so well - you will see miss alignment of columns,
monochrome emojis, etc.

You may also need to play with font config to get Noto Color Emoji available in your terminal.

<video src="https://github.com/user-attachments/assets/48af346a-b527-45f0-903d-0144b973e36c" width="500" alt="Terminal Demo" controls></video>

## 👆 UI

Top left is the emoji input field and on the right the search field.

In the middle is a (key)board like overview of emoji groups or emojis.
Each one has a <kbd>key</kbd> associated with it that opens the group or inserts the emoji.

At the bottom is a status field showing information about the selected emoji.

Closing will copy the content of the input field to the clipboard and print it to stdout.

If your window manager supports it, a left click in left half of status allows for moving the window and in right half allows for resizing.

## 🔑 Key bindings

| Key 🖮                                              | Action                           |
|-----------------------------------------------------|----------------------------------|
| **Global**                                                                             |
| <kbd>Cursor</kbd>, <kbd>Home</kbd>, <kbd>End</kbd>  | navigate around                  |
| <kbd>Ctrl-I</kbd>                                   | focus input                      |
| <kbd>Ctrl-F</kbd>                                   | focus search                     |
| <kbd>PageUp</kbd>/<kbd>PageDown</kbd>               | scroll page up/down              |
| <kbd>Esc</kbd>                                      | back to previous board           |
| **Input** and **Search**                                                               |
| <kbd>Down</kbd>                                     | focus board                      |
| <kbd>Tab</kbd>                                      | focus board and keep focus       |
| **Input**                                                                              |
| key on board                                        | select and insert emoji          |
| <kbd>Enter</kbd>                                    | close and print result           |
| <kbd>Right</kbd> at end                             | focus search                     |
| **Search**                                                                             |
| <kbd>Enter</kbd>                                    | insert first match               |
| <kbd>Right</kbd> at end                             | select next match                |
| <kbd>Left</kbd> at start                            | focus input                      |
| **Board**                                                                              |
| key on board                                        | select and insert emoji          |
| <kbd>Space</kbd> + key on board                     | open variants                    |
| <kbd>Enter</kbd>                                    | insert emoji                     |
| <kbd>Up</kbd> in first row                          | focus input                      |
| **Recent Board** additional keys                                                       |
| <kbd>Shift-Left</kbd>/<kbd>Right</kbd>              | move selected left/right         |
| <kbd>Shift-Enter</kbd>                              | toggles favorite state           |
| <kbd>Space</kbd> + key on board                     | toggles favorite state           |
| <kbd>Shift-Delete</kbd>                             | delete selected                  |
| **Mouse** 🖱️                                                                           |
| <kbd>LeftClick</kbd>                                | insert emoji                     |
| <kbd>LeftClick</kbd> in upper right corner          | open variants                    |
| <kbd>DoubleLeftClick</kbd>                          | insert emoji and close           |
| <kbd>RightClick</kbd>                               | back to previous board           |
| <kbd>Wheel</kbd>                                    | scroll pages                     |

There are two ways to enter the board from the input or search field.
- With <kbd>Tab</kbd> focus will be kept on board when inserting emoji.
- With <kbd>Down</kbd> focus will return to input field when inserting emoji.

## ⟲ Recent List 

Used emojis will be put automatically to the recent list.

Items will be added without variants.

Every item has a score and items are sorted by score when opening the recent board.

A score >= 100 makes an item a favorite and it will not change anymore.

When an item is inserted into the input its score will increase by 10 and the score of all others - except favorites - decreases by 1.

## 🔎 Search 

When entering search without a pattern it will display all available emojis.

With a pattern it will show items matching by name or tag in the order of their score and select the first result.

Special patterns are:
- "#" prefix for tag search, e.g. "#heart"
- "," to separate group,subgroup search, e.g. ",heart"
- "+" prefix for hex code search

## 🛠️ Requirements

Install:

- Python 3.12+

Other requirements will be downloaded automatically.

For displaying emojis the [Noto Color Emoji](https://github.com/googlefonts/noto-emoji/tree/main/fonts) font is used - otherwise flags and some other newer emojis will not display correctly.

The emoji groups are built from:
[Emojibase](https://github.com/milesj/emojibase/raw/refs/heads/master/packages/data)
and
[UnicodeData](https://www.unicode.org/Public/UCD/latest/ucd/).

## 🔧 Building

```shell
python -m venv .venv
source .venv/Scripts/activate
pip install -e . # or: uv sync
python src/guikbd.py # for testing
python src/termkbd.py # for testing
```

## 🔨 Installation

Integration into your system works with one of the scripts in `scripts/*`.

### 💧 Linux Hyprland

Install:

- `nc` (netcat)
- `wl-copy`
- `wtype`
- `kitty`
- `noto-fonts-emoji`

In Arch by:

```shell
sudo pacman -S openbsd-netcat wl-clipboard wtype kitty noto-fonts-emoji
```

Add hotkey to `~/.config/hypr/bindings.conf`

```shell
unbind = SUPER, period
# bindd = SUPER, period, Emojis, exec, PATHTO/scripts/emoji-kbd-gui-wl
bindd = SUPER, period, Emojis, exec, PATHTO/scripts/emoji-kbd-kitty-hl-open
```

Add for fast opening (noanim) and floating window to `~/.config/hypr/hyprland.conf`

With hyprland <= 0.52:

```shell
windowrulev2 = tag -floating-window, title:^Emoji Kbd$
windowrulev2 = tag -terminal, title:^Emoji Kbd$
windowrulev2 = noanim, title:^Emoji Kbd$
windowrulev2 = float, title:^Emoji Kbd$
windowrulev2 = center, title:^Emoji Kbd$
windowrulev2 = unset size, title:^Emoji Kbd$
# you may also want to set/adjust the size
#windowrulev2 = size 600 285, title:^Emoji Kbd$
#windowrulev2 = minsize 500 200, title:^Emoji Kbd$
#windowrulev2 = maxsize 800 400, title:^Emoji Kbd$
```

With hyprland >= 0.53:

```shell
windowrule {
    name = Emoji Kbd
    match:title = ^(Emoji Kbd)$
    tag = -floating-window
    tag = -terminal
    no_anim = on
    float = on
    center = on
    max_size = 800 600
}
```

Optionally copy `res/emoji-kbd.desktop` to `~/.local/share/applications/`
for a launcher entry and adjust the paths in the copied file.

### 🪟 Windows

Install:

- [Autohotkey v2](https://autohotkey.com/)

If you have Noto Color Emoji font already installed, make sure it is the
[Windows compatible](https://github.com/googlefonts/noto-emoji/raw/refs/heads/main/fonts/NotoColorEmoji_WindowsCompatible.ttf) one - otherwise flags render very slowly.

First startup on windows might be slow due to downloading emoji databases and Noto font and you may get a warning that the daemon could not be started.
Just wait a bit longer or check the logs.

Run:

```cmd
scripts\emoji-kbd.ahk
```

It will overwrite <kbd>Win-.</kbd>, i.e. the Windows emoji picker.
If you prefer another hotkey edit the script.

### 📟 Terminal

Only kitty fully supports displaying all emojis (flags, ..) and without misalignment!

Start terminal version:

```shell
python src/termkbd.py
```

or the daemon like terminal - using a kitty terminal which is hidden/shown by hyprland:

```shell
./scripts/emoji-kbd-kitty-hl-open
```

or start the gui:

```shell
python src/guikbd.py
```

or start the gui via daemon for faster opening - use "GET" to wait for result or "SHOW" to just show gui:

```shell
python src/guidmn.py get
```

## ⚙️ Customization

Edit `~/.config/emoji-kbd/emoji-kbd.toml`

For everything else - change the code 😉 or wait until it is added.

## Other Files

- `~/.local/state/emoji-kbd/recent.txt` the recent list.
- `~/.local/state/emoji-kbd/*.log` the log files.
- `~/.cache/emoji-kbd/*` emoji databases and Noto font - delete these and start Emoji Kbd again to update to newer versions.

## Development

When the environment variable `EMOJI_KBD_DEV` is set to a value the config file is taken from 
`res/emoji-kbd.toml` and all other files go to `.local` in the repo. It can be set also to a 
comma separated list of words, currently only "no_cache", to disable use of cache.

## Alternatives

I started to use emojis with Windows 10 but disliked the new picker from Windows 11 as it had a much smaller recent list.

Looking for alternatives I found <https://github.com/gilleswaeber/emoji-keyboard> from Gilles Weber and added the recent emojis board and was very happy with it for years.

But when switching back to Linux for the desktop I could not find a proper alternative and thus made my own one - Emoji Kbd - inspired by emoji-keyboard.

I like Walker, but not the emoji picker.

## Todos

- Add more board layouts
- https://raw.githubusercontent.com/unicode-org/cldr/refs/heads/main/common/annotations/de.xml
- ...

## Licenses

- **Emoji Kbd**: [GPL-3.0-or-later](LICENSE)
- **Emojibase**: Copyright (c) Miles Johnson. License: [MIT License](https://github.com/milesj/emojibase/blob/master/packages/data/LICENSE).
- **UnicodeData**: Copyright © 1991-2026 Unicode, Inc. All rights reserved. Distributed under the [Unicode License Agreement](https://www.unicode.org/copyright.html).

