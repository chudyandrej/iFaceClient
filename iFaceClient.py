import cv2
import sys
import time
import base64
import requests





BLUR_SIZE = 3
NOISE_CUTOFF = 20
# Ah, but the third main parameter that affects movement detection
# sensitivity is the time between frames. I like about 10 frames per
# second. Even 4 FPS is fine.
#FRAMES_PER_SECOND = 10

def send_fame_to_analysis(frame):

	img_str = cv2.imencode('.jpg', frame)[1].tostring()
	encoded_img = base64.b64encode(img_str)
	req = requests.post (url="http://192.168.1.121:8080/recognise", data="image="+encoded_img+"&camraID=1")
	print(req.status_code, req.reason)
	print req.text



cam = cv2.VideoCapture(0)

cam.set(3, 1280)
cam.set(4, 720)


window_name = "delta view"
cv2.namedWindow(window_name, cv2.CV_WINDOW_AUTOSIZE)

# Stabilize the detector by letting the camera warm up and
# seeding the first frames.
original_frame = cam.read()[1]
original_frame = cam.read()[1]
frame_now = cv2.cvtColor(original_frame, cv2.COLOR_RGB2GRAY)
frame_now = cv2.blur(frame_now, (BLUR_SIZE, BLUR_SIZE))
frame_prior = frame_now

delta_count_last = 1
while True:

	frame_delta = cv2.absdiff(frame_prior, frame_now)
	frame_delta = cv2.threshold(frame_delta, NOISE_CUTOFF, 255, 3)[1]
	delta_count = cv2.countNonZero(frame_delta)
	print delta_count
	send_fame_to_analysis(original_frame)


	# Advance the frames.
	frame_prior = frame_now
	original_frame = cam.read()[1]
	cv2.imshow("Original", original_frame)
	frame_now = cv2.cvtColor(original_frame, cv2.COLOR_RGB2GRAY)
	frame_now = cv2.blur(frame_now, (BLUR_SIZE, BLUR_SIZE))

    # Wait up to 10ms for a key press. Quit if the key is either ESC or 'q'.
	key = cv2.waitKey(10)
	if key == 0x1b or key == ord('q'):
		cv2.destroyWindow(window_name)
		break

# vim: set ft=python fileencoding=utf-8 sr et ts=4 sw=4 : See help 'modeline'