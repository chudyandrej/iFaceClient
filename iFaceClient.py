#!/usr/bin/python

import cv2
import thread
import numpy as np
import sys
import math
from threading import Thread
from communication import send_fame_to_iFaceSERVER, thread_counter

#SETTINGS
URL_server = "http://192.168.1.121:8080/recognise"
WINDOW_NAME = "Camera"
FRAMES_TO_LEARN_BG = 30
SENSITIVITY_MOTION_TRIGGER = 3000

#Atributes of program (extended)
BLUR_SIZE = 3
NOISE_CUTOFF = 20		# Set sensitivity between new frame and sample

#Global variables
espeak = True
config_mode = False
point1 = ()
point2 = ()
cliced = False

def click_and_crop(event, x, y, flags, param):
	# grab references to the global variables
	global point1, point2,cliced

	if config_mode and event == cv2.EVENT_LBUTTONDOWN:
		cliced = True
		point1 = (x,y)
		point2 = (x + 10,y + 10)

	if config_mode and event == cv2.EVENT_MOUSEMOVE and cliced:
		point2 = (x,y)

	if config_mode and event == cv2.EVENT_LBUTTONUP:
		cliced = False
		point2 = (x,y)

def scene_change(frame_sample, frame_now):
	frame_delta = cv2.absdiff(frame_sample, frame_now)
	frame_delta = cv2.threshold(frame_delta, NOISE_CUTOFF, 255, 3)[1]
	return cv2.countNonZero(frame_delta)

# Main function of program
def main():
	global espeak, point1, point2, config_mode
	if "off-espeak" in sys.argv:
		espeak = False
	#Open video capture arg -> number (camera USB) / path to video / URL
	cam = cv2.VideoCapture("rtsp://admin:123456@192.168.1.103:554/1")

	#Set size of video capture
	#cam.set(3, 720)
	#cam.set(4, 576)
	#Creat window
	cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
	cv2.setMouseCallback(WINDOW_NAME, click_and_crop)

	# Operations whit first frame
	frame_sample = cam.read()[1]
	frame_sample = cv2.cvtColor(frame_sample, cv2.COLOR_RGB2GRAY)
	frame_sample = cv2.blur(frame_sample, (BLUR_SIZE, BLUR_SIZE))

	counter_frame = 1

 	point1 = (0, 0)
	w, h = frame_sample.shape
	point2 = (h-1, w-1)

	while True:
		frame = cam.read()[1]
		frame_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
		frame_blur_gray = cv2.blur(frame_gray, (BLUR_SIZE, BLUR_SIZE))
		show_frame = frame.copy()

		if config_mode:
			cv2.rectangle(show_frame, point1, point2, (0, 255, 0), 2)
			cv2.putText(show_frame,'Configure mode',(int(w-(w*0.02)),50),  cv2.FONT_HERSHEY_SIMPLEX, 2,(255,0,0),2,cv2.LINE_AA)
		cv2.imshow(WINDOW_NAME, show_frame)

		counter_frame += 1

		if not cliced and  scene_change(frame_sample[point1[1]:point2[1], point1[0]:point2[0]],frame_blur_gray[point1[1]:point2[1], point1[0]:point2[0]]) > SENSITIVITY_MOTION_TRIGGER:
			thread.start_new_thread(send_fame_to_iFaceSERVER,(frame,frame_gray))

		if counter_frame > FRAMES_TO_LEARN_BG:
			frame_sample = frame_blur_gray
			counter_frame = 0

		print thread_counter

	    # Wait up to 1ms for a key press. Quit if the key is either ESC or 'q'.
		key = cv2.waitKey(1) & 0xFF
		if key == ord("q"):
			cv2.destroyWindow(WINDOW_NAME)
			break
		elif key == ord("c"):
			config_mode = not config_mode


if __name__ == "__main__":
    main()
