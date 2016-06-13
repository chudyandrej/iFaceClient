import cv2
import sys
import time
import base64
import requests
import thread
import numpy as np
from Queue import Queue
from threading import Thread
from time import sleep
import json
from atomiclong import AtomicLong


#SETTINGS
URL_server = "http://192.168.1.121:8080/recognise"
WINDOW_NAME = "Camera"
FRAMES_TO_LEARN_BG = 30
SENSITIVITY_MOTION_TRIGGER = 3000



#Atributes of program (extended)
BLUR_SIZE = 3
NOISE_CUTOFF = 20		# Set sensitivity between new frame and sample

#Global variables
thread_counter = AtomicLong(0)
espeak = True


def frame_to_imgB64(frame):
	img_str = cv2.imencode('.jpg', frame)[1].tostring()
	encoded_img = base64.encodestring(img_str)
	encoded_img = encoded_img.replace('+', '-')
	encoded_img = encoded_img.replace('/', '_')
	encoded_img = encoded_img.replace('.', '.')
	return encoded_img

def voice_synthesizer(json_message):
	parsed_json = json.loads(json_message)
	if parsed_json['count'] > 0:
		command = "espeak -v sk --stdout '%s %s' | aplay" % (parsed_json['first_name'], parsed_json['last_name'])
		os.system(command.encode('UTF-8'))


#Function for send frame to iFace server
def send_fame_to_iFaceSERVER(frame):
	global thread_counter
	thread_counter += 1
	encoded_img = frame_to_imgB64(frame)
	req = requests.post (url=URL_server, data="image="+encoded_img+"&camraID=1")
	print req.text
	print "posielam"
	#if espeak:
#		voice_synthesizer(req.text)
	thread_counter -= 1

def scene_change(frame_sample, frame_now):
	frame_delta = cv2.absdiff(frame_sample, frame_now)
	frame_delta = cv2.threshold(frame_delta, NOISE_CUTOFF, 255, 3)[1]
	return cv2.countNonZero(frame_delta)





# Main function of program
def main():
	if "off-espeak" in sys.argv:
		global espeak
		espeak = False
	#Open video capture arg -> number (camera USB) / path to video / URL
	cam = cv2.VideoCapture(0)
	#Set size of video capture
	cam.set(3, 720)
	cam.set(4, 576)
	#Creat window
	cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
	# Stabilize the detector by letting the camera warm up andseeding the first frames.

	frame_sample = cam.read()[1]
	frame_sample = cam.read()[1]
	frame_sample = cv2.cvtColor(frame_sample, cv2.COLOR_RGB2GRAY)
	frame_sample = cv2.blur(frame_sample, (BLUR_SIZE, BLUR_SIZE))
	counter_frame = 1

	while True:
		frame = cam.read()[1]
		cv2.imshow(WINDOW_NAME, frame)
		frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
		frame = cv2.blur(frame, (BLUR_SIZE, BLUR_SIZE))
		counter_frame += 1

		if scene_change(frame_sample,frame) > 3000:
			thread.start_new_thread(send_fame_to_iFaceSERVER,(frame,))

		if counter_frame > FRAMES_TO_LEARN_BG:
			frame_sample = frame
			counter_frame = 0

		print thread_counter.value
	    # Wait up to 1ms for a key press. Quit if the key is either ESC or 'q'.
		if cv2.waitKey(1) & 0xFF == ord('q'):

			cv2.destroyWindow(WINDOW_NAME)
			break

if __name__ == "__main__":
    main()
