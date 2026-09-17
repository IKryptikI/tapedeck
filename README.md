# tapedeck

Pull a concert, DJ set or single track off the web and file it into your music
library — split into numbered tracks, tagged, with artwork, ready for Apple Music
or anything else that reads a folder of MP3s.

Runs on your own machine. Nothing is uploaded anywhere and there is no service in
the middle.

Built on [yt-dlp](https://github.com/yt-dlp/yt-dlp) for fetching and
[ffmpeg](https://ffmpeg.org/) for audio work.

## Where it can read from

yt-dlp supports around 1,750 sites, and tapedeck passes URLs straight through, so
anything it handles works here. Commonly:

**YouTube** · **SoundCloud** · **Vimeo** · **Dailymotion** · **Bandcamp** ·
**Mixcloud** · **Twitch** · **Internet Archive**

Worth knowing about the last one: the Internet Archive's
[Live Music Archive](https://archive.org/details/etree) holds tens of thousands of
live concert recordings that the artists have explicitly authorised for free
distribution. If you are after live shows, start there — it is the largest source
that is unambiguously yours to keep.

Chapter-based splitting needs the site to expose chapter markers, which in
practice means YouTube. Everywhere else, tapedeck detects track boundaries from
the audio itself.

## What this is for

tapedeck is a personal archiving tool. It is built for material you already have
a right to: your own uploads, artist-authorised downloads, Creative Commons and
public-domain works, and the taper-authorised recordings on the Live Music
Archive.

It does not circumvent DRM, and cannot — yt-dlp decodes nothing that is
encrypted. It has no sharing, hosting or upload features. Everything it produces
stays on the machine that ran it.

Downloading commercial catalogue generally conflicts with the terms of service of
the site it came from, whatever the copyright position where you live. That is
your call and your responsibility. This project does not condone redistributing
licensed material, and is not affiliated with any of the platforms it can read.

## Download

### Windows

**[Latest release](https://github.com/kw0175/tapedeck/releases/latest)** - grab
`tapedeck.exe`, double-click, done. One file, no installer.

Windows will show a SmartScreen warning the first time because the build is not
code-signed: **More info -> Run anyway**. Signing certificates cost money and
this is a free tool.

Two things are not bundled and must be installed once:

```powershell
winget install Gyan.FFmpeg      # converting and splitting audio
winget install DenoLand.Deno    # YouTube; without it downloads fail with 403
```

They stay external deliberately - together they are ~200 MB, and ffmpeg's
licensing would complicate this project's MIT terms. The app tells you if either
is missing rather than failing cryptically.

### Linux / macOS

No bundled binary yet - run from source. It's a few extra minutes, not a
different experience: see [Setup](#setup) below.

## Web UI

Paste a link, name a destination folder, press Download. The job runs in the
background: fetch best audio → split on chapters if the upload has them → convert
→ embed artwork. The destination folder is created if it doesn't exist.

```powershell
python server.py
python server.py --root "C:\Users\Public\AppleMusic" --port 8800
```

Then open <http://localhost:8800>.

Artist / Album / Year boxes override the upload's own tags. Worth filling in for
YouTube, where the "artist" is otherwise the channel name.

### Reaching it from anywhere (Cloudflare Worker + tunnel)

The Worker serves the page and forwards `/api/*` to your PC. It cannot do the work
itself — no Python, no ffmpeg, and no way to write to your music folder — so
`server.py` still has to be running at home.

Quick tunnels get a new hostname every restart, so the backend URL isn't baked in:
`tunnel.py` reads whatever hostname it was handed and POSTs it to the Worker's
`/_register`, which stores it in KV.

One-time setup:

```powershell
cd worker
wrangler kv namespace create STATE      # paste the id into wrangler.toml
wrangler secret put ADMIN_TOKEN         # any long random string
wrangler deploy
```

Then, at home, two windows:

```powershell
python server.py --root "C:\Users\<you>\Music" --token <SERVER_TOKEN>
python tunnel.py --worker https://<name>.workers.dev --admin-token <ADMIN_TOKEN>
```

Open the Worker URL from anywhere. Two separate secrets, deliberately: `ADMIN_TOKEN`
only lets a machine register itself, `SERVER_TOKEN` is what the page asks you for.

If the PC is off or the tunnel is down, the page returns a clear 503 rather than
failing silently.

### Exposing it

`server.py` binds to `127.0.0.1` and refuses to write outside `--root`. Both
matter if you put it behind a Cloudflare Tunnel or similar — an open endpoint that
downloads arbitrary URLs onto your machine is not something to leave unauthenticated.

```powershell
python server.py --host 0.0.0.0 --token "some-long-random-string" --root "C:\Users\Public\AppleMusic"
```

The page prompts for the token once and remembers it. Starting with `--host` set to
anything public and no `--token` prints a warning.

Note this runs on **your** machine, which matters: SoundCloud and YouTube block
datacenter IPs aggressively, so the same code on cloud hosting hits bot checks that
a home connection doesn't.

## Setup

Works the same way on Windows, macOS and Linux — Python, ffmpeg and Deno are
all cross-platform. Every script looks for its tools on `PATH` first
(`platform_tools.py`), so as long as they're installed the normal way for
your OS, nothing else needs configuring.

**1. Python packages**

A virtualenv keeps yt-dlp's dependencies out of your system Python:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

(Windows: `py -m venv .venv` then `.venv\Scripts\pip install -r requirements.txt`.)
Run scripts as `.venv/bin/python tapedeck.py ...` from then on, or activate the
venv (`source .venv/bin/activate`) and drop the prefix.

**2. ffmpeg** — required for anything except `--format best`.

| OS | Command |
|---|---|
| Windows | `winget install Gyan.FFmpeg` (reopen your terminal after) |
| macOS | `brew install ffmpeg` |
| Debian/Ubuntu | `sudo apt install ffmpeg` |
| Fedora | `sudo dnf install ffmpeg` |
| Arch | `sudo pacman -S ffmpeg` |

Verify with `ffmpeg -version`.

**3. Deno** — required for YouTube.

| OS | Command |
|---|---|
| Windows | `winget install DenoLand.Deno` |
| macOS | `brew install deno` |
| Linux | `curl -fsSL https://deno.land/install.sh \| sh` |

YouTube now requires executing JavaScript to solve the signature and "n"
challenges on its media URLs. Without a runtime, yt-dlp still lists formats
perfectly happily and then every download dies with **HTTP 403 Forbidden** — the
failure looks like a network or auth problem rather than a missing dependency.

tapedeck finds Deno automatically and passes `--js-runtimes` plus
`--remote-components ejs:github` (the solver script, which is an opt-in
download). If Deno is missing it says so in the job log instead of leaving you
guessing.

Other sites don't need it. This is a YouTube-specific requirement.

**Keep yt-dlp current.** Site extraction breaks regularly, and YouTube most of
all:

```bash
.venv/bin/pip install -U yt-dlp
```

### Linux: desktop app and auto-start

`app.py` (the windowed version) uses [pywebview](https://pywebview.flowrl.com/),
which on Linux needs a system WebKit binding — `pip install pywebview` alone
isn't enough:

```bash
sudo apt install python3-gi gir1.2-webkit2-4.1   # Debian/Ubuntu
sudo dnf install python3-gobject webkit2gtk4.1    # Fedora
.venv/bin/pip install pywebview
```

Without it, `app.py` falls back to opening your regular browser instead — still
fully functional, just not in its own window.

For a shortcut: `tapedeck.sh` launches the desktop app (`chmod +x` it first),
and `tapedeck.desktop` is a launcher you can drop in `~/.local/share/applications/`
after editing the two paths inside it to match where you cloned the repo.

To run the server (and optionally the tunnel) automatically at login — the
Linux equivalent of the Windows Scheduled Task setup below — use the systemd
user units in `systemd/`:

```bash
mkdir -p ~/.config/systemd/user
cp systemd/tapedeck-server.service systemd/tapedeck-tunnel.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now tapedeck-server.service
# only if you're using the Worker + tunnel setup below:
systemctl --user enable --now tapedeck-tunnel.service
```

Logs land in `~/.local/state/tapedeck/`. `loginctl enable-linger $USER` keeps
the units running after you log out (e.g. on a headless box).

### Getting downloads into Spotify or Apple Music on Linux

**Spotify: yes, via Local Files.** Point Spotify's desktop app at Tapedeck's
output folder (Settings → Local Files → add a source) and your downloads play
alongside the regular catalog. This is a client-side folder scan, not
something the Web API exposes — no API can add a local file to a Spotify
library, for anyone, on any platform. Tapedeck's tags/artwork are exactly what
that feature wants, so no extra integration work is needed here.

**Apple Music: not yet, and not through Sidra.** There is no official Apple
Music client for Linux, and [Sidra](https://github.com/wimpysworld/sidra) —
the Apple Music wrapper most people run instead — has no local-file support at
all; it only streams the catalog. [Cider](https://cidercollective.io) dropped
local-file support in its 2.x rewrite for the same reason. Nor is there an
API path: Apple's MusicKit can add *catalog* songs to a library, but has no
endpoint to upload arbitrary audio. Until Apple ships an official Linux
client (or a wrapper adds real local-library support), there is no
destination on this platform to send a download to — so for now, **Tapedeck's
Linux library integration is Spotify-only.** Downloads still work fine either
way; on the Apple Music side they just stay files in a folder rather than
landing inside any app.

## config.local.json

Both scripts read `config.local.json` from the repo folder, so tokens stay off
the command line and out of shell history. It is gitignored. Flags override it.

```json
{
  "root": "C:\Users\<you>\Music",
  "port": 8800,
  "token": "<what the page asks you for>",
  "worker": "https://<your-worker>.workers.dev",
  "adminToken": "<the Worker's ADMIN_TOKEN secret>",
  "wait": 300,
  "cookiesFromBrowser": "firefox",
  "discogsToken": "<optional, see below>"
}
```

| Key | Used by | What it does |
|---|---|---|
| `root` | server | Destination folders must live under this |
| `port` | both | Local server port (default 8800) |
| `token` | server | Required in an `X-Token` header |
| `worker` | tunnel | Worker base URL to register with |
| `adminToken` | tunnel | Lets a machine register itself |
| `wait` | tunnel | Seconds to wait for the server at logon |
| `cookiesFromBrowser` | server | Browser to borrow a logged-in session from |
| `discogsToken` | artwork | Free token; unlocks bootleg/live sleeve search |

### Artwork sources

Downloads look for a real release sleeve before falling back to the video
thumbnail. A thumbnail is a 16:9 frame - squaring it throws away a third of the
picture - so a genuine cover is always better when one exists.

Four catalogues are tried, best result by actual pixel size wins:

| Source | Needs a key | Good for |
|---|---|---|
| Discogs | free token | **bootlegs and unofficial live pressings** |
| iTunes | no | commercial releases, up to 1200px |
| Deezer | no | commercial releases, 1000px |
| Cover Art Archive | no | anything archived on MusicBrainz |

Results whose artist does not match are discarded - searching a bootleg's title
otherwise returns unrelated albums, and a confidently wrong cover is worse than
no cover.

**Discogs is the one that matters for live recordings.** Most shows were never
sold, so the commercial catalogues have nothing; Discogs lists unofficial
pressings. Get a token free at
<https://www.discogs.com/settings/developers> ("Generate new token") and put it
in `config.local.json` as `discogsToken`. Without it Discogs is skipped and the
message says so.

If nothing is found anywhere, the thumbnail is used - for a show that was never
pressed, that is the honest answer.

Output is square and capped at whatever the source actually provides. Apple
Music and Spotify both want >=1000px, but a smaller cover is left at its real
size rather than upscaled to claim a number it cannot back.

### cookiesFromBrowser

YouTube increasingly answers anonymous requests with **"Sign in to confirm
you're not a bot"**, which kills extraction outright. It is a different failure
from the 403 above and Deno does not help — the fix is lending yt-dlp your
browser's logged-in session.

Set it to `firefox`, `chrome`, `edge`, `brave`, `opera`, `vivaldi` or `safari`.
Off by default: reading a browser's cookie store is not something a tool should
do uninvited. Cookies are handed to yt-dlp locally and go nowhere else.

**Firefox is the easy one** on every platform — Chromium-based browsers (Chrome,
Edge, Brave, Vivaldi) lock their cookie database while running, so they have to
be closed first.

## Troubleshooting

| Symptom | Cause |
|---|---|
| `HTTP 403 Forbidden` on YouTube | Deno missing, or yt-dlp out of date |
| `Sign in to confirm you're not a bot` | Set `cookiesFromBrowser` (see above) |
| Page loads but every action 404s | The Worker was redeployed over — see the Worker section |
| Page returns 503 | `server.py` or `tunnel.py` isn't running |
| Page returns 530 | Tunnel is registered but your PC is unreachable |
| `file is locked` when embedding art | The player has the file open; pause it |
| Destination folder empties itself | Expected if it's a watched folder — the player imported them |

## Usage

```powershell
# one track -> ./downloads/Artist - Title.mp3
python tapedeck.py https://soundcloud.com/artist/track-name

# several at once, into a specific folder
python tapedeck.py URL1 URL2 URL3 -o "D:\Music"

# a whole set, numbered, in its own subfolder
python tapedeck.py https://soundcloud.com/artist/sets/my-set --playlist-folder

# a list of URLs from a file
python tapedeck.py --batch urls.txt

# skip anything already grabbed on a previous run
python tapedeck.py --batch urls.txt --archive done.txt

# keep the original file, no transcode (fastest, no quality loss)
python tapedeck.py --format best URL

# your own private/unlisted uploads (reads your logged-in browser session)
python tapedeck.py --cookies-from-browser chrome URL
```

### Options

| Flag | Default | What it does |
|---|---|---|
| `-o, --out` | `./downloads` | Output directory |
| `-f, --format` | `mp3` | `mp3`, `m4a`, `opus`, `flac`, `wav`, or `best` (no conversion) |
| `-q, --bitrate` | `320` | kbps for lossy formats |
| `-b, --batch` | — | Text file, one URL per line, `#` comments allowed |
| `--playlist-folder` | off | Sets go in their own numbered subfolder |
| `--template` | — | Raw yt-dlp output template override |
| `--archive` | — | File of already-downloaded ids; skipped on reruns |
| `--limit N` | — | Only the first N items of a set/profile |
| `--cookies-from-browser` | — | `chrome`, `firefox`, `edge`, `brave`, `opera`, `vivaldi`, `safari` |
| `--cookies` | — | Netscape `cookies.txt` instead of a live browser |
| `--no-cover` | off | Skip embedding artwork |
| `--no-metadata` | off | Skip writing title/artist tags |

Title, artist, and cover art are embedded into the file automatically unless you
opt out.

## Splitting a long recording

`split_tracks.py` cuts a concert, DJ set, or mixtape into individual tagged tracks.
It runs in two steps so you can correct the boundaries before committing.

```bash
# 1. find the boundaries -> writes an editable cuesheet
python split_tracks.py concert.m4a --detect --expect 12 --names tracklist.txt --artist "Oasis" --album "Live At Wolverhampton 1994" --date 1994 --cue-out cue.txt

# 2. check/adjust the times in cue.txt, then cut
python split_tracks.py concert.m4a --cue cue.txt -o tracks
```

`--names` takes a plain text file of song titles, one per line, in playing order.

### Use chapters when they exist

If the upload has chapter markers — or timestamps in the description that YouTube
parsed into chapters — those boundaries are exact. Always prefer them:

```bash
python split_tracks.py concert.webm --detect --from-chapters "https://youtu.be/VIDEOID" --artist "Oasis" --album "MTV Unplugged 1996" --date 1996 --cue-out cue.txt
```

Titles come from the chapters too, so no `--names` file is needed. Everything below
is only for recordings with no chapters.

### Detection methods

`--method auto` (the default) tries these in order:

| Method | How it works | Best for |
|---|---|---|
| `gaps` | Finds the short digital silences that joined uploads use as separators, and **trims them out** so no dead air survives into a track | Uploads assembled from separate song files — very common, and exact when it applies |
| `envelope` | Builds a per-second loudness envelope and ranks *relative* dips by prominence | True live recordings, where constant crowd noise defeats silence detection |
| `silence` | Absolute silence threshold | Clean studio compilations |

Segments shorter than `--min-track` (default 45s) are discarded, which drops spoken
intros and closing applause instead of turning them into tracks.

### Split options

| Flag | Default | What it does |
|---|---|---|
| `--detect` | — | Find boundaries and write a cuesheet |
| `--cue FILE` | — | Cuesheet to split with |
| `--names FILE` | — | Track titles, one per line |
| `--expect N` | — | How many tracks to expect |
| `--method` | `auto` | `auto`, `gaps`, `envelope`, `silence` |
| `--min-track` | `45` | Segments shorter than this aren't songs |
| `--gap-noise` | `-50` | dB threshold for a separator |
| `--gap-min` | `0.6` | Minimum separator length, seconds |
| `--fade MS` | `24` | Fade in/out at each cut; kills clicks (forces re-encode) |
| `-f, --format` | `copy` | `copy`, `mp3`, `m4a`, `flac`, `wav`, `opus` |
| `--dry-run` | off | Show the cuts, write nothing |

### Cuesheet format

```
ALBUM:  Live At Wolverhampton Civic Hall
ARTIST: Oasis
DATE:   1994

0:44 - 5:22.18    Rock 'n' Roll Star     <- explicit end: gap trimmed out
5:24.16           Columbia               <- no end: runs to the next start
```

### About `--fade` and quality

Concatenated uploads often have a click exactly where one song was joined to the
next, and a cut lands right on it — you hear a blip before the music starts. A few
milliseconds of fade removes it.

Fading needs a filter, and filters need decoded audio, so **any fade forces a
re-encode**. Two ways to avoid a second generation of lossy compression:

- `--format flac` — lossless, so the re-encode costs nothing in quality (bigger files)
- `--fade 0` — true lossless stream copy, but you keep the clicks

The default (`--fade 24` into the source format at 256kbps) is a middle ground:
audibly transparent from a 128–160kbps SoundCloud source, and small.

## Album artwork

```powershell
python add_art.py cover.jpg -d "Artist - Album"
python add_art.py --from-track https://soundcloud.com/user/track -d "Artist - Album"
```

`--from-track` pulls the artwork straight off the SoundCloud page. Non-square images
are centre-cropped to the largest square they contain, then scaled to `--size`
(default 500). Audio is stream-copied, so embedding costs nothing in quality. A
folder-level `cover.jpg` is written too, since many players prefer that over tags.

## Converting formats

```powershell
python convert_folder.py -d "Artist - Album" --format alac
python convert_folder.py -d "Artist - Album" --format mp3 -q 320 -o "somewhere else"
```

| Target | Type | Notes |
|---|---|---|
| `alac` | lossless | Apple Lossless in `.m4a` |
| `flac` | lossless | |
| `wav` | lossless | uncompressed; no tag support |
| `m4a` | lossy | AAC |
| `mp3` | lossy | most universally supported |

Tags and embedded art carry across. The script reports whether a conversion
preserves audio exactly, and warns on lossy → lossy, which stacks artefacts.

### Getting a bootleg into Apple Music on Windows

Verified the hard way, on Apple Music for Windows 1.1540:

- **FLAC does not work.** Apple has never supported it in iTunes or Apple Music.
- **ALAC did not work either**, despite being Apple's own lossless codec. The app
  silently refused ffmpeg-written `.m4a` files — no error, no import.
- **MP3 works.** `--format mp3 -q 320` is the reliable route.

The app's local-file import is buggy in general: many users report `Import`
missing from the sidebar's `⋯` menu and drag-and-drop failing without any error.
If it fights you, MusicBee or foobar2000 read the original FLAC folders directly,
artwork and tags included, with no conversion at all.

**On quality:** SoundCloud serves 96–160kbps, so that is the ceiling regardless of
what you convert to. MP3 320 gives the encoder far more headroom than the source
ever used, making the loss effectively inaudible. Keep FLAC as the archival copy
and use MP3 for playback.

## Notes

- **`--format best` vs `mp3`:** SoundCloud serves most streams as ~128kbps
  Opus/AAC. Transcoding that to 320kbps MP3 does not add quality — it just makes a
  bigger file that plays everywhere. Use `best` if your player handles Opus.
- **Failures on a big set** don't stop the run; anything that failed is listed at
  the end.
- **Common failure causes:** track is Go+ only, private, deleted, or geo-blocked.
- **Keep yt-dlp current** — SoundCloud changes their API periodically and yt-dlp
  ships fixes fast:
  ```powershell
  pip install -U yt-dlp
  ```
