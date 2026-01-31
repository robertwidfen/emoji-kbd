# Emoji Kbd <img src="res/emoji-kbd.svg" alt="Emoji Kbd" width="32" style="vertical-align: bottom; padding-bottom: 4px"/>

![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![License](https://img.shields.io/badge/license-GPL--3.0--or--later-green)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows-lightgrey)

Fast and efficient emoji picker with keyboard-driven navigation. Available as GUI and TUI.

## 🚀 Features

- Packed with 3940 emojis 🤩 including 2030 variants (skin tones, gender, …) and 5249 symbols Α-Ω in 35 groups ⯒.
- Fast keyboard ⌨️ and mouse 🖱️ navigation.
- Combined favorites ⭐️ and recent ⟲ list.
- Powerful search 🔎.
- Grouping of people emojis differing just by gender 🎅🤶🧑‍🎄.
- TUI/Terminal 📟️ version available.
- Localization 🏳️‍🌈 where available.
- Customizable keyboard layouts (US, DE, Bone Corne, …).
- Cross-platform: Linux (Wayland/Hyprland), Windows, …

## 🖼️ Screenshots

**GUI:**

<video src="https://github.com/user-attachments/assets/93a74a6d-8692-4574-b4c1-11c6136bea9f" width="500" alt="GUI Demo" controls></video>

**TUI:**

<video src="https://github.com/user-attachments/assets/48af346a-b527-45f0-903d-0144b973e36c" width="500" alt="Terminal Demo" controls></video>

## 🎯 Why Choose Emoji Kbd?

**Speed and efficiency.** Get any favorite emoji in just 3 keystrokes:

1. <kbd>Win-.</kbd> — Open Emoji Kbd
2. <kbd>key</kbd> — Select emoji (each emoji has a keyboard key assigned)
3. <kbd>Enter</kbd> — Insert and close

No mouse needed. No scrolling through categories. Just fast keyboard navigation.

## 📦 Quick Start

```bash
# Clone and setup
git clone https://github.com/robertwidfen/emoji-kbd
cd emoji-kbd
python -m venv .venv
source .venv/bin/activate
pip install -e . # or uv sync

# Test run
python src/guikbd.py
```

**Linux (Arch/Hyprland):**
```bash
# Install dependencies
sudo pacman -S python openbsd-netcat wl-clipboard wtype kitty noto-fonts-emoji
```

Add key binding to `~/.config/hypr/bindings.conf`:
```
bindd = SUPER, period, Emojis, exec, /PATH_TO/scripts/emoji-kbd-gui-wl
#bindd = SUPER, period, Emojis, exec, /PATH_TO/scripts/emoji-kbd-kitty-hl-open
```

**Windows (11):**

Run with AutoHotkey (overrides <kbd>Win-.</kbd>)
```cmd
scripts\emoji-kbd.ahk
```

See [Installation](#-installation) for detailed platform-specific setup.

## 👆 UI

Top left is the emoji input field and on the right the search field.

In the middle is a (key)board like overview of emoji groups resp. emojis.
Each one has a <kbd>key</kbd> associated with it that opens the group or inserts the emoji into the input field.

At the bottom is a status field showing information about the currently selected emoji.

<kbd>Enter</kbd> in the input field will copy the content of the input field to the clipboard and and inserts it into your app.

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
| **> Input** and **🔎 Search**                                                          |
| <kbd>Down</kbd>                                     | focus board                      |
| <kbd>Tab</kbd>                                      | focus board and keep focus       |
| **> Input**                                                                            |
| key on board                                        | select and insert emoji          |
| <kbd>Enter</kbd>                                    | close and insert/print result    |
| <kbd>Right</kbd> at end                             | focus search                     |
| **🔎 Search**                                                                          |
| <kbd>Enter</kbd>                                    | insert first match               |
| <kbd>Right</kbd> at end                             | select next match                |
| <kbd>Left</kbd> at start                            | focus input                      |
| **⌨️ Board**                                                                           |
| key on board                                        | select and insert emoji          |
| <kbd>Space</kbd> + key on board                     | open variants                    |
| <kbd>Enter</kbd>                                    | insert selected emoji            |
| <kbd>Up</kbd> in first row                          | focus input                      |
| **⟲ Recent Board** additional keys                                                     |
| <kbd>Shift-Left</kbd>/<kbd>Right</kbd>              | move selected left/right         |
| <kbd>Shift-Enter</kbd>                              | toggles favorite state           |
| <kbd>Space</kbd> + key on board                     | toggles favorite state           |
| <kbd>Shift-Delete</kbd>                             | delete selected                  |
| **🖱️ Mouse**                                                                           |
| <kbd>LeftClick</kbd>                                | insert emoji                     |
| <kbd>LeftClick</kbd> in upper right corner          | open variants                    |
| <kbd>DoubleLeftClick</kbd>                          | insert emoji and close           |
| <kbd>RightClick</kbd>                               | back to previous board           |
| <kbd>Wheel</kbd>                                    | scroll pages                     |

## ⟲ Recent List 

Inserted emojis will be put to the recent list.


Every item has a score and items are sorted by score when new ones are added.

A score ≥ 100 makes an item a favorite and it will not change its score or position anymore.

When an item is inserted into the input its score will increase by 10 and the score of all others - except favorites - decreases by 1.

## 🔎 Search 

Enter the search field and type to filter emojis. 
Results are sorted by relevance score.
Search terms are separated by space.

Empty search displays all available emojis.

**Search patterns:**

| Pattern           | Example          | Matches             |
|-------------------|------------------|---------------------|
| Plain text        | `heart`          | ♥️💟😻💗🫀💓💔😍…  |
| `#tag`            | `#love`          | 🤟😘🏩🥰😍😗😙😻…  |
| `group,subgroup`  | `smileys,tongue` | 😋😛😜🤪😝🤑       |
| `,subgroup`       | `,mammal`        | 🐵🐒🦍🦧🐶🐕️…      |
| `+hexcode`        | `+221e`          | ∞                  |


## 🛠️ Requirements

**Core:**
- Python 3.12+
- [Noto Color Emoji](https://github.com/googlefonts/noto-emoji) font (auto-downloaded on first run)

**Platform-specific:**

| Platform             | Dependencies                                          |
|----------------------|-------------------------------------------------------|
| **Linux (Hyprland)** | `nc`, `wl-copy`, `wtype`, `kitty`, `noto-fonts-emoji` |
| **Windows**          | [AutoHotkey v2](https://autohotkey.com/)              |

Required Python packages are installed automatically with `pip install -e .`

**Data sources which will be automatically downloaded:**
- Emoji data: [Emojibase](https://github.com/milesj/emojibase) (MIT License)
- Unicode data: [UnicodeData](https://www.unicode.org/Public/UCD/latest/ucd/) (Unicode License)

## 🔨 Installation

Choose your platform and follow the integration steps:

### 💧 Linux (Hyprland)

Install dependencies - in Arch by:

```shell
sudo pacman -S openbsd-netcat wl-clipboard wtype kitty noto-fonts-emoji
```

Add hotkey to `~/.config/hypr/bindings.conf`:

```conf
unbind = SUPER, period

# Option 1: TUI if you have kitty installed
bindd = SUPER, period, Emojis, exec, /PATH_TO/scripts/emoji-kbd-kitty-hl-open

# Option 2: GUI
# bindd = SUPER, period, Emojis, exec, /PATH_TO/scripts/emoji-kbd-gui-wl
```

Add window rules for fast opening (noanim) and floating window to `~/.config/hypr/hyprland.conf`:

**Hyprland ≥ 0.53:**
```conf
windowrule {
    name = Emoji Kbd
    match:title = ^(Emoji Kbd)$
    tag = -floating-window
    tag = -terminal
    no_anim = on
    float = on
    center = on
    max_size = 800 600
    min_size = 500 200
}
```

**Hyprland ≤ 0.52:**
```conf
windowrulev2 = tag -floating-window, title:^Emoji Kbd$
windowrulev2 = tag -terminal, title:^Emoji Kbd$
windowrulev2 = noanim, title:^Emoji Kbd$
windowrulev2 = float, title:^Emoji Kbd$
windowrulev2 = center, title:^Emoji Kbd$
windowrulev2 = unset size, title:^Emoji Kbd$
windowrulev2 = size 600 285, title:^Emoji Kbd$
```

Optionally copy `res/emoji-kbd.desktop` to `~/.local/share/applications/`
for a launcher entry and adjust the paths in the copied file.

### 🪟 Windows

**Setup:**

1. Install [AutoHotkey v2](https://autohotkey.com/)
2. *(Optional)* Install [Windows-compatible Noto Color Emoji](https://github.com/googlefonts/noto-emoji/raw/refs/heads/main/fonts/NotoColorEmoji_WindowsCompatible.ttf) font
   - If you already have Noto Color Emoji, replace it with the Windows-compatible version to avoid slow flag rendering
3. Run `scripts\emoji-kbd.ahk` (double-click or add to startup)

**Default hotkey:** <kbd>Win-.</kbd> (overrides Windows emoji picker)

To change the hotkey, edit `scripts/emoji-kbd.ahk` and modify the `#.::` line.

> **First startup note:** Initial launch downloads emoji databases and Noto font. You might see a daemon startup warning. Check logs if issues persist.

### 📟 Terminal

**Terminal compatibility:**

| Terminal      | Emoji Support | Notes                                          |
|---------------|---------------|------------------------------------------------|
| **Kitty**     | ✅ Full       | Perfect rendering, all flags and graphemes     |
| **Ghostty**   | ⚠️ Mostly     | Minor rendering issues                         |
| **Alacritty** | ❌ Limited    | Misaligned columns, monochrome emojis          |
| **Others**    | ❓            | Font configuration needed for Noto Color Emoji |

## ⚙️ Customization

Copy `res/emoji-kbd.toml` or parts to `~/.config/emoji-kbd/emoji-kbd.toml` and edit:

**Change locale:**
```toml
[board]
locale = "de"  # Options: "en", "de", or any supported locale
layout = "de"  # Options: "us", "de", "bone-corne"
```

**Customize keyboard layouts:**
```toml
[[layout]]
…
```

See `res/emoji-kbd.toml` for all available options.

For everything else - change the code 😉

## 🔍 Troubleshooting

**Issue: Emojis not displaying, monochrome, flags show as 🇦 🇧 🇨, …**
- **Cause:** Missing or old Noto Color Emoji font.
- **Fix Linux:** `sudo pacman -S noto-fonts-emoji` (Arch) or equivalent.
- **Fix Windows:** Download [Windows-compatible Noto Color Emoji](https://github.com/googlefonts/noto-emoji/raw/refs/heads/main/fonts/NotoColorEmoji_WindowsCompatible.ttf).
- **Fix Terminal:** Configure font fallback (fontconf, …) to use Noto font.

**Issue: TUI misalignment**
- **Cause:** Terminal doesn't handle complex graphemes.
- **Fix:** Use Kitty terminal (recommended) or switch to GUI.

**Issue: Slow first startup**
- **Expected:** First run downloads ~5 MB of emoji data and Noto font on Windows. May cause startup warning on Windows.
- **Fix:** Wait 30-60 seconds for downloads to complete. 
- **Subsequent runs:** Uses cache (~ms startup).

**Issue: <kbd>Win-.</kbd> not working (Windows)**
- **Check:** AutoHotkey script is running (`scripts\emoji-kbd.ahk`)
- **Check:** No other app is overriding <kbd>Win-.</kbd>

**Emojis from news Unicode standard are missing**
- **Clear cache to update emojis:** From the ⚙️ menu select ♻️ and restart.
- **Update Noto font.**

## 📁 File Locations

| Path                                  | Purpose                            |
|---------------------------------------|------------------------------------|
| `~/.config/emoji-kbd/emoji-kbd.toml`  | User configuration                 |
| `~/.local/state/emoji-kbd/recent.txt` | Recent/favorite emojis list        |
| `~/.local/state/emoji-kbd/*.log`      | Log files                          |
| `~/.cache/emoji-kbd/*`                | Emoji databases, caches, Noto font |

## Development

When the environment variable `EMOJI_KBD_DEV` is set to a value the config file is taken from 
`res/emoji-kbd.toml` and all other files go to `.local` in the repo. It can be set also to a 
comma separated list of words, currently only "no_cache", to disable use of cache.

**Run terminal version for testing:**
```bash
python src/termkbd.py
```

**Run kitty helper script:**
```bash
./scripts/emoji-kbd-kitty-hl-open
```

**GUI daemon:**
Daemon mode keeps the app loaded in memory for instant opening.
Communicates by socket. If not reachable starts a new daemon.
```bash
python src/guidmn.py get    # Wait for result
python src/guidmn.py show   # Show only
```

**Check emoji grouping:**
```bash
python src/emojis.py
```

**Check and query config:**
```bash
python src/config.py
python src/config.py board.layout
```

## 🔄 Comparison with Alternatives

| Feature                 | Emoji Kbd      | Others             |
|-------------------------|----------------|--------------------|
| **Keyboard first**      | ✅             | ❌                 |
| **Favorites** ⭐        | ✅             | ❌                 |
| **Advanced Grouping** ⯒ | ✅             | ❌                 |
| **Advanced Search** 🔎  | ✅             | ❌ Often just name |
| **Cross Platform**      | ✅             | ❌ Often just one  |

**Why Emoji Kbd?**
- **Keyboard-first** design - navigate fast without mouse
- **Favorites** for fast access by muscle memory
- **Large recent list** with smart scoring
- **Advanced search** by name, tags, (sub)groups, code
- **Gender variant grouping** (🎅🤶🧑‍🎄)
- **See meta data** code, name, group, subgroup, tags
- **Cross-platform** Linux + Windows + …

**Origin story:** I disliked the new picker from Windows 11 as it had a much smaller recent list than the Windows 10 version.
Looking for alternatives I found <https://github.com/gilleswaeber/emoji-keyboard> from Gilles Weber and added the recent emojis board and was very happy with it for years.

But when switching back to Linux for the desktop I could not find a proper alternative and thus made my own one - Emoji Kbd - inspired by emoji-keyboard.

## 🚧 Roadmap

Kaomoji and GIFs will never be added. 😉

## Licenses

- **Emoji Kbd**: [GPL-3.0-or-later](LICENSE)
- **Emojibase**: Copyright (c) Miles Johnson. License: [MIT License](https://github.com/milesj/emojibase/blob/master/packages/data/LICENSE).
- **UnicodeData**: Copyright © 1991-2026 Unicode, Inc. All rights reserved. Distributed under the [Unicode License Agreement](https://www.unicode.org/copyright.html).
