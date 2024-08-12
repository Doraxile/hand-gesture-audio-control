from math import hypot
import cv2
import mediapipe as mp
import numpy as np
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Initialize camera and variables
cap = cv2.VideoCapture(0)
volMin, volMax = -65, 0  # Adjust volume range

# Initialize MediaPipe Hands
mpHands = mp.solutions.hands
hands = mpHands.Hands()
mpDraw = mp.solutions.drawing_utils

# Variables to track the state of the hand
thumb_tip_id = 4
index_tip_id = 8
hand_open = False

# Get the audio device
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

def draw_volume_bar(img, volume_level):
    # Define bar dimensions and position
    bar_width = 200
    bar_height = 20
    x, y = 10, img.shape[0] - 30

    # Calculate the filled width based on volume level
    fill_width = int(np.interp(volume_level, [volMin, volMax], [0, bar_width]))

    # Draw the background and the filled part of the volume bar
    cv2.rectangle(img, (x, y), (x + bar_width, y + bar_height), (0, 0, 0), -1)  # Background
    cv2.rectangle(img, (x, y), (x + fill_width, y + bar_height), (0, 255, 0), -1)  # Filled part

    # Add text indicating the volume level
    cv2.putText(img, f'{int(volume_level)} dB', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

while True:
    success, img = cap.read()
    if not success:
        break

    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)

    lmList = []
    if results.multi_hand_landmarks:
        for handlandmark in results.multi_hand_landmarks:
            for id, lm in enumerate(handlandmark.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmList.append([id, cx, cy])
            mpDraw.draw_landmarks(img, handlandmark, mpHands.HAND_CONNECTIONS)

        if len(lmList) >= 9:  # Check if enough landmarks are detected
            x1, y1 = lmList[thumb_tip_id][1], lmList[thumb_tip_id][2]
            x2, y2 = lmList[index_tip_id][1], lmList[index_tip_id][2]

            # Calculate the distance between thumb tip and index finger tip
            length = hypot(x2 - x1, y2 - y1)

            # Adjust volume based on the distance
            vol = np.interp(length, [15, 100], [0, 1])  # Adjust range as needed

            try:
                # Set the audio volume
                volume.SetMasterVolumeLevelScalar(vol, None)
            except Exception as e:
                print(f"Error setting volume: {e}")

            hand_open = True  # Reset hand state
        else:
            hand_open = False

    # Get the current volume level
    current_volume = volume.GetMasterVolumeLevel()
    draw_volume_bar(img, current_volume)

    cv2.imshow('Image', img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
