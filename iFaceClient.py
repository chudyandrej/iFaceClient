import cv2
import sys
import time
import base64
import requests
import thread
import numpy as np



#SETTINGS 
BLUR_SIZE = 3			
NOISE_CUTOFF = 20		# Set sensitivity between new frame and sample 
WINDOW_NAME = "Camera"
FRAMES_TO_LEARN_BG = 30


#Function for send frame to iFace server
def send_fame_to_analysis(frame):
	img_str = cv2.imencode('.jpg', frame)[1].tostring()
	encoded_img = base64.encodestring(img_str)
	
	encoded_img = encoded_img.replace('+', '-')
	encoded_img = encoded_img.replace('/', '_')
	encoded_img = encoded_img.replace('.', '.')

	req = requests.post (url="http://192.168.1.157:8080/recognise", data="image="+encoded_img+"&camraID=1")
	print req.text

# Main function of program
def main():
	
	#Open video capture arg -> number (camera USB) / path to video / URL
	cam = cv2.VideoCapture(0)
	#Set size of video capture
	cam.set(3, 1280)
	cam.set(4, 720)
	#Creat window
	cv2.namedWindow(WINDOW_NAME, cv2.CV_WINDOW_AUTOSIZE)
	# Stabilize the detector by letting the camera warm up andseeding the first frames.
	original_frame = cam.read()[1]
	original_frame = cam.read()[1]
	#Convert to GRAY color space
	frame_now = cv2.cvtColor(original_frame, cv2.COLOR_RGB2GRAY)
	frame_now = cv2.blur(frame_now, (BLUR_SIZE, BLUR_SIZE))
	frame_prior = frame_now
	counter_frame = 1
	while True:

		frame_delta = cv2.absdiff(frame_prior, frame_now)
		frame_delta = cv2.threshold(frame_delta, NOISE_CUTOFF, 255, 3)[1]
		delta_count = cv2.countNonZero(frame_delta)
		##cv2.imshow("AAA", frame_delta)
		counter_frame += 1
		print delta_count
		if delta_count > 1500:
			thread.start_new_thread(send_fame_to_analysis,(original_frame,))

		if counter_frame > FRAMES_TO_LEARN_BG:
			frame_prior = frame_now
			counter_frame = 0

		original_frame = cam.read()[1]
		cv2.imshow(WINDOW_NAME, original_frame)
		frame_now = cv2.cvtColor(original_frame, cv2.COLOR_RGB2GRAY)
		frame_now = cv2.blur(frame_now, (BLUR_SIZE, BLUR_SIZE))

	    # Wait up to 1ms for a key press. Quit if the key is either ESC or 'q'.
		key = cv2.waitKey(1)
		if key == 0x1b or key == ord('q'):
			cv2.destroyWindow(WINDOW_NAME)
			break



if __name__ == "__main__":
    main()




