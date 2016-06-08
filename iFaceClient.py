import cv2
import sys
import time

# The two main parameters that affect movement detection sensitivity
# are BLUR_SIZE and NOISE_CUTOFF. Both have little direct effect on
# CPU usage. In theory a smaller BLUR_SIZE should use less CPU, but
# for the range of values that are effective the difference is
# negligible. The default values are effective with on most light
# conditions with the cameras I have tested. At these levels the
# detector can easily trigger on eye blinks, yet not trigger if the
# subject remains still without blinking. These levels will likely be
# useless outdoors.
BLUR_SIZE = 3
NOISE_CUTOFF = 20
# Ah, but the third main parameter that affects movement detection
# sensitivity is the time between frames. I like about 10 frames per
# second. Even 4 FPS is fine.
#FRAMES_PER_SECOND = 10

cam = cv2.VideoCapture(0)

cam.set(3, 1280)
cam.set(4, 720)


window_name = "delta view"
cv2.namedWindow(window_name, cv2.CV_WINDOW_AUTOSIZE)

# Stabilize the detector by letting the camera warm up and
# seeding the first frames.
frame_now = cam.read()[1]
frame_now = cam.read()[1]
frame_now = cv2.cvtColor(frame_now, cv2.COLOR_RGB2GRAY)
frame_now = cv2.blur(frame_now, (BLUR_SIZE, BLUR_SIZE))
frame_prior = frame_now

delta_count_last = 1
while True:

	frame_delta = cv2.absdiff(frame_prior, frame_now)
	frame_delta = cv2.threshold(frame_delta, NOISE_CUTOFF, 255, 3)[1]
	delta_count = cv2.countNonZero(frame_delta)
	print delta_count
	# Visual detection statistics output.
	# Normalize improves brightness and contrast.
	# Mirror view makes self display more intuitive.


	# Stdout output.
	# Only output when there is new movement or when movement stops.
	# Time codes are in epoch time format.


	# Advance the frames.
	frame_prior = frame_now
	frame_now = cam.read()[1]
	cv2.imshow("Original", frame_now)
	frame_now = cv2.cvtColor(frame_now, cv2.COLOR_RGB2GRAY)
	frame_now = cv2.blur(frame_now, (BLUR_SIZE, BLUR_SIZE))

    # Wait up to 10ms for a key press. Quit if the key is either ESC or 'q'.
	key = cv2.waitKey(10)
	if key == 0x1b or key == ord('q'):
		cv2.destroyWindow(window_name)
		break

# vim: set ft=python fileencoding=utf-8 sr et ts=4 sw=4 : See help 'modeline'