import cv2
import sys
import thread
import concurrent.futures
import time
import datetime
import os.path

from communication import send_fame_to_iFaceSERVER,getCounterThreads,isTimeout




LAST_RECORD_WATCHDOG = None
WATCHDOG_NAME = None
MIN_SIZE_FACE = 60      #Distance from camera  (Big influence to performace)
MAX_SIZE_FACE = 250     #Distance from camera  (Big influence to performace)




#Global variables


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



def faceDetect(faceCascade, gray, deg):
  #  rotat_gray = rotate(gray, deg)
    rotat_gray = gray
    faces = faceCascade.detectMultiScale(
        rotat_gray,
        scaleFactor=1.1,
        minNeighbors=3,     #Count of matches
        minSize=(MIN_SIZE_FACE, MIN_SIZE_FACE),
        maxSize=(MAX_SIZE_FACE,MAX_SIZE_FACE)
    )
    return faces

def updateWatchDogFile():
    global LAST_RECORD_WATCHDOG
    if (datetime.datetime.now() - LAST_RECORD_WATCHDOG) >= datetime.timedelta(0, 40, 0):
        LAST_RECORD_WATCHDOG= datetime.datetime.now()
        fo = open(WATCHDOG_NAME, "wb")
        fo.write( "modify");
        fo.close()


def runFaceDetect(file_name):

###### init values ######
    url_ipcamera = "rtsp://admin:Admin12345@192.168.1.106/jpeg/ch2/sub/av_stream"
    path_haarcascade = "./haarcascade_frontalface_alt2.xml"
    window = ()
    prev = time.time()
#########################---------------------------------------

##### init watchdog #####
    global LAST_RECORD_WATCHDOG, WATCHDOG_NAME
    WATCHDOG_NAME = file_name
    LAST_RECORD_WATCHDOG= datetime.datetime.now()
    fo = open(WATCHDOG_NAME, "wb")
    fo.write( "modify");
    fo.close()
#########################---------------------------------------

## init camera capture ##
    video_capture = cv2.VideoCapture(url_ipcamera)
#########################---------------------------------------

## load face cascade ###
    if os.path.exists(path_haarcascade):
        faceCascade = cv2.CascadeClassifier(path_haarcascade)
    else:
        print Bcolors.FAIL + "Error: Haar cascade not found!" + bcolors.ENDC
        sys.exit(1)
#########################---------------------------------------
     
    while True:
       
        updateWatchDogFile()

        ret, frame = video_capture.read()   #There program will be freez when camera will be disconect.
        if not  ret:
            print Bcolors.FAIL + "Error: Read fram from capture unsuccessful!" + Bcolors.ENDC
            print Bcolors.OKBLUE + "Recommend: Check connection of IP camera (ip addres, network)" + Bcolors.ENDC
            time.sleep(1)
            video_capture = cv2.VideoCapture(URL_IPCAMERA)
            continue
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
       
        faces = faceDetect(faceCascade, gray, 0)
        for (x, y, w, h) in faces:
            p1 = (x,y)
            p2 = (x+w,y+h)
            window = cutFrame(frame, p1, p2)
            print isTimeout()
            if getCounterThreads() < 20 and not isTimeout():
                thread.start_new_thread(send_fame_to_iFaceSERVER,(window,))
           
            #cv2.imshow('win', window)

        #cv2.imshow('Camera', frame)
        cv2.putText(frame,str(int(1.0 /(time.time()-prev)))+" FPS",(600,350), cv2.FONT_HERSHEY_SIMPLEX,  0.3 ,(0,255,0),1,cv2.LINE_AA)
        prev = time.time()
        print "threds: ",getCounterThreads()
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # When everything is done, release the capture
    video_capture.release()
    cv2.destroyAllWindows()

