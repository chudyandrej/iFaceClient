import cv2


class moutionTrigger:
	count = 0
	sampe_frame = None
	p1 = ()
	p2 = ()


	def __init__(self, cap, p1, p2):
		self.cap = cap
		self.p1 = p1
		self.p2 = p2
		self.make_sample(p1, p2)


  	def calculate_change(self, frame_actual):
		cut_frame_actual = frame_actual[self.p1[1]:self.p2[1], self.p1[0]:self.p2[0]]
		cut_frame_actual = cv2.blur(cut_frame_actual, (3, 3))
		frame_delta = cv2.absdiff(self.sampe_frame, cut_frame_actual)
		frame_delta = cv2.threshold(frame_delta, 20, 255, 3)[1]
		self.count += 1
		if self.count > 15:
			self.sampe_frame = cut_frame_actual
		return cv2.countNonZero(frame_delta)


	def make_sample(self, po1, po2):
		frame = self.cap.read()[1]
		frame = frame[po1[1]:po2[1], po1[0]:po2[0]]
		frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
		self.sampe_frame = cv2.blur(frame, (3, 3))
		self.p1 = po1
		self.p2 = po2
		print "ZAPISANE"