#http://bversion.com/WordPress/2023/09/22/drone-programming-gesture-control/?fbclid=IwAR3suunHgtjFPXGXGcpFAAZK_hd_2TiDSmOzblF4CUEW5tzbiUVoiGFy3Lc

"""
Created on Mon Nov 13 16:12:30 2023

@author: shado
"""

from djitellopy import Tello
import cv2
import mediapipe as mp
import threading
import math
import logging
import time


tello = Tello()
tello.LOGGER.setLevel(logging.ERROR) #Ignoring the info from Tello
fly = True #For debuggin purpose


mpHands = mp.solutions.hands
hands = mpHands.Hands(min_detection_confidence=0.8, min_tracking_confidence=0.8)


mpDraw = mp.solutions.drawing_utils

def hand_detection(tello):

    while True:
        
        global gesture
        
        
        frame = tello.get_frame_read().frame
        frame = cv2.flip(frame, 1)
      
        result = hands.process(frame)
        
        
        frame_height = frame.shape[0]
        frame_width = frame.shape[1]
        my_hand = []
        
        if result.multi_hand_landmarks:
            for handlms, handside in zip(result.multi_hand_landmarks, result.multi_handedness):
                if handside.classification[0].label == 'Right': 
                    continue
                        
                
                mpDraw.draw_landmarks(frame, handlms, mpHands.HAND_CONNECTIONS,\
                                        mp.solutions.drawing_styles.get_default_hand_landmarks_style(),\
                                        mp.solutions.drawing_styles.get_default_hand_connections_style())          
               
                # Convert all the hand information from a ratio into actual position according to the frame size.
                for i, landmark in enumerate(handlms.landmark):
                    x = int(landmark.x * frame_width)
                    y = int(landmark.y * frame_height)
                    my_hand.append((x, y))
                    
                for hand_coordinates in my_hand:
                    cv2.putText(frame, f"X: {my_hand[0]},Y:{my_hand[1]}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    
        #Detection algorithm     
                finger_on = []
                if my_hand[4][0] > my_hand[2][0]:
                    finger_on.append(1)
                    
                else:
                    finger_on.append(0) 
                for i in range(1,5):
                    if my_hand[4 + i*4][1] < my_hand[2 + i*4][1]: 
                        finger_on.append(1)
                    else:
                        finger_on.append(0)
                
                gesture = 'Unknown'        
                if sum(finger_on) == 0:
                    gesture = 'Stop'
                elif sum(finger_on) == 5:
                    gesture = 'Land'
                elif sum(finger_on) == 1:
                    if finger_on[0] == 1:
                        gesture = 'Right'
                    elif finger_on[4] == 1:
                        gesture = 'Left'
                    elif finger_on[1] == 1:
                        gesture = 'Up'
                elif sum(finger_on) == 2:
                    if finger_on[0] == finger_on[1] == 1:
                        gesture = 'Down'
                    elif finger_on[1] == finger_on[4] == 1:
                        gesture = 'Forward flip'
                    elif finger_on[1] == finger_on[2] == 1:
                        gesture = 'Come'
                    elif finger_on[0] == finger_on[4] == 1:
                        gesture = 'Rotate clockwise'
                elif sum(finger_on) == 3: 
                    if finger_on[1] == finger_on[2] == finger_on[3] == 1:
                        gesture = 'Away'
        
        cv2.putText(frame, gesture, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 3)
       
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
        cv2.imshow('Tello Video Stream', frame)
        cv2.waitKey(1)
        if gesture == 'Landed':
            break      

# Connect to the drone via WIFI
tello.connect()

# I
tello.streamon()

while True:
            frame = tello.get_frame_read().frame
            if frame is not None:
                break


gesture = 'Unknown'
video_thread = threading.Thread(target=hand_detection, args=(tello,), daemon=True)
video_thread.start()    

# Take off the drone
time.sleep(1)
if fly:
    tello.takeoff()
    tello.set_speed(10)
    time.sleep(1)
    tello.move_up(80)
    
while True:
    
    hV = dV = vV = rV = 0
    if gesture == 'Land':
        break
    elif gesture == 'Stop' or gesture == 'Unknown':
        hV = dV = vV = rV = 0
    elif gesture == 'Right':
        hV = -15
    elif gesture == 'Left':
        hV = 15
    elif gesture == 'Up':
        vV = 20
    elif gesture == 'Down':
        vV = -20
    elif gesture == 'Come':
        dV = 15
    elif gesture == 'Away':
        dV = -15
    elif gesture == 'Forward flip':
        tello.flip_forward()
        time.sleep(1)
    elif gesture == 'Rotate clockwise':
        tello.rotate_clockwise(180)
        time.sleep(1)
    tello.send_rc_control(hV, dV, vV, rV)
    time.sleep(0.01)
    
# Landing the drone
if fly: tello.land()
gesture = 'Landed'

# Stop the video stream
tello.streamoff()

print("Battery :", tello.get_battery())
    
