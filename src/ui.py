import cv2
import numpy as np
from typing import Tuple, Optional

class UIManager:
    def __init__(self) -> None:
        # High-end Harmonious Theme Colors (BGR format)
        self.color_bg = (24, 24, 24)          # Very dark slate grey
        self.color_border = (60, 60, 60)      # Sophisticated dark border
        self.color_text = (245, 245, 245)      # Clean soft off-white
        self.color_active = (235, 140, 40)     # Vibrant electric cyan-blue
        self.color_muted = (90, 90, 235)       # Soft warm red for muted states
        self.color_accent = (65, 220, 100)     # Neon emerald green
        self.color_warning = (0, 190, 245)     # Warm glowing gold/amber

    def draw_hud(self, img: np.ndarray, volume_pct: float, is_muted: bool,
                 fps: float, hand_info: Optional[dict], calibration_state: str,
                 min_dist: float, max_dist: float, audio_ok: bool,
                 media_is_playing: bool) -> None:
        """Draws a premium, modern dashboard overlay on the camera frame."""
        h, w, _ = img.shape
        
        # 1. Glassmorphism Bottom Panel
        overlay = img.copy()
        cv2.rectangle(overlay, (15, h - 90), (w - 15, h - 15), self.color_bg, -1)
        # Border contour
        cv2.rectangle(overlay, (15, h - 90), (w - 15, h - 15), self.color_border, 1)
        cv2.addWeighted(overlay, 0.45, img, 0.55, 0, img)

        # 2. Modern Sleek Volume Slider
        # Design: Thin 4px seekbar track with circular glowing endpoints and concentric active slider knob
        bar_x1, bar_y = 40, h - 40
        bar_width = w - 210
        bar_height = 4  # Elegant thin line
        
        fill_width = int((volume_pct / 100.0) * bar_width)
        bar_color = self.color_muted if is_muted else self.color_accent
        
        # Draw background track
        cv2.rectangle(img, (bar_x1, bar_y - bar_height // 2), (bar_x1 + bar_width, bar_y + bar_height // 2), (65, 65, 65), -1)
        # Round track caps
        cv2.circle(img, (bar_x1, bar_y), bar_height // 2, (65, 65, 65), -1)
        cv2.circle(img, (bar_x1 + bar_width, bar_y), bar_height // 2, (65, 65, 65), -1)
        
        # Draw filled track
        if fill_width > 0:
            cv2.rectangle(img, (bar_x1, bar_y - bar_height // 2), (bar_x1 + fill_width, bar_y + bar_height // 2), bar_color, -1)
            cv2.circle(img, (bar_x1, bar_y), bar_height // 2, bar_color, -1)
            
            # Glow / Concentric circular slider knob (Thumb)
            thumb_x = bar_x1 + fill_width
            # Ambient outer glow
            cv2.circle(img, (thumb_x, bar_y), 13, bar_color, -1, lineType=cv2.LINE_AA)
            cv2.addWeighted(img, 0.8, img, 0.2, 0, img)  # blend for soft glow
            # Solid inner rings
            cv2.circle(img, (thumb_x, bar_y), 9, (255, 255, 255), -1, lineType=cv2.LINE_AA)
            cv2.circle(img, (thumb_x, bar_y), 5, bar_color, -1, lineType=cv2.LINE_AA)

        # Volume status typography
        status_text = "MUTED" if is_muted else f"{int(volume_pct)}%"
        cv2.putText(img, f"Vol: {status_text}", (bar_x1 + bar_width + 25, bar_y + 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, self.color_text, 2, cv2.LINE_AA)

        # 3. Dynamic Media Status Indicator Panel (Top Right)
        # Draws a gorgeous status panel showing standard Vector Play/Pause icon overlays
        panel_x1, panel_y1 = w - 240, 15
        panel_x2, panel_y2 = w - 15, 52
        
        media_overlay = img.copy()
        cv2.rectangle(media_overlay, (panel_x1, panel_y1), (panel_x2, panel_y2), self.color_bg, -1)
        cv2.rectangle(media_overlay, (panel_x1, panel_y1), (panel_x2, panel_y2), self.color_border, 1)
        cv2.addWeighted(media_overlay, 0.5, img, 0.5, 0, img)
        
        icon_color = self.color_accent if media_is_playing else self.color_warning
        icon_x, icon_y = panel_x1 + 18, panel_y1 + 18
        
        if media_is_playing:
            # Draw Vector Play Triangle
            pts = np.array([[icon_x, icon_y], [icon_x + 12, icon_y + 7], [icon_x, icon_y + 14]], np.int32)
            cv2.fillPoly(img, [pts], icon_color, lineType=cv2.LINE_AA)
            state_text = "PLAYING"
        else:
            # Draw Vector Pause Double-Bar (||)
            cv2.rectangle(img, (icon_x, icon_y), (icon_x + 4, icon_y + 14), icon_color, -1)
            cv2.rectangle(img, (icon_x + 7, icon_y), (icon_x + 11, icon_y + 14), icon_color, -1)
            state_text = "PAUSED"
            
        cv2.putText(img, f"MEDIA: {state_text}", (panel_x1 + 45, panel_y1 + 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, self.color_text, 2, cv2.LINE_AA)

        # 4. Draw FPS Counter (Top Right, stacked cleanly)
        fps_text = f"FPS: {int(fps)}"
        cv2.putText(img, fps_text, (w - 90, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.color_accent, 1, cv2.LINE_AA)

        # 5. Hand Info / Active Hand Badge (Top Left)
        if hand_info:
            hand_type = hand_info.get("hand_type", "Unknown")
            dist = hand_info.get("distance", 0.0)
            
            # Badge Background with premium border
            cv2.rectangle(img, (20, 15), (170, 50), self.color_bg, -1)
            cv2.rectangle(img, (20, 15), (170, 50), self.color_active, 1)
            
            hand_label = f"{hand_type} Hand"
            cv2.putText(img, hand_label, (32, 37),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, self.color_text, 1, cv2.LINE_AA)
            
            # Draw vector active line connecting finger tips
            t_tip = hand_info["thumb_tip"]
            i_tip = hand_info["index_tip"]
            cv2.line(img, t_tip, i_tip, self.color_active, 2, cv2.LINE_AA)
            
            # Glowing fingertips endpoint circles
            cv2.circle(img, t_tip, 8, self.color_active, -1, cv2.LINE_AA)
            cv2.circle(img, t_tip, 10, (255, 255, 255), 1, cv2.LINE_AA)
            
            cv2.circle(img, i_tip, 8, self.color_active, -1, cv2.LINE_AA)
            cv2.circle(img, i_tip, 10, (255, 255, 255), 1, cv2.LINE_AA)
            
            # Label depth-compensated normalized distance
            mid_x = (t_tip[0] + i_tip[0]) // 2
            mid_y = (t_tip[1] + i_tip[1]) // 2
            cv2.putText(img, f"{int(dist)}px ({hand_info['normalized_distance']:.2f})", (mid_x + 12, mid_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, self.color_text, 1, cv2.LINE_AA)

        # 6. Audio/Fist Status Check layout
        audio_offset = 0
        if not audio_ok:
            cv2.rectangle(img, (20, 60), (300, 95), (20, 20, 180), -1)
            cv2.putText(img, "AUDIO SYSTEM OFFLINE", (32, 82),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, self.color_text, 2, cv2.LINE_AA)
            audio_offset = 40

        # 6b. Fist Gesture HUD Overlay
        if hand_info and hand_info.get("is_fist", False):
            y_start = 60 + audio_offset
            cv2.rectangle(img, (20, y_start), (300, y_start + 35), self.color_bg, -1)
            cv2.rectangle(img, (20, y_start), (300, y_start + 35), self.color_warning, 1)
            cv2.putText(img, "FIST: Hold 1s to Play/Pause", (30, y_start + 23),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, self.color_warning, 1, cv2.LINE_AA)

        # 7. Bottom controls banner text
        info_str = "Q: Quit | M: Mute | C: Calibrate | R: Reset | P: Sync Media"
        cv2.putText(img, info_str, (40, h - 68),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, self.color_text, 1, cv2.LINE_AA)

        # 8. Calibration Mode panels
        if calibration_state != "IDLE":
            # Transparent warning block
            guide_panel = img.copy()
            cv2.rectangle(guide_panel, (0, 0), (w, 60), self.color_warning, -1)
            cv2.addWeighted(guide_panel, 0.3, img, 0.7, 0, img)
            
            prompt_msg = ""
            if calibration_state == "MIN":
                prompt_msg = "CALIBRATION: Pinch fingers close, then press 'C' to save MIN"
            elif calibration_state == "MAX":
                prompt_msg = "CALIBRATION: Stretch fingers wide, then press 'C' to save MAX"

            cv2.putText(img, prompt_msg, (30, 38),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)
            
            # Show active calibration bounds at bottom
            cal_info = f"Calibration: MIN={min_dist:.2f} | MAX={max_dist:.2f}"
            cv2.putText(img, cal_info, (w - 320, h - 68),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, self.color_warning, 1, cv2.LINE_AA)
        else:
            # Show active runtime bounds if idle
            cal_info = f"Bounds: MIN={min_dist:.2f} | MAX={max_dist:.2f}"
            cv2.putText(img, cal_info, (w - 240, h - 68),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, self.color_text, 1, cv2.LINE_AA)
