#!/usr/bin/env python3
"""
platform_tools.py - cross-platform bits shared by every entry point: locating
ffmpeg/deno/cloudflared, the config file's base directory, and the "not
found" install hints.

Previously each script (tapedeck.py, server.py, add_art.py, refresh_art.py,
convert_folder.py, split_tracks.py, tunnel.py) carried its own copy of this
logic, written Windows-first. Centralising it here means a platform fix - or
a new platform - only has to happen once.
"""

import os
import shutil
import sys
from pathlib import Path

WINDOWS = sys.platform == "win32"
MACOS = sys.platform == "darwin"


def find_exe(name):
    """Locate an executable on PATH, falling back to the WinGet (ffmpeg)
    install location on Windows.

    winget adds ffmpeg to PATH, but shells opened before the install don't see
    it until they're restarted; this fallback covers that gap. Package
    managers on Linux/macOS put things on PATH immediately, so shutil.which
    alone is enough there.
    """
    exe = shutil.which(name)
    if exe:
        return exe
    if WINDOWS:
        local = os.environ.get("LOCALAPPDATA")
        if local:
            hits = sorted(Path(local).glob(
                f"Microsoft/WinGet/Packages/Gyan.FFmpeg*/**/bin/{name}.exe"))
            if hits:
                return str(hits[-1])
    return None


def find_deno():
    """Locate deno, which YouTube extraction needs to solve the signature and
    "n" challenges. Without it yt-dlp still lists formats, but the media URLs
    it hands back 403 - the failure looks like a download problem rather than
    a missing dependency.
    """
    exe = shutil.which("deno")
    if exe:
        return exe
    if WINDOWS:
        local = os.environ.get("LOCALAPPDATA")
        if local:
            for pat in ("Microsoft/WinGet/Packages/DenoLand.Deno*/**/deno.exe",
                        "../../.deno/bin/deno.exe"):
                hits = sorted(Path(local).glob(pat))
                if hits:
                    return str(hits[-1])
        home = Path.home() / ".deno" / "bin" / "deno.exe"
    else:
        # The official install script (curl -fsSL https://deno.land/install.sh
        # | sh) puts the binary here and appends it to PATH in the shell rc -
        # but a shell opened before that edit won't see it yet, same race as
        # the Windows case above.
        home = Path.home() / ".deno" / "bin" / "deno"
    return str(home) if home.exists() else None


def find_cloudflared():
    exe = shutil.which("cloudflared")
    if exe:
        return exe
    if WINDOWS:
        for pat in (r"C:\Program Files (x86)\cloudflared\cloudflared.exe",
                    r"C:\Program Files\cloudflared\cloudflared.exe"):
            if Path(pat).exists():
                return pat
        local = os.environ.get("LOCALAPPDATA")
        if local:
            hits = sorted(Path(local).glob(
                "Microsoft/WinGet/Packages/Cloudflare.cloudflared*/**/cloudflared.exe"))
            if hits:
                return str(hits[-1])
    else:
        for p in ("/usr/local/bin/cloudflared", "/opt/homebrew/bin/cloudflared",
                   str(Path.home() / ".local/bin/cloudflared")):
            if Path(p).exists():
                return p
    return None


def config_base_dir():
    """Base directory for tapedeck/config.json, per platform convention.

    Windows: %LOCALAPPDATA%. Linux/macOS: $XDG_CONFIG_HOME, defaulting to
    ~/.config per the XDG base-directory spec (most tools, including several
    on macOS, honour this even though Apple's own convention is
    ~/Library/Application Support).
    """
    if WINDOWS:
        return os.environ.get("LOCALAPPDATA")
    return os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")


def install_hint(display_name, *, winget=None, brew=None, apt=None):
    """A three-line 'how to install this' block, one line per platform.

    Falls back to a generic message for a platform with no package given
    (e.g. cloudflared has no apt package upstream).
    """
    lines = [f"{display_name} not found on PATH."]
    lines.append("  Windows:  " + (f"winget install {winget}" if winget
                                    else "see the project's install docs"))
    lines.append("  macOS:    " + (f"brew install {brew}" if brew
                                    else "see the project's install docs"))
    lines.append("  Linux:    " + (f"sudo apt install {apt}" if apt
                                    else "see the project's install docs"))
    return "\n".join(lines)
