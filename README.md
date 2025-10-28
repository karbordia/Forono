# Forono - Shortcut Maker for Linux

**Forono** is a lightweight GUI application that lets you quickly create application shortcuts on Linux. With a few clicks, you can generate `.desktop` files for local or system-wide use, including custom icons, arguments, and categories.

## Features

- Create application shortcuts easily for any executable or script.
- Option to run applications in a terminal.
- Add custom icons and comments (tooltips).
- Choose shortcut location: local (`~/.local/share/applications`) or system-wide (`/usr/share/applications`).
- Generates `.desktop` files compatible with standard Linux desktop environments.

## Installation

1. Download the latest `.deb` package from the [Releases](#) page.
2. Install using:

```bash
sudo dpkg -i forono.deb
```

Launch Forono from your application menu or terminal:

```
forono
```


![ScreenShot](https://raw.githubusercontent.com/karbordia/Forono/refs/heads/main/images/screenshot.png)