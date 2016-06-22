import cv2
import sys
import thread
import concurrent.futures
import time
from communication import send_fame_to_iFaceSERVER

def cutFrame(frame, p1, p2):

    increaseX = p2[0] *0.3 
    increaseY = p2[1] *0.3
    rows = len(frame)
    cols = len (frame[1])
    a = int(p1[1]-increaseY) if int(p1[1]-increaseY) >= 0 else 0  
    b = int(p2[1]+increaseY) if int(p2[1]+increaseY) <= rows else rows  
    c = int(p1[0]-increaseX) if int(p1[0]-increaseX) >= 0 else 0  
    d = int(p2[0]+ increaseX) if int(p2[0]+ increaseX)  <= cols else cols  

    return frame[a:b,c:d]


#def rotate(gray, deg):
    
 #   gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)
 #   rows,cols = gray.shape
 #   M = cv2.getRotationMatrix2D((cols/2,rows/2),deg,1)
 #   rotat_gray = cv2.warpAffine(gray,M,(cols,rows))
 #   #cv2.imshow('rot', rotat_gray) 
    #return rotat_gray

def faceDetect(gray, deg):
  #  rotat_gray = rotate(gray, deg)
    rotat_gray = gray
    faces = faceCascade.detectMultiScale(
        rotat_gray,
        scaleFactor=1.1,
        minNeighbors=2,
        minSize=(50, 50),
        maxSize=(120,120)
    )
    return faces

faceCascade = cv2.CascadeClassifier("haarcascade_frontalface_alt2.xml")
video_capture = cv2.VideoCapture("rtsp://admin:Admin12345@192.168.1.106/jpeg/ch2/sub/av_stream")

window = ()
prev = time.time()
while True:
    # Capture frame-by-frame
    ret, frame = video_capture.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = []

   # for angle in range(-20,20,10):
    faces.extend(faceDetect(gray, 0))

    for (x, y, w, h) in faces:
        p1 = (x,y)
        p2 = (x+w,y+h)
        window = cutFrame(frame, p1, p2)
        thread.start_new_thread(send_fame_to_iFaceSERVER,(window,))
        #cv2.rectangle(frame, p1, p2, (0, 255, 0), 2)
        cv2.imshow('win', window)

    # Display the resulting frame
    cv2.imshow('Video', frame)

    # FPS
    #print 1.0 /(time.time()-prev) 
    #prev = time.time()

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything is done, release the capture
video_capture.release()
cv2.destroyAllWindows()
