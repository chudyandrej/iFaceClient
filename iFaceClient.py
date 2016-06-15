#!/usr/bin/python

import cv2
import thread
import numpy as np
import sys
import math
from threading import Thread
from communication import send_fame_to_iFaceSERVER, thread_counter
from motion_trigger import moutionTrigger

#SETTINGS

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
trigger = None


def get_size_capture(cap):
	frame = cap.read()[1]
	frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
	w, h = frame.shape
	print "Resolution", w, " x ", h
	return (h,w)

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
		trigger.make_sample(point1, point2)



# Main function of program
def main():

	global espeak, point1, point2, config_mode
	if "off-espeak" in sys.argv:
		espeak = False
	#Open video capture arg -> number (camera USB) / path to video / URL
	cam = cv2.VideoCapture(0)

	point1 = (0, 0)
	point2 = get_size_capture(cam)

	cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
	cv2.setMouseCallback(WINDOW_NAME, click_and_crop)

	global trigger
	trigger = moutionTrigger(cam, point1, point2)


	while True:
		frame = cam.read()[1]
		frame_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
		show_frame = frame.copy()

		if config_mode:
			cv2.rectangle(show_frame, point1, point2, (0, 255, 0), 2)
			#cv2.putText(show_frame,'Configure mode',(int(w-(w*0.02)),50),  cv2.FONT_HERSHEY_SIMPLEX, 2,(255,0,0),2,cv2.LINE_AA)
		cv2.imshow(WINDOW_NAME, show_frame)

		if not cliced and  trigger.calculate_change(frame_gray) > SENSITIVITY_MOTION_TRIGGER:
			thread.start_new_thread(send_fame_to_iFaceSERVER,(frame,frame_gray))

		
		print thread_coungit

	    # Wait up to 1ms for a key press. Quit if the key is either ESC or 'q'.
		key = cv2.waitKey(1) & 0xFF
		if key == ord("q"):
			cv2.destroyWindow(WINDOW_NAME)
			break
		elif key == ord("c"):
			config_mode = not config_mode


if __name__ == "__main__":
    main()
