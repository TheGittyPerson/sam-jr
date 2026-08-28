import sys
import os
import glob
import time
import subprocess
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- Global Configuration ---

TARGET_PATTERN = os.path.expanduser(
    "~/Library/Application Support/Spotify/Users/*-user/ad-state-storage.bnk")
MATCHED_FILES = glob.glob(TARGET_PATTERN)

if not MATCHED_FILES:
    print("Error: Could not find ad-state-storage.bnk matching pattern: "
          f"{TARGET_PATTERN}")
    print("Please make sure Spotify is installed and you have logged in at "
          "least once.")
    sys.exit(1)

TARGET_FILE_PATH = MATCHED_FILES[0]
TARGET_DIR = os.path.dirname(TARGET_FILE_PATH)
FILE_NAME = os.path.basename(TARGET_FILE_PATH)

ALERT_SOUND_PATH = "/System/Library/Sounds/Bottle.aiff"

WAS_MUTED = False

print(f"[✓] Successfully resolved target file: {TARGET_FILE_PATH}")
print(f"[*] Watching directory: {TARGET_DIR}")

# ----------------------------


def run_osascript(script):
    """Helper function to execute AppleScript commands via shell."""
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(
            "[˟] Error while telling Spotify "
            f"{script.removeprefix('tell application \"Spotify\" ')}"
        )
        print(e.output)


def manage_spotify_volume():
    global WAS_MUTED

    apple_script = (
        'tell application "Spotify"\n'
        '    if it is running then\n'
        '        try\n'
        '            set tArtist to artist of current track\n'
        '            set tAlbum to album of current track\n'
        '            return tArtist & "|||" & tAlbum\n'
        '        on error\n'
        '            return ""\n'
        '        end try\n'
        '    end if\n'
        'end tell'
    )

    script_output = run_osascript(apple_script)

    if script_output is None:
        return

    # Split the output safely back into components
    parts = script_output.split("|||")
    if len(parts) < 2:
        return

    this_is_an_ad = not parts[0].strip() or not parts[1].strip()

    if this_is_an_ad and not WAS_MUTED:
        print(f"[!] Ad Detected — Muting Spotify volume.")
        run_osascript('tell application "Spotify" to set sound volume to 0')
        play_sound()
        WAS_MUTED = True
    elif not this_is_an_ad and WAS_MUTED:
        print(f"[✓] Music Restored — Setting Spotify volume to 100.")
        run_osascript(
            'tell application "Spotify" to set sound volume to 100')
        WAS_MUTED = False


def play_sound():
    """Plays the built-in macOS alert sound asynchronously."""
    if os.path.exists(ALERT_SOUND_PATH):
        subprocess.Popen(["afplay", ALERT_SOUND_PATH])


class SpotifyAdMuter(FileSystemEventHandler):
    """Custom event handler that listens for file modifications."""

    def __init__(self):
        super().__init__()
        self.throttle_seconds = 2
        self.last_triggered = 0.0

    def on_modified(self, event):
        current_time = time.time()

        if current_time - self.last_triggered < self.throttle_seconds:
            return

        self.last_triggered = current_time

        time.sleep(0.1)  # Wait for the ad to register in currently playing
        manage_spotify_volume()


if __name__ == "__main__":
    event_handler = SpotifyAdMuter()
    observer = Observer()

    # Watchdog monitors the directory containing the file
    observer.schedule(event_handler, path=TARGET_DIR, recursive=False)
    observer.start()

    print("[*] Script running. Play some music to begin monitoring...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Stopping observer...")
        observer.stop()

    observer.join()
