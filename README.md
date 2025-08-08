# Hand Gesture Audio Control 🎛️✋

A Python application that lets you control your system volume in real-time using hand gestures detected via webcam.  
Built with [MediaPipe](https://mediapipe.dev/), [OpenCV](https://opencv.org/), and [PyCaw](https://github.com/AndreMiras/pycaw).

---

##  Project Link
GitHub Repository: [Doraxile/hand-gesture-audio-control](https://github.com/Doraxile/hand-gesture-audio-control)

---

##  Features
- Real-time hand gesture detection using MediaPipe
- Thumb-index finger distance controls system volume
- On-screen volume bar for instant feedback

---

##  Project Structure
hand-gesture-audio-control/
│-- hand_gesture_audio_control.py # Main script
│-- requirements.txt # Dependencies
│-- assets/
│ └── screenshot.png # Program screenshot


---

##  Installation & Usage

1. **Clone the repository**
   ```bash
   git clone https://github.com/Doraxile/hand-gesture-audio-control.git
   cd hand-gesture-audio-control
   ```
2. Create a virtual environment (Recommended Python 3.10)

   ```bash
   python -m venv venv
   venv\Scripts\activate  # For Windows
   ```
3. Install dependencies

   ```bash
   pip install -r requirements.txt
   ```
4. Run the application
   ```bash
   python hand_gesture_audio_control.py
   ```
5. Exit the program
   Press ```q``` in the webcam window.
   
##  Dependencies
- opencv-python
- mediapipe (compatible with Python 3.10)
- numpy
- pycaw
- comtypes

##  Demo
Below is a preview of the running application:

<img width="867" height="506" alt="volume1" src="https://github.com/user-attachments/assets/9dc4f37f-9f5c-4b90-aa19-40fd74411305" />
<img width="874" height="512" alt="volume2" src="https://github.com/user-attachments/assets/8a0d13be-f55d-440d-8c93-9df0850ef911" />



##  License
This project is open-source and available for educational and personal use.
