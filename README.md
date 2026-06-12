# Brawl Stars v26.184 — Local Server Emulator

A personal-use Python server emulator for **Brawl Stars version 26.184**,
designed to run on your own machine and connect to a patched Android client.

> ⚠️ **For personal, offline, educational use only.**  
> This project is not affiliated with Supercell in any way.  
> Do not use against the official Supercell servers.

---

## What you get

| Feature | Details |
|---|---|
| TCP game server | Port **9339**, same as the official game |
| Player storage | MongoDB — your account persists across sessions |
| All brawlers unlocked | Every brawler at power level 9, for free |
| Unlimited resources | 9 999 gems · 99 999 gold by default |
| Editable events | Change which maps are active via `data/events/events.json` |
| Editable shop | Add / remove offers via `data/shop/shop.json` |
| Admin CLI tool | Give gems, rename players, list accounts |
| IP patcher tool | One command to update the APK config to your IP |

---

## Requirements

| Requirement | Minimum |
|---|---|
| Python | **3.9 or newer** |
| MongoDB | **5.0 or newer** (local or Atlas) |
| OS | Windows 10 / macOS 12 / Ubuntu 20.04 |
| Android | A patched Classic Brawl APK (v26.184) |

---

## Step 1 — Install Python

### Windows
1. Go to https://www.python.org/downloads/ and download **Python 3.11** (or newer).
2. During installation tick **"Add Python to PATH"**.
3. Click *Install Now*.

### macOS
```bash
# Install Homebrew first if you don't have it:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install python@3.11
```

### Linux (Ubuntu / Debian)
```bash
sudo apt update && sudo apt install python3 python3-pip -y
```

---

## Step 2 — Install MongoDB

You only need **one** of the options below.

### Option A — MongoDB Atlas (Cloud, easiest — no install)
1. Go to https://www.mongodb.com/cloud/atlas/register and create a **free** account.
2. Create a **Free Tier (M0)** cluster.
3. Under *Database Access* create a user with *Read and Write* permissions.
4. Under *Network Access* click **+ Add IP Address → Allow Access from Anywhere**.
5. Click **Connect → Drivers → Python** and copy the connection string.
   It looks like: `mongodb+srv://youruser:yourpassword@cluster0.xxxxx.mongodb.net`
6. Open `config.json` and paste it as the value of `"uri"`.

### Option B — MongoDB on your own computer
1. Go to https://www.mongodb.com/try/download/community and download the **Community Server**.
2. Run the installer (keep all defaults).
3. MongoDB will now start automatically with Windows / macOS.
4. The default `config.json` already points to `mongodb://localhost:27017` — nothing to change.

**Linux:**
```bash
# Ubuntu 22.04
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update && sudo apt install -y mongodb-org
sudo systemctl start mongod && sudo systemctl enable mongod
```

---

## Step 3 — Download and configure the server

```bash
# Clone or download the zip and extract it, then:
cd brawl-server

# Install Python dependencies (automatic on first run, but you can do it manually):
pip install -r requirements.txt
```

Edit **`config.json`** if needed:

```json
{
  "server"  : { "host": "0.0.0.0", "port": 9339 },
  "mongodb" : { "uri": "mongodb://localhost:27017", "database": "brawlserver" },
  "log_level": "INFO"
}
```

The only thing most people need to change is `mongodb.uri` if using Atlas.

---

## Step 4 — Run the server

```bash
python main.py
```

You will see something like this:

```
  ╔══════════════════════════════════════════════════════╗
  ║    ██████╗ ███████╗   Brawl Stars                    ║
  ║    ██╔══██╗██╔════╝   v26.184 Server Emulator        ║
  ╚══════════════════════════════════════════════════════╝

  ✔ MongoDB connected
  ✔ Events  : 5 loaded
  ✔ Shop    : 5 offers loaded
  ✔ Brawlers: 26 loaded

  ══════════════════════════════════════════════════════
  SERVER IS UP AND RUNNING!
  ══════════════════════════════════════════════════════
    Local  (same device):  127.0.0.1:9339
    Network (Android/PC):  192.168.1.42:9339
  ══════════════════════════════════════════════════════
```

Leave this window open — the server must stay running while you play.

---

## Step 5 — Patch and connect the Android client

### Get the patched APK

The Classic Brawl community maintains a pre-patched APK (Frida-gadget embedded)
for v26.184. Search for **"Classic Brawl v26.184 patched APK"** in the  
[Classic-Brawl GitHub issues](https://github.com/PhoenixFire6934/Classic-Brawl/issues)  
or community Discord.

The APK contains a file at:
```
lib/armeabi-v7a/libcb.config.so
```
This is actually a JSON file (despite the `.so` name) that tells Frida  
which server IP to connect to.

---

### Patch the IP with the helper tool

**Option A — Automatic (recommended)**

First extract `libcb.config.so` from the APK (use  
[apktool](https://apktool.org/) or just open the APK as a ZIP with 7-Zip/WinRAR).

Then run:

```bash
# Replace IP automatically (uses your LAN IP):
python tools/patch_apk_ip.py  path/to/libcb.config.so

# Or specify IP manually (e.g. for running server on another machine):
python tools/patch_apk_ip.py  path/to/libcb.config.so  192.168.1.42

# For same-device testing (server and game on same Android / emulator):
python tools/patch_apk_ip.py  path/to/libcb.config.so  127.0.0.1
```

The tool edits the JSON and saves a `.bak` backup of the original.

**Option B — Manual**

Open `libcb.config.so` in any text editor (Notepad, VS Code, etc.).  
Find `"redirectHost"` and change the value to your server's IP:

```json
{
  "interaction": {
    "interaction": {
      "type"      : "script",
      "path"      : "libscript.so",
      "on_change" : "reload",
      "parameters": {
        "redirectHost": "192.168.1.42",
        "relocate"    : true
      }
    }
  }
}
```

---

### Rebuild and install the APK

After patching `libcb.config.so`, put it back into the APK:

```bash
# 1. Decompile the APK
apktool d ClassicBrawl.apk -o ClassicBrawl_patched

# 2. Replace the config file
cp libcb.config.so ClassicBrawl_patched/lib/armeabi-v7a/libcb.config.so

# 3. Rebuild
apktool b ClassicBrawl_patched -o ClassicBrawl_patched.apk

# 4. Sign the APK (download uber-apk-signer from GitHub)
java -jar uber-apk-signer.jar --apks ClassicBrawl_patched.apk
```

Then install:
```bash
# Via ADB (Android Debug Bridge):
adb install ClassicBrawl_patched-aligned-debugSigned.apk

# Or just copy the APK to your phone and tap to install
# (Enable "Install from unknown sources" in Android Settings → Security)
```

---

### Connect

1. Start `python main.py` on your computer.
2. Make sure your Android device is on the **same Wi-Fi** as your computer.
3. Launch the patched Brawl Stars APK.
4. The game will connect to your server automatically.
5. You should see `[+] Client connected` in the server console.

---

## Customising the game

### Change active events
Edit **`data/events/events.json`** — no restart needed if you reload by stopping and restarting the server.

| Field | Meaning |
|---|---|
| `mode_id` | 3 = Gem Grab, 4 = Bounty, 5 = Brawl Ball, 6 = Showdown, 7 = Heist |
| `map_id` | Any map ID — the client renders the map |
| `map_name` | Displayed name in the event tab |

### Change shop offers
Edit **`data/shop/shop.json`**. Change `cost_gems` and `cost_gold` to 0 to make items free.

### Admin tools

```bash
# List all players
python tools/admin.py list

# Show a player (replace ID with the real one from the list)
python tools/admin.py show  12345678901

# Give 9999 gems
python tools/admin.py gems  12345678901  9999

# Give 99999 gold
python tools/admin.py gold  12345678901  99999

# Rename
python tools/admin.py name  12345678901  MyName

# Reset to fresh defaults
python tools/admin.py reset 12345678901
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `[FATAL] Cannot connect to MongoDB` | Make sure MongoDB is running. On Windows: open Services and start *MongoDB Server*. |
| Game shows "Connecting…" forever | Check your firewall allows port 9339. On Windows: *Windows Defender Firewall → Allow an app → add Python*. |
| Game connects but crashes | Make sure you're using the correct patched APK for v26.184. |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again. |
| Can't install APK | Enable *Install from unknown sources* in your Android settings. |
| Server IP not reachable from phone | Use the LAN IP shown at startup (e.g. `192.168.x.x`), not `127.0.0.1`. |

---

## Project structure

```
brawl-server/
├── main.py                  ← Entry point — run this
├── server.py                ← TCP server + session manager
├── config.json              ← Your settings (edit this)
├── requirements.txt
│
├── protocol/
│   ├── messages.py          ← Message ID constants
│   └── packet.py            ← Packet encode / decode
│
├── handlers/
│   ├── login.py             ← Handshake + login
│   ├── home.py              ← Home screen data
│   ├── battle.py            ← Battle matchmaking + results
│   └── chat.py              ← Club chat
│
├── models/
│   └── player.py            ← Player DB schema + helpers
│
├── utils/
│   ├── config.py            ← Config loader
│   ├── logger.py            ← Coloured console output
│   ├── db.py                ← MongoDB connection
│   └── loader.py            ← Game data file loader
│
├── data/
│   ├── events/events.json   ← Active game events (edit me!)
│   ├── shop/shop.json       ← Shop offers      (edit me!)
│   └── brawlers/brawlers.json ← Brawler metadata
│
└── tools/
    ├── patch_apk_ip.py      ← Patches libcb.config.so IP
    └── admin.py             ← Player admin CLI
```

---

## Credits

Protocol research: [Classic-Brawl](https://github.com/PhoenixFire6934/Classic-Brawl),
[bs-proxy/bs-messages](https://github.com/bs-proxy/bs-messages),
[VitalikObject/brawl-stars-server](https://github.com/VitalikObject/brawl-stars-server).

This emulator is independent, built from scratch for personal local use.
