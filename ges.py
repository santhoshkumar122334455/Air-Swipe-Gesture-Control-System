

import cv2
import mediapipe as mp
import time
import os
from playsound import playsound
import threading

# --- Configuration Section ---
PROCESSING_WIDTH = 480
ADB_PATH = r"C:\Users\Admin\AppData\Local\Android\Sdk\platform-tools\adb.exe"
ZONE_H_BUFFER = 0.30
ZONE_V_BUFFER = 0.30
BOX_COLOR = (255, 0, 0)
TEXT_COLOR = (255, 255, 255)
ACTIVE_COLOR = (0, 255, 0)
FINGER_DOT_COLOR = (0, 255, 0)

# --- NEW: Sound File Configuration ---
# Make sure these sound files are in the same folder as this script!
SOUND_ACTIVATION = 'click.mp3'  # A short click/tick sound
SOUND_SWIPE = 'swoosh.mp3'      # A whoosh sound for the action

# --- Function to play sound without freezing the video ---
def play_sound_async(sound_file):
    try:
        # We run playsound in a separate thread so it doesn't block the main video loop
        threading.Thread(target=playsound, args=(sound_file,), daemon=True).start()
    except Exception as e:
        # This will catch errors if the sound file is not found
        print(f"Could not play sound {sound_file}: {e}")

# --- ADB Swipe Functions (Now with sound!) ---
def swipe_right():
    print("ACTION: RIGHT (Pinky) -> Sending SWIPE RIGHT command")
    play_sound_async(SOUND_SWIPE) # Play the swipe sound
    os.system(f"{ADB_PATH} shell input swipe 200 1000 800 1000 100")

def swipe_left():
    print("ACTION: LEFT (Thumb) -> Sending SWIPE LEFT command")
    play_sound_async(SOUND_SWIPE)
    os.system(f"{ADB_PATH} shell input swipe 800 1000 200 1000 100")

def swipe_up():
    print("ACTION: UP (Index) -> Sending SWIPE UP command")
    play_sound_async(SOUND_SWIPE)
    os.system(f"{ADB_PATH} shell input swipe 500 1500 500 500 100")

def swipe_down():
    print("ACTION: DOWN (Ring) -> Sending SWIPE DOWN command")
    play_sound_async(SOUND_SWIPE)
    os.system(f"{ADB_PATH} shell input swipe 500 500 500 1500 100")

# --- Setup Hand Tracking ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.5)
mp_draw = mp.solutions.drawing_utils

# --- Setup Webcam ---
cap = cv2.VideoCapture(0)

# --- State Management ---
last_action_times = {"LEFT": 0, "RIGHT": 0, "UP": 0, "DOWN": 0}
ACTION_COOLDOWN = 0.8

# --- Main Program Loop ---
while cap.isOpened():
    success, full_size_image = cap.read()
    if not success: break

    full_size_image = cv2.flip(full_size_image, 1)

    aspect_ratio = full_size_image.shape[0] / full_size_image.shape[1]
    processing_height = int(PROCESSING_WIDTH * aspect_ratio)
    processing_image = cv2.resize(full_size_image, (PROCESSING_WIDTH, processing_height))
    
    image_rgb = cv2.cvtColor(processing_image, cv2.COLOR_BGR2RGB)
    results = hands.process(image_rgb)

    h, w, _ = full_size_image.shape
    left_zone_end = int(w * ZONE_H_BUFFER)
    right_zone_start = int(w * (1 - ZONE_H_BUFFER))
    up_zone_end = int(h * ZONE_V_BUFFER)
    down_zone_start = int(h * (1 - ZONE_V_BUFFER))
    current_time = time.time()

    if results.multi_hand_landmarks:
        hand_landmarks = results.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(full_size_image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
        
        thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
        index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
        ring_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP]
        pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]

        thumb_cx, thumb_cy = int(thumb_tip.x * w), int(thumb_tip.y * h)
        index_cx, index_cy = int(index_tip.x * w), int(index_tip.y * h)
        ring_cx, ring_cy = int(ring_tip.x * w), int(ring_tip.y * h)
        pinky_cx, pinky_cy = int(pinky_tip.x * w), int(pinky_tip.y * h)
        
        cv2.circle(full_size_image, (thumb_cx, thumb_cy), 10, FINGER_DOT_COLOR, cv2.FILLED)
        cv2.circle(full_size_image, (index_cx, index_cy), 10, FINGER_DOT_COLOR, cv2.FILLED)
        cv2.circle(full_size_image, (ring_cx, ring_cy), 10, FINGER_DOT_COLOR, cv2.FILLED)
        cv2.circle(full_size_image, (pinky_cx, pinky_cy), 10, FINGER_DOT_COLOR, cv2.FILLED)

        # Check each finger against its dedicated zone
        if thumb_cx < left_zone_end and current_time - last_action_times["LEFT"] > ACTION_COOLDOWN:
            play_sound_async(SOUND_ACTIVATION)
            swipe_left()
            last_action_times["LEFT"] = current_time
            cv2.rectangle(full_size_image, (0, 0), (left_zone_end, h), ACTIVE_COLOR, -1)
            
        if pinky_cx > right_zone_start and current_time - last_action_times["RIGHT"] > ACTION_COOLDOWN:
            play_sound_async(SOUND_ACTIVATION)
            swipe_right()
            last_action_times["RIGHT"] = current_time
            cv2.rectangle(full_size_image, (right_zone_start, 0), (w, h), ACTIVE_COLOR, -1)

        if index_cy < up_zone_end and current_time - last_action_times["UP"] > ACTION_COOLDOWN:
            play_sound_async(SOUND_ACTIVATION)
            swipe_up()
            last_action_times["UP"] = current_time
            cv2.rectangle(full_size_image, (0, 0), (w, up_zone_end), ACTIVE_COLOR, -1)

        if ring_cy > down_zone_start and current_time - last_action_times["DOWN"] > ACTION_COOLDOWN:
            play_sound_async(SOUND_ACTIVATION)
            swipe_down()
            last_action_times["DOWN"] = current_time
            cv2.rectangle(full_size_image, (0, down_zone_start), (w, h), ACTIVE_COLOR, -1)

    # Drawing the UI
    # ... (The rest of the drawing code is the same) ...
    cv2.rectangle(full_size_image, (0, 0), (left_zone_end, h), BOX_COLOR, 2)
    cv2.putText(full_size_image, 'LEFT (Thumb)', (20, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 1, TEXT_COLOR, 2)
    cv2.rectangle(full_size_image, (right_zone_start, 0), (w, h), BOX_COLOR, 2)
    cv2.putText(full_size_image, 'RIGHT (Pinky)', (right_zone_start + 20, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 1, TEXT_COLOR, 2)
    cv2.rectangle(full_size_image, (0, 0), (w, up_zone_end), BOX_COLOR, 2)
    cv2.putText(full_size_image, 'UP (Index)', (w // 2 - 80, up_zone_end - 20), cv2.FONT_HERSHEY_SIMPLEX, 1, TEXT_COLOR, 2)
    cv2.rectangle(full_size_image, (0, down_zone_start), (w, h), BOX_COLOR, 2)
    cv2.putText(full_size_image, 'DOWN (Ring)', (w // 2 - 90, down_zone_start + 50), cv2.FONT_HERSHEY_SIMPLEX, 1, TEXT_COLOR, 2)
    
    cv2.imshow('Audio Feedback Controller - Press ESC to Exit', full_size_image)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()