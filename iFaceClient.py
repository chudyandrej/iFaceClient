import cv2
import sys
import thread
import concurrent.futures
import time
import os.path
from communication import send_fame_to_iFaceSERVER,getCounterThreads


####******   SETTINGS   *******#####

URL_IPCAMERA = "rtsp://admin:Admin12345@192.168.1.106/jpeg/ch2/sub/av_stream"
PATH_HAARCASCADE = "./haarcascade_frontalface_alt2.xml"
MIN_SIZE_FACE = 80      #Distance from camera  (Big influence to performace)
MAX_SIZE_FACE = 300     #Distance from camera  (Big influence to performace)


class Bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def cutFrame(frame, p1, p2):
    increaseX = p2[0] * 0.1 
    increaseY = p2[1] * 0.2
    rows = len(frame)
    cols = len (frame[1])
    a = int(p1[1]-increaseY) if int(p1[1]-increaseY) >= 0 else 0  
    b = int(p2[1]+increaseY) if int(p2[1]+increaseY) <= rows else rows  
    c = int(p1[0]-increaseX) if int(p1[0]-increaseX) >= 0 else 0  
    d = int(p2[0]+ increaseX) if int(p2[0]+ increaseX)  <= cols else cols  
    
    deviation = (d - c) % 4

    if not deviation == 0:
        if c > 4:
            c = c + deviation
        else:
            d = d + deviation
    print (d - c)
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
        minNeighbors=2,     #Count of matches
        minSize=(MIN_SIZE_FACE, MIN_SIZE_FACE),
        maxSize=(MAX_SIZE_FACE,MAX_SIZE_FACE)
    )
    return faces




if __name__ == "__main__":
    if os.path.exists(PATH_HAARCASCADE):
        faceCascade = cv2.CascadeClassifier(PATH_HAARCASCADE)
    else:
        print Bcolors.FAIL + "Error: Haar cascade not found!" + bcolors.ENDC
        sys.exit(1)

    video_capture = cv2.VideoCapture(URL_IPCAMERA)

    window = ()
    prev = time.time()
    while True:
        # Capture frame-by-frame
        ret, frame = video_capture.read()
        if not  ret:
            print Bcolors.FAIL + "Error: Read fram from capture unsuccessful!" + Bcolors.ENDC
            print Bcolors.OKBLUE + "Recommend: Check connection of IP camera (ip addres, network)" + Bcolors.ENDC
            sys.exit(1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        

       # for angle in range(-20,20,10):
        faces = faceDetect(gray, 0)

        for (x, y, w, h) in faces:
            p1 = (x,y)
            p2 = (x+w,y+h)
            window = cutFrame(frame, p1, p2)
            if getCounterThreads() < 20:
                thread.start_new_thread(send_fame_to_iFaceSERVER,(window,))

            #cv2.rectangle(frame, p1, p2, (0, 255, 0), 2)
            cv2.imshow('win', window)

        # Display the resulting frame
        #if getCounterThreads() >= 20:
        #    print bcolors.FAIL + "Error: Sending of data fail! Its too bad." + bcolors.ENDC
        #    print bcolors.OKBLUE + "Recommend: Check connection between sensor and iFace Server." + bcolors.ENDC
        #cv2.putText(frame,str(int(1.0 /(time.time()-prev)))+" FPS",(600,350), cv2.FONT_HERSHEY_SIMPLEX,  0.3 ,(0,255,0),1,cv2.LINE_AA)
        cv2.imshow('Video', frame)
        prev = time.time()
        print getCounterThreads()," threads."
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # When everything is done, release the capture
    video_capture.release()
    cv2.destroyAllWindows()
