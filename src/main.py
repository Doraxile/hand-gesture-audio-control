import cv2
import time
import sys
from hand_tracker import HandTracker
from volume_controller import VolumeController
from ui import UIManager

def main() -> None:
    # Initialize Camera
    print("Attempting to open camera (using DirectShow backend for instant start on Windows)...")
    # DirectShow (cv2.CAP_DSHOW) prevents the typical 10-20 second lag when opening USB cameras on Windows
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("Camera index 0 not available, trying external camera index 1...")
        cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

    if not cap.isOpened():
        # Fallback to standard backend if DirectShow is not supported/fails
        print("DirectShow failed, falling back to standard backend on camera index 0...")
        cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not access any webcam (tried index 0 and 1). Please check USB connection and permissions.")
        sys.exit(1)

    # Initialize Modules
    tracker = HandTracker(max_hands=1, detection_con=0.7, track_con=0.7)
    vol_ctrl = VolumeController(alpha=0.25)
    ui_mgr = UIManager()

    # Audio status logs
    if vol_ctrl.is_audio_available():
        print("Windows Audio Service successfully connected via Pycaw.")
    else:
        print("Warning: Windows Audio Endpoint not available. System volume changes will be simulated.")

    # Time tracking variables for FPS calculation
    prev_time = time.time()
    fps = 0.0

    print("\n--- Hand Gesture Volume Control ---")
    print("Controls:")
    print("  'q' - Quit the program")
    print("  'm' - Toggle mute / unmute")
    print("  'c' - Start/advance calibration mode")
    print("  'r' - Reset calibration to defaults")
    print("  'p' - Toggle/sync visual Play/Pause status in HUD")
    print("-----------------------------------\n")

    try:
        while True:
            success, frame = cap.read()
            if not success:
                print("Error: Failed to grab frame from webcam. Exiting...")
                break

            # Flip frame horizontally for a more intuitive selfie-view mirror effect
            frame = cv2.flip(frame, 1)

            # Calculate FPS
            curr_time = time.time()
            time_diff = curr_time - prev_time
            if time_diff > 0:
                fps = 1.0 / time_diff
            prev_time = curr_time

            # 1. Detect Hand Landmarks
            frame = tracker.find_hands(frame, draw=True)
            hand_info = tracker.get_hand_info(frame, hand_idx=0)

            # Retrieve active volume status for representation
            volume_pct = vol_ctrl.prev_volume_pct
            
            # 2. Extract distance, calibrate, scale volume, check media/mute gestures
            if hand_info:
                norm_dist = hand_info["normalized_distance"]
                is_fist = hand_info["is_fist"]
                
                if vol_ctrl.calibration_state == "IDLE":
                    # Process Play/Pause Media Gesture
                    vol_ctrl.update_media_gesture(is_fist)
                    
                    # Update volume and mute checks only if hand is NOT closed (not a fist)
                    # This prevents the volume from suddenly spiking down to 0% during play/pause trigger
                    if not is_fist:
                        vol_ctrl.update_mute_gesture(norm_dist)
                        volume_pct = vol_ctrl.set_volume_from_distance(norm_dist)
                        
                        # Process Swipe Track Gestures (only when hand is spread open, index 9 is middle knuckle)
                        if norm_dist > 0.45:
                            current_x = hand_info["lm_list"][9][0]
                            vol_ctrl.update_swipe_gesture(current_x)
            
            # 3. Draw UI HUD Overlays
            ui_mgr.draw_hud(
                img=frame,
                volume_pct=volume_pct,
                is_muted=vol_ctrl.is_muted,
                fps=fps,
                hand_info=hand_info,
                calibration_state=vol_ctrl.calibration_state,
                min_dist=vol_ctrl.min_dist,
                max_dist=vol_ctrl.max_dist,
                audio_ok=vol_ctrl.is_audio_available(),
                media_is_playing=vol_ctrl.media_is_playing
            )

            # Show Frame
            cv2.imshow('Hand Gesture Volume Controller', frame)

            # 4. Handle Keyboard Actions
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                print("Exiting application...")
                break
                
            elif key == ord('m'):
                vol_ctrl.toggle_mute()
                print(f"Mute toggled. Current Muted State: {vol_ctrl.is_muted}")
                
            elif key == ord('c'):
                # Advance calibration state only if a hand is actively detected
                if hand_info:
                    current_dist = hand_info["normalized_distance"]
                    vol_ctrl.advance_calibration(current_dist)
                    print(f"Calibration State advanced to: {vol_ctrl.calibration_state}")
                    if vol_ctrl.calibration_state == "IDLE":
                        print(f"Calibration saved! Min: {vol_ctrl.min_dist:.2f}, Max: {vol_ctrl.max_dist:.2f}")
                else:
                    print("Warning: No hand detected! Please keep your hand fully visible in front of the camera to calibrate.")
                    
            elif key == ord('r'):
                vol_ctrl.reset_calibration()
                print("Calibration reset to system defaults.")

            elif key == ord('p'):
                # Manual sync keyboard shortcut to toggle visual status on the HUD
                vol_ctrl.media_is_playing = not vol_ctrl.media_is_playing
                print(f"Media HUD state manually synchronized. Current HUD State: {'PLAYING' if vol_ctrl.media_is_playing else 'PAUSED'}")

    except KeyboardInterrupt:
        print("\nApplication stopped by user via keyboard interrupt.")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Webcam and display resources released cleanly.")

if __name__ == "__main__":
    main()
