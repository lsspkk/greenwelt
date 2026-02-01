# Audio manager for pygame-ce
# Uses OGG files for cross-platform compatibility (including WASM/browser)

import os
import random
import pygame
from pathlib import Path

# Try to import yaml, fall back to simple parsing if not available
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def parse_soundmap_simple(content: str) -> dict:
    """Simple parser for soundmap.yaml format without yaml library."""
    result = {}
    current_key = None
    current_sounds = []
    current_volume = 1.0

    for line in content.split('\n'):
        stripped = line.strip()
        if not stripped:
            continue

        # Top-level key (no indentation)
        if not line.startswith(' ') and not line.startswith('\t') and stripped.endswith(':'):
            # Save previous entry
            if current_key is not None:
                result[current_key] = {'sounds': current_sounds, 'volume': current_volume}
            current_key = stripped[:-1]
            current_sounds = []
            current_volume = 1.0

        # Sound file entry
        elif stripped.startswith('- '):
            sound_path = stripped[2:].strip()
            current_sounds.append(sound_path)

        # Volume entry
        elif stripped.startswith('volume:'):
            try:
                current_volume = float(stripped.split(':')[1].strip())
            except (ValueError, IndexError):
                current_volume = 1.0

    # Save last entry
    if current_key is not None:
        result[current_key] = {'sounds': current_sounds, 'volume': current_volume}

    return result


def is_running_in_wasm():
    """Check if running in WASM/browser environment"""
    try:
        import sys
        # Pygbag/Pyodide sets this
        if sys.platform == "emscripten":
            return True
        # Alternative check
        import js  # noqa: F401
        return True
    except ImportError:
        return False


class AudioManager:
    """Simple audio manager for sound effects and music"""

    def __init__(self):
        self.sounds = {}
        self.music_playing = False
        self.sound_enabled = True
        self.music_enabled = True
        self.initialized = False
        self.is_wasm = is_running_in_wasm()
        self.audio_available = False

    def initialize(self):
        """Initialize the pygame mixer"""
        if self.is_wasm:
            # In WASM/browser, pygame.mixer works via browser audio API
            self._initialize_wasm()
        else:
            # In native mode (including WSL), try different approaches
            self._initialize_native()

    def _initialize_wasm(self):
        """Initialize audio for WASM/browser - straightforward"""
        try:
            pygame.mixer.init()
            self.initialized = True
            self.audio_available = True
        except Exception as e:
            print(f"WASM audio init failed: {e}")
            self.initialized = False
            self.audio_available = False

    def _initialize_native(self):
        """Initialize audio for native/desktop/WSL"""
        # First, try normal initialization
        try:
            pygame.mixer.init()
            self.initialized = True
            self.audio_available = True
            return
        except Exception:
            pass

        # If that failed, try with explicit SDL audio driver settings
        # Try common drivers in order of preference
        drivers_to_try = ["pulseaudio", "alsa", "dsp", "dummy"]

        for driver in drivers_to_try:
            try:
                os.environ["SDL_AUDIODRIVER"] = driver
                pygame.mixer.quit()  # Reset mixer state
                pygame.mixer.init()
                self.initialized = True
                self.audio_available = (driver != "dummy")
                if self.audio_available:
                    print(f"Audio initialized with driver: {driver}")
                return
            except Exception:
                continue

        # All drivers failed - audio not available
        print("Audio not available - running in silent mode")
        self.initialized = False
        self.audio_available = False

    def load_sounds(self):
        """Load all sound effects at startup"""
        if not self.initialized:
            return

        if not self.audio_available:
            # Audio not available, skip loading
            return

        # load soundmap.yaml file from data
        yaml_path = Path("data/soundmap.yaml")
        with open(yaml_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if HAS_YAML:
                self.soundmap = yaml.safe_load(content)
            else:
                self.soundmap = parse_soundmap_simple(content)



        sound_files = []
        # each key in yaml has sounds field, that is a list of filenames
        for sound_key, sound_info in self.soundmap.items():
            sound_files.extend(sound_info.get("sounds", []))

        loaded_count = 0
        for filename in sound_files:
            filepath = Path(filename)
            if filepath.exists():
                name = filename.replace(".ogg", "")
                try:
                    self.sounds[name] = pygame.mixer.Sound(str(filepath))
                    loaded_count += 1
                except Exception as e:
                    print(f"Failed to load sound {filename}: {e}")
            else:
                print(f"Sound file not found: {filename}")
        
        print(f"Loaded {loaded_count}/{len(sound_files)} sounds")

    def play(self, sound_name: str):
        """Play a sound effect by name"""
        if not self.initialized or not self.audio_available:
            return

        if not self.sound_enabled:
            return

        # choose a random sound from the soundmap for this sound_name
        if sound_name in self.soundmap:
            options = self.soundmap[sound_name]
            sound_files = options.get("sounds", [])
            volume = options.get("volume", 1.0)
            if sound_files:
                # Shuffle and try each sound until one works
                shuffled = sound_files.copy()
                random.shuffle(shuffled)
                for chosen_file in shuffled:
                    chosen_name = chosen_file.replace(".ogg", "")
                    if chosen_name in self.sounds:
                        sound = self.sounds[chosen_name]
                        sound.set_volume(volume)
                        sound.play()
                        return



    def play_music(self, filename: str, loop: bool = True):
        """Start background music"""
        if not self.initialized or not self.audio_available:
            return

        if not self.music_enabled:
            return

        filepath = Path("assets/audio") / filename
        if filepath.exists():
            try:
                pygame.mixer.music.load(str(filepath))
                pygame.mixer.music.set_volume(0.3)
                pygame.mixer.music.play(-1 if loop else 0)
                self.music_playing = True
            except Exception as e:
                print(f"Failed to play music {filename}: {e}")

    def stop_music(self):
        """Stop background music"""
        if not self.initialized or not self.audio_available:
            return

        pygame.mixer.music.stop()
        self.music_playing = False

    def toggle_sound(self):
        """Toggle sound effects on/off"""
        self.sound_enabled = not self.sound_enabled
        return self.sound_enabled

    def toggle_music(self):
        """Toggle music on/off"""
        self.music_enabled = not self.music_enabled
        if not self.music_enabled and self.audio_available:
            pygame.mixer.music.stop()
        return self.music_enabled

    def get_status(self):
        """Return audio status for debugging"""
        if self.is_wasm:
            platform = "WASM/Browser"
        else:
            platform = "Native"

        if self.audio_available:
            status = "Available"
        elif self.initialized:
            status = "Dummy (silent)"
        else:
            status = "Not available"

        return f"{platform}: {status}"
