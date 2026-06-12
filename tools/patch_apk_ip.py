#!/usr/bin/env python3
"""
tools/patch_apk_ip.py — Patch the server IP inside the Frida config file.

What this does
──────────────
The patched Classic Brawl APK ships with a Frida gadget whose
configuration lives in:

    lib/armeabi-v7a/libcb.config.so   (older builds: libgg.config.so)

That file is plain JSON (despite the .so extension) and looks like:

    {
      "interaction": {
        "interaction": {
          "type"      : "script",
          "path"      : "libscript.so",
          "on_change" : "reload",
          "parameters": {
            "redirectHost": "YOUR_IP_HERE",
            "relocate"    : true
          }
        }
      }
    }

You just need to change "redirectHost" to your server's IP address.

Usage
─────
  # Auto-detect your LAN IP and patch the file:
  python tools/patch_apk_ip.py  path/to/libcb.config.so

  # Specify an IP manually:
  python tools/patch_apk_ip.py  path/to/libcb.config.so  192.168.1.42

  # Patch to localhost (same Android device running the server):
  python tools/patch_apk_ip.py  path/to/libcb.config.so  127.0.0.1

After patching, re-sign the APK and install it (see README for details).
"""

import sys
import json
import socket
import shutil
import os


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def patch_config_so(filepath: str, new_ip: str):
    """
    Read the Frida JSON config file, update 'redirectHost', and write it back.
    Keeps a .bak backup of the original.
    """
    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        sys.exit(1)

    # Backup
    backup = filepath + ".bak"
    shutil.copy2(filepath, backup)
    print(f"  Backup saved → {backup}")

    with open(filepath, "r") as f:
        content = f.read()

    # ── Try JSON parse ────────────────────────────────────────────────
    try:
        cfg = json.loads(content)
        # Navigate the nested structure
        params = cfg["interaction"]["interaction"]["parameters"]
        old_ip = params.get("redirectHost", "???")
        params["redirectHost"] = new_ip
        with open(filepath, "w") as f:
            json.dump(cfg, f, indent=2)
        print(f"  Old IP : {old_ip}")
        print(f"  New IP : {new_ip}")
        print(f"  ✔ Patched successfully → {filepath}")
        return
    except (json.JSONDecodeError, KeyError):
        pass

    # ── Fallback: raw string replacement ─────────────────────────────
    # Sometimes the file has a different structure; do a best-effort
    # string swap for common IP patterns
    import re
    pattern = r'"redirectHost"\s*:\s*"([^"]+)"'
    match = re.search(pattern, content)
    if match:
        old_ip = match.group(1)
        new_content = re.sub(pattern, f'"redirectHost": "{new_ip}"', content)
        with open(filepath, "w") as f:
            f.write(new_content)
        print(f"  Old IP : {old_ip}  (raw replace)")
        print(f"  New IP : {new_ip}")
        print(f"  ✔ Patched (raw) → {filepath}")
    else:
        print("[ERROR] Could not find 'redirectHost' in the file.")
        print("  Content preview:", content[:300])
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    filepath = sys.argv[1]
    new_ip   = sys.argv[2] if len(sys.argv) >= 3 else get_local_ip()

    print(f"\n[*] Patching: {filepath}")
    print(f"[*] Target IP: {new_ip}\n")
    patch_config_so(filepath, new_ip)
    print()
    print("Next steps:")
    print("  1. If you extracted from APK: rebuild the APK and re-sign it")
    print("     (use apktool + uber-apk-signer — see README).")
    print("  2. Install the patched APK on your Android device / emulator.")
    print(f"  3. Start the server: python main.py")
    print(f"  4. Make sure your device can reach {new_ip}:9339\n")


if __name__ == "__main__":
    main()
