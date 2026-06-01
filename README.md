# Real-Time Hand Gesture Volume Controller

An intelligent, professional, and customizable real-time hand gesture volume controller for Windows systems. Using computer vision and hand tracking, the application maps hand pinches directly to the OS audio system. Built with modular OOP architecture using OpenCV, MediaPipe, and Pycaw.

## Features

- **Real-Time Hand Tracking**: Uses high-performance Google MediaPipe Hands tracking to identify landmark locations instantly.
- **Depth-Compensated Volume Control**: Normalizes finger distance relative to palm size, making volume control completely independent of your hand's distance from the camera!
- **Adaptive EMA Smoothing**: Features dynamic smoothing where the EMA alpha value adaptively scales based on the rate of hand movement—rock-solid stability when resting, instant responsiveness when moving.
- **Media Playback Gestures**: Make a closed fist (at least 3 fingers folded) and hold it for **1.0 second** to trigger a native Windows **Play/Pause** event.
- **Track Skipping Gestures (Swipe)**: Swipe your open hand rapidly to the right (Left-to-Right) to skip to the **Next Track**, or rapidly to the left (Right-to-Left) to play the **Previous Track**, complete with built-in cooldowns to prevent double-skips.
- **Dynamic Calibration Mode**: Calibrate minimum and maximum pinch distance at runtime matching any hand size and physical distance to the webcam.
- **Left/Right Hand Detection**: Shows a dedicated UI badge classifying whether the right or left hand is currently controlling audio.
- **Gesture Mute / Unmute**: Pinch and hold fingers very close together for 1.0 second to toggle system mute state with built-in toggle cooldown.
- **Beautiful Transparent HUD**: Features clean, custom transparent panels, smoothed progression meters, and overlay hints.
- **Robust Error Handling**: Gracefully handles offline webcams and reports when Windows audio devices are occupied or missing.

## Tech Stack

- **Python 3.8+**
- **OpenCV**: Video capture, transformation, and high-performance overlay UI rendering.
- **MediaPipe**: Deep learning-based multi-hand tracking.
- **NumPy**: Interpolation calculations.
- **Pycaw & comtypes**: Native Windows core-audio endpoint communication API.

## Project Structure

```text
hand-gesture-audio-control/
├── src/
│   ├── main.py                # Main orchestration loop and keyboard shortcut handler
│   ├── hand_tracker.py        # HandTracker class wrapping MediaPipe Hand detection
│   ├── volume_controller.py   # VolumeController class managing Pycaw volume, EMA, and calibration
│   └── ui.py                  # UIManager class drawing visual HUD and state graphics
├── assets/
│   └── screenshot.png         # Project representation preview
├── requirements.txt           # Declared dependencies
├── README.md                  # Comprehensive project documentation
└── .gitignore                 # Standard Python project ignore list
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/hand-gesture-audio-control.git
   cd hand-gesture-audio-control
   ```

2. (Optional) Set up a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the program with:
```bash
python src/main.py
```

### Keyboard Controls

- `q`: **Quit** the application.
- `m`: **Mute/Unmute** fallback keyboard control.
- `c`: **Calibration Mode** - cycles through steps:
  1. Starts calibration: Pinch fingers together, then press `c` to save MIN.
  2. Spreads fingers apart comfortably, then press `c` to save MAX.
  3. Completes calibration and starts scaling volume.
- `r`: **Reset** calibration back to system defaults (MIN=20px, MAX=150px).

### Gesture Controls

- **Volume Adjustment**: Scale the distance between your **Thumb Tip** (Landmark 4) and **Index Finger Tip** (Landmark 8) to set the volume from 0% to 100%. (This is fully depth-compensated for hands closer/further from camera).
- **Hold-to-Mute / Unmute**: Pinch thumb and index tips together extremely closely (normalized distance below threshold) and hold it for **1.0 second**. The HUD volume bar will turn red to indicate muted status. Repeat the pinch to unmute.
- **Play/Pause Media (Closed Fist)**: Close your hand into a fist (fold index, middle, ring, and pinky fingers) and hold it for **1.0 second**. This triggers a native Windows Media Play/Pause action. When a fist is detected, a dedicated orange HUD badge will appear on screen.
- **Next/Prev Track (Horizontal Swipe)**: Spread your fingers open and swipe your hand rapidly to the right (Left-to-Right) or left (Right-to-Left) across the camera's view. This triggers Windows native Media Next/Prev track skips. (Note: Swipe tracking is automatically disabled during pinch/volume adjustment to prevent accidental skips).

## Future Improvements

- Add support for macOS CoreAudio and Linux ALSA systems.
- Build a lightweight system-tray widget to run the control loop in the background.
- Integrate gesture-based play/pause and media track skipping using multi-finger swipes.

## License

This project is open-source and licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
