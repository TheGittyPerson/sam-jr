import sys
import os
import glob
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- Global Configuration ---
# Resolve the path pattern using glob to find the actual file path
TARGET_PATTERN = os.path.expanduser(
    "~/Library/Application Support/Spotify/Users/*-user/ad-state-storage.bnk")
MATCHED_FILES = glob.glob(TARGET_PATTERN)

if not MATCHED_FILES:
    print("Error: Could not find ad-state-storage.bnk matching pattern: "
          f"{TARGET_PATTERN}")
    print("Please make sure Spotify is installed and you have logged in at "
          "least once.")
    sys.exit(1)

# Set the resolved file path and its parent directory to global variables
TARGET_FILE_PATH = MATCHED_FILES[0]
TARGET_DIR = os.path.dirname(TARGET_FILE_PATH)
FILE_NAME = os.path.basename(TARGET_FILE_PATH)

print(f"[*] Successfully resolved target file: {TARGET_FILE_PATH}")
print(f"[*] Watching directory: {TARGET_DIR}")


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
    except subprocess.CalledProcessError:
        # If AppleScript fails (e.g., Spotify is closed), return None
        return None


def manage_spotify_volume():
    """Checks the current track name and adjusts the volume accordingly."""
    # AppleScript to fetch the current track name from Spotify
    apple_script = 'tell application "Spotify" to name of current track'
    track_name = run_osascript(apple_script)

    if not track_name:
        return

    # Check for "advertisement" case-insensitively
    if "advertisement" in track_name.lower():
        print(f"[!] Ad Detected: '{track_name}'. Muting Spotify volume.")
        run_osascript('tell application "Spotify" to set sound volume to 0')
    else:
        print(f"[✓] Playing Music: '{track_name}'. Setting Spotify volume to "
              "100.")
        run_osascript('tell application "Spotify" to set sound volume to 100')


class SpotifyAdMuter(FileSystemEventHandler):
    """Custom event handler that listens for file modifications."""

    def on_modified(self, event):
        # Watchdog fires events for directories too;
        # ensure we only track our file
        if event.is_directory:
            return

        # Standardize paths to ensure an exact match
        if (os.path.abspath(str(event.src_path))
                == os.path.abspath(TARGET_FILE_PATH)):
            # A tiny delay allows Spotify to finish writing to the file before
            # we poll AppleScript
            time.sleep(0.1)
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
