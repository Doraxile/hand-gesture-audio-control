from typing import Tuple, List, Optional, Dict
import cv2
import mediapipe as mp
import numpy as np
from math import hypot

class HandTracker:
    def __init__(self, mode: bool = False, max_hands: int = 2, 
                 detection_con: float = 0.5, track_con: float = 0.5) -> None:
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=mode,
            max_num_hands=max_hands,
            min_detection_confidence=detection_con,
            min_tracking_confidence=track_con
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.results = None

    def find_hands(self, img: np.ndarray, draw: bool = True) -> np.ndarray:
        """Processes the frame for hand landmarks and optionally draws them."""
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)
        
        if self.results.multi_hand_landmarks and draw:
            for hand_lms in self.results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(img, hand_lms, self.mp_hands.HAND_CONNECTIONS)
        return img

    def get_hand_info(self, img: np.ndarray, hand_idx: int = 0) -> Optional[Dict]:
        """
        Extracts landmark list, hand type (Left/Right), and specific points.
        Returns a dictionary with hand details if a hand is detected, else None.
        """
        if not self.results or not self.results.multi_hand_landmarks:
            return None
            
        if hand_idx >= len(self.results.multi_hand_landmarks):
            return None

        hand_lms = self.results.multi_hand_landmarks[hand_idx]
        h, w, c = img.shape
        lm_list: List[Tuple[int, int]] = []
        
        for lm in hand_lms.landmark:
            cx, cy = int(lm.x * w), int(lm.y * h)
            lm_list.append((cx, cy))

        # Detect left/right hand classification.
        # Note: MediaPipe hand classification is mirrored. We correct it based on standard view.
        hand_type = "Unknown"
        if self.results.multi_handedness:
            handedness = self.results.multi_handedness[hand_idx]
            hand_type = handedness.classification[0].label
            # Usually MediaPipe swaps left/right on standard camera feeds. We can just use the classification label directly
            # or reverse it if needed. Let's provide the raw classified label.

        # Landmark 4: Thumb Tip, Landmark 8: Index Finger Tip
        thumb_tip = lm_list[4]
        index_tip = lm_list[8]
        distance = hypot(index_tip[0] - thumb_tip[0], index_tip[1] - thumb_tip[1])

        # Landmark 0: Wrist, Landmark 5: Index Finger MCP (Knuckle)
        # The distance between the wrist and index finger knuckle acts as a stable reference for palm size (depth proxy)
        wrist = lm_list[0]
        index_mcp = lm_list[5]
        palm_size = hypot(index_mcp[0] - wrist[0], index_mcp[1] - wrist[1])
        
        # Calculate depth-invariant normalized distance
        normalized_distance = distance / max(palm_size, 1.0)

        # Check if the hand is a closed fist (for play/pause gesture)
        # Finger tips: 8, 12, 16, 20. Respective joints: 6, 10, 14, 18.
        # In screen coordinates, y increases downwards, so tip y > joint y means folded.
        fingers_folded = [
            lm_list[8][1] > lm_list[6][1],
            lm_list[12][1] > lm_list[10][1],
            lm_list[16][1] > lm_list[14][1],
            lm_list[20][1] > lm_list[18][1],
        ]
        is_fist = sum(fingers_folded) >= 3

        return {
            "lm_list": lm_list,
            "hand_type": hand_type,
            "thumb_tip": thumb_tip,
            "index_tip": index_tip,
            "distance": distance,
            "palm_size": palm_size,
            "normalized_distance": normalized_distance,
            "is_fist": is_fist
        }
