import time
import os
import json
from typing import Tuple, Optional
import numpy as np
from ctypes import cast, POINTER
import comtypes
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

class VolumeController:
    def __init__(self, alpha: float = 0.25) -> None:
        self.alpha = alpha
        
        # Calibration state (Normalized to palm size for depth-compensation)
        self.default_min_dist = 0.15
        self.default_max_dist = 0.85
        self.min_dist = self.default_min_dist
        self.max_dist = self.default_max_dist
        
        # Calibration modes: "IDLE", "MIN", "MAX"
        self.calibration_state = "IDLE"
        
        # Smoothing tracking
        self.prev_volume_pct = 50.0
        
        # Mute gesture tracking
        self.is_muted = False
        self.mute_gesture_start_time: Optional[float] = None
        self.last_mute_toggle_time = 0.0
        self.mute_cooldown = 1.5  # seconds
        
        # Media gesture tracking (Closed Fist Play/Pause)
        self.fist_start_time: Optional[float] = None
        self.last_media_trigger_time = 0.0
        self.media_cooldown = 2.0  # seconds
        self.media_is_playing = True
        
        # Media swipe gesture tracking (Open Hand Swipe Left/Right)
        self.x_history: list = []
        self.last_swipe_time = 0.0
        self.swipe_cooldown = 1.2  # seconds
        
        # Initialize Audio Device
        self.volume_interface = None
        self.volume_api = None
        self.initialize_audio()
        
        # Load saved calibration config if available
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
        self.load_config()

    def initialize_audio(self) -> bool:
        """Initializes the Windows master volume control API with COM library initialization."""
        try:
            # Crucial for Windows COM interfaces to initialize correctly in modular architectures
            comtypes.CoInitialize()
            
            devices = AudioUtilities.GetSpeakers()
            if not devices:
                print("Error: No speakers found.")
                return False
            
            # Check if the returned object is the high-level Pycaw AudioDevice wrapper or a raw COM interface
            if hasattr(devices, "EndpointVolume"):
                self.volume_api = devices.EndpointVolume
            else:
                self.volume_interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self.volume_api = cast(self.volume_interface, POINTER(IAudioEndpointVolume))
            
            # Get initial volume
            try:
                self.is_muted = self.volume_api.GetMute()
                current_vol = self.volume_api.GetMasterVolumeLevelScalar()
                self.prev_volume_pct = current_vol * 100.0
            except Exception as ex:
                print(f"Failed to query current state: {ex}")
                self.prev_volume_pct = 50.0
            print("Audio interface initialized successfully.")
            return True
        except Exception as e:
            print(f"Audio initialization failed: {e}")
            self.volume_api = None
            return False

    def is_audio_available(self) -> bool:
        return self.volume_api is not None

    def toggle_mute(self) -> None:
        """Toggles the system mute state with cooldown protection."""
        now = time.time()
        if now - self.last_mute_toggle_time < self.mute_cooldown:
            return
            
        self.last_mute_toggle_time = now
        if not self.is_audio_available():
            # Fallback if no audio API
            self.is_muted = not self.is_muted
            return

        try:
            self.is_muted = not self.is_muted
            self.volume_api.SetMute(self.is_muted, None)
        except Exception as e:
            print(f"Error toggling mute: {e}")

    def update_mute_gesture(self, distance: float) -> bool:
        """
        Checks if fingers are pinched extremely close (< min_dist + 0.05) for 1 second.
        Returns True if a toggle occurred.
        """
        pinch_threshold = min(self.min_dist + 0.05, 0.22)
        now = time.time()
        
        if distance < pinch_threshold:
            if self.mute_gesture_start_time is None:
                self.mute_gesture_start_time = now
            elif now - self.mute_gesture_start_time >= 1.0:
                # 1.0 second threshold met
                self.toggle_mute()
                self.mute_gesture_start_time = None  # Reset tracking
                return True
        else:
            self.mute_gesture_start_time = None
            
        return False

    def set_volume_from_distance(self, distance: float) -> float:
        """
        Calculates, smooths adaptively, and sets the system volume level.
        Returns the current smoothed volume percentage.
        """
        # Clamp distance to calibration range
        clamped_dist = np.clip(distance, self.min_dist, self.max_dist)
        
        # Map distance to percentage (0 - 100)
        target_vol_pct = np.interp(clamped_dist, [self.min_dist, self.max_dist], [0.0, 100.0])
        
        # Adaptive EMA smoothing: rate of change adjusts alpha
        # When moving quickly, alpha is higher (responsive). When stationary, alpha is lower (rock-solid stable).
        diff = abs(target_vol_pct - self.prev_volume_pct)
        adaptive_alpha = np.interp(diff, [0.0, 30.0], [0.10, 0.65])
        
        smoothed_vol_pct = adaptive_alpha * target_vol_pct + (1.0 - adaptive_alpha) * self.prev_volume_pct
        self.prev_volume_pct = smoothed_vol_pct
        
        # Set system volume
        if self.is_audio_available() and not self.is_muted:
            try:
                # Convert 0-100 to 0.0-1.0 scalar
                self.volume_api.SetMasterVolumeLevelScalar(smoothed_vol_pct / 100.0, None)
            except Exception as e:
                print(f"Failed to set system volume: {e}")
                
        return smoothed_vol_pct

    def update_media_gesture(self, is_fist: bool) -> bool:
        """
        Checks if hand is a closed fist for 1.0 second.
        Triggers a native Windows Media Play/Pause keypress.
        """
        now = time.time()
        if is_fist:
            if self.fist_start_time is None:
                self.fist_start_time = now
            elif now - self.fist_start_time >= 1.0:
                if now - self.last_media_trigger_time >= self.media_cooldown:
                    self.trigger_media_play_pause()
                    self.last_media_trigger_time = now
                self.fist_start_time = None  # Reset trigger tracking
                return True
        else:
            self.fist_start_time = None
        return False

    def trigger_media_play_pause(self) -> None:
        """Sends native Windows VK_MEDIA_PLAY_PAUSE event using ctypes keybd_event."""
        try:
            import ctypes
            VK_MEDIA_PLAY_PAUSE = 0xB3
            # Key Down
            ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
            # Key Up
            ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 2, 0)
            
            # Toggle internal media playing state
            self.media_is_playing = not self.media_is_playing
            print(f"Media Play/Pause triggered. Current State: {'PLAYING' if self.media_is_playing else 'PAUSED'}")
        except Exception as e:
            print(f"Error sending media key: {e}")

    def advance_calibration(self, current_distance: float) -> None:
        """Advances calibration state machine using current hand distance."""
        if self.calibration_state == "IDLE":
            self.calibration_state = "MIN"
        elif self.calibration_state == "MIN":
            self.min_dist = max(0.05, current_distance)
            self.calibration_state = "MAX"
        elif self.calibration_state == "MAX":
            # Max must be strictly greater than min
            if current_distance > self.min_dist:
                self.max_dist = current_distance
            else:
                self.max_dist = self.min_dist + 0.40
            self.calibration_state = "IDLE"
            self.save_config()

    def reset_calibration(self) -> None:
        """Resets calibration to standard defaults."""
        self.min_dist = self.default_min_dist
        self.max_dist = self.default_max_dist
        self.calibration_state = "IDLE"
        self.save_config()

    def load_config(self) -> None:
        """Loads calibration settings from config.json."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    self.min_dist = data.get("min_dist", self.default_min_dist)
                    self.max_dist = data.get("max_dist", self.default_max_dist)
                print(f"Calibration config loaded: Min={self.min_dist:.2f}, Max={self.max_dist:.2f}")
        except Exception as e:
            print(f"Failed to load config: {e}")

    def save_config(self) -> None:
        """Saves current calibration settings to config.json."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump({
                    "min_dist": self.min_dist,
                    "max_dist": self.max_dist
                }, f, indent=4)
            print("Calibration config saved to config.json.")
        except Exception as e:
            print(f"Failed to save config: {e}")

    def update_swipe_gesture(self, current_x: float) -> Optional[str]:
        """
        Tracks X coordinates of hand over time to detect rapid swipe gestures.
        Triggers Next/Prev track media keys natively on Windows.
        """
        now = time.time()
        self.x_history.append(current_x)
        if len(self.x_history) > 6:
            self.x_history.pop(0)
            
        # We need enough history and check cooldown
        if len(self.x_history) >= 5 and (now - self.last_swipe_time >= self.swipe_cooldown):
            delta_x = self.x_history[-1] - self.x_history[0]
            
            # Rapid movement threshold (120 pixels across 5-6 frames)
            if abs(delta_x) > 130:
                self.x_history.clear()  # Clear to prevent multiple skip triggers
                self.last_swipe_time = now
                if delta_x > 0:
                    self.trigger_media_next()
                    return "NEXT"
                else:
                    self.trigger_media_prev()
                    return "PREV"
        return None

    def trigger_media_next(self) -> None:
        """Sends native Windows VK_MEDIA_NEXT_TRACK event."""
        try:
            import ctypes
            VK_MEDIA_NEXT_TRACK = 0xB0
            ctypes.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 2, 0)
            print("Media Next Track triggered successfully.")
        except Exception as e:
            print(f"Error sending next media key: {e}")

    def trigger_media_prev(self) -> None:
        """Sends native Windows VK_MEDIA_PREV_TRACK event."""
        try:
            import ctypes
            VK_MEDIA_PREV_TRACK = 0xB1
            ctypes.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 2, 0)
            print("Media Prev Track triggered successfully.")
        except Exception as e:
            print(f"Error sending prev media key: {e}")
