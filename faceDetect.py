import cv2
import sys
import thread
import concurrent.futures
import time
import datetime
import math
import random
import os.path
import copy
from concurrent import futures

from gui import getConfig, offConfig
from communication import send_fame_to_iFaceSERVER,getCounterThreads,isTimeout, liveCommunication, getSnapingRun

#-------------------------------------------------------
#                       Settings
#-------------------------------------------------------
URL_IPCAMERA = "rtsp://admin:Admin12345@192.168.1.106/jpeg/ch2/sub/av_stream"
PATH_HAARCASCADE = "haarcascade_frontalface_alt2.xml"
MIN_SIZE_FACE = 55                  #Distance from camera  (Big influence to performace)
MAX_SIZE_FACE = 170                 #Distance from camera  (Big influence to performace)
MAX_DISTANCE_OBJ_FACE = 100
INTERVAL_UPDATE_WATCHDOG = [0,40]   #[minute , second]
WINDOW_NAME = "Camera"
TIME_EXPIRE_FACEOBJECT = [0,8]  #[minute , second]
#######################################################

LAST_RECORD_WATCHDOG = None
persons = []

printOKCount = 0
pointPrint = ()
PERSONID = random.randrange(0, 10000, 2) 


class Bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


#Person object 
class Person:
    #Constructor
    def __init__(self, p1, p2):

        global PERSONID
        PERSONID+=1
        if PERSONID > 10000:
            PERSONID = 0
        self.idRectangle = PERSONID
        self.timestamp = datetime.datetime.now()
        self.p1 = p1
        self.p2 = p2
        self.R = 255
        self.G = 0
        self.B = 0
        self.validity = 5
        self.window = ()
        self.confidence = 0
        self.fakeDetectCount = 0
        self.fakeObject = False
        self.trust = False
        self.recognised = False
        
    #Drow
    def drowRectangle(self,frame):
        #Load text
        if self.confidence < 1000:
            status = " Bad"
        elif self.confidence > 1000 and self.confidence < 3000:
            status = " Good"
        elif self.confidence > 3000 and self.confidence < 4000:
            status = " Ecelent"
        elif self.confidence > 4000:
            status = " The best"
        self.validity-=1
        if getSnapingRun() or getConfig(): 
            font = cv2.FONT_HERSHEY_SIMPLEX
            #drow text an value of confidence
            cv2.putText(frame,str(self.confidence)+ status,(self.p1[0] - 15,self.p1[1] - 15), font, 0.8,(self.B, self.G,self.R ),3,cv2.LINE_AA)
            #drow rectangle
            cv2.rectangle(frame, (self.p1[0],self.p1[1]), (self.p2[0],self.p2[1]), (self.B, self.G,self.R ), 6)
            return frame

    #Set new confidence
    def setConfidence(self, confidence):
        #set color of rectangle  and better confidence
        if confidence > self.confidence:
            self.confidence = confidence
        self.n = 100 - int(self.confidence / 50) 
        if self.n > 100:
            self.n = 100
        self.R = (255 * self.n) / 100
        self.G = (255 * (100 - self.n)) / 100 
        self.B = 0

    def setPosition(self, p1, p2):
        self.trust = True
        self.p1 = p1
        self.p2 = p2
        self.validity = 5

    def personRecognised(self):
        self.recognised = True

    def getPosition(self):
        return self.p1 

    def setWindow(self,window):
        self.window = window

    def getWindow(self):
        return self.window

    def getValidity(self):
        return self.validity

    def getTrust(self):
        return self.trust

    def isRecognised(self):
        return self.recognised

    def getIdRectangle(self):
        return self.idRectangle

    def isExpire(self):
        return (datetime.datetime.now() - self.timestamp) > datetime.timedelta(TIME_EXPIRE_FACEOBJECT[0], TIME_EXPIRE_FACEOBJECT[1], 0)




#-------------------------------------------------------
#            Mini calculate functions
#-------------------------------------------------------            
def calsDistance(p1,p2):
    #calc absolut distance
    a = (p1[0] - p2[0]) 
    b = (p1[1] - p2[1])
    return  math.sqrt(a**2 + b**2)

def findBestObject(p1):
#Calculate distance, sort, filter smaller as limit
    rectangles_dist = []
    map(lambda obj: rectangles_dist.append((obj,calsDistance(p1,obj.getPosition()))), persons)
    rectangles_dist = sorted(rectangles_dist, key=lambda object: object[1])

    if len(rectangles_dist) >= 1:
        best_object = rectangles_dist[0]
        if best_object[1] < MAX_DISTANCE_OBJ_FACE:
            return best_object[0]
    return None
#########################################################

#-------------------------------------------------------
#            Finde and cut face from frame
#------------------------------------------------------- 
#Creat window from -> frame - opencvFrame p - point (x,y)
def cutFrame(frame, p1, p2):
    #set size bonus edges -> %
    increaseX = p2[0] * 0.1     
    increaseY = p2[1] * 0.2
    #size of frame
    rows = len(frame)
    cols = len (frame[1])
    #trim edges
    a = int(p1[1]-increaseY) if int(p1[1]-increaseY) >= 0 else 0  
    b = int(p2[1]+increaseY) if int(p2[1]+increaseY) <= rows else rows  
    c = int(p1[0]-increaseX) if int(p1[0]-increaseX) >= 0 else 0  
    d = int(p2[0]+ increaseX) if int(p2[0]+ increaseX)  <= cols else cols  
    #width of window must be divisible 4
    residue = (d - c) % 4
    if not residue == 0:
        if c > 4:
            c = c + residue
        else:
            d = d + residue
    #cut frame
    return frame[a:b,c:d]

#Detect faces in frame-> faceCascade - loaded harr. cascade, gray - frame in grayscale (black white)
def faceDetect(faceCascade, gray):
    faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=3,     #Count of matches
        minSize=(MIN_SIZE_FACE, MIN_SIZE_FACE),
        maxSize=(MAX_SIZE_FACE,MAX_SIZE_FACE)
    )
    #return list of faces
    return faces
########################################################

#-------------------------------------------------------
#            Watch dog message system
#------------------------------------------------------- 
#update shared file for watch dog (program is running)
def updateWatchDogFile(watchdog_name):
    global LAST_RECORD_WATCHDOG
    #if it's time to update
    if (datetime.datetime.now() - LAST_RECORD_WATCHDOG) >= datetime.timedelta(INTERVAL_UPDATE_WATCHDOG[0], INTERVAL_UPDATE_WATCHDOG[1], 0):
        LAST_RECORD_WATCHDOG= datetime.datetime.now()
        fo = open(watchdog_name, "wb")
        fo.write( "modify");
        fo.close()
########################################################

#Main function of face detection 
def runFaceDetect(watchdog_name):
#########    init values    ##############
    print PERSONID
    global LAST_RECORD_WATCHDOG, persons
    window = ()
    prev = time.time()
    LAST_RECORD_WATCHDOG = datetime.datetime.now() 
    video_capture = cv2.VideoCapture(URL_IPCAMERA)      #Init camera stream argument -> URL / video 0 
    executor = futures.ThreadPoolExecutor(max_workers=10)
    workers = []
    oldConfig_var = getConfig()
#------------------------------------------

#######   load face cascade    ###########
    if os.path.exists(PATH_HAARCASCADE):            #if cascade exit
        faceCascade = cv2.CascadeClassifier(PATH_HAARCASCADE)       #load cascade
    else:
        print Bcolors.FAIL + "Error: Haar cascade not found!" + bcolors.ENDC
        sys.exit(1)
#----------------------------------------
    #run forewer live communication
    thread.start_new_thread(liveCommunication,(10,))
    #forewer main run (camera processing)
    while True:
        #edit watch dog file (program is alive)
        updateWatchDogFile(watchdog_name)

        #read new frame
        ret, gray = video_capture.read()   #There program will be freez when camera will be disconect.
        #read a new frame was unsucessful
        if not  ret:
            #Print error wait 2 s and try read again 
            print Bcolors.FAIL + "Error: Read fram from capture unsuccessful!" + Bcolors.ENDC
            print Bcolors.OKBLUE + "Recommend: Check connection of IP camera (ip addres, network)" + Bcolors.ENDC
            time.sleep(5)
            video_capture = cv2.VideoCapture(URL_IPCAMERA)
            continue

        persons = filter(lambda person: not person.isExpire(), persons)
        #detect faces
        faces = faceDetect(faceCascade, gray)
        copyGray = gray.copy()
        for (x, y, w, h) in faces:
            p1 = (x,y)
            p2 = (x+w,y+h)

            #calc distance between face and object. Filter 
            bestObject = findBestObject(p1)
            if not bestObject == None:
                bestObject.setPosition(p1,p2)
                bestObject.setWindow(cutFrame(gray, p1, p2))
            else:
                person = Person(p1,p2)
                person.setWindow(cutFrame(gray, p1, p2))
                persons.append(person)

        #-------------------------------------------------------
        #         Drow rectangle and send person (frame)
        #------------------------------------------------------- 
        for person in persons:
            #if is object still valid
            if person.getValidity() > 0:
                if person.getTrust():
                    person.drowRectangle(copyGray)
                    #if threads pool is not full and is not timeout
                    if len(workers) < 10 and not isTimeout() and not person.isRecognised():
                        #send request
                        workers.append(executor.submit(send_fame_to_iFaceSERVER, person))
            else:
                persons.remove(person)
        ########################################################
        #Delete done instances of worker pool
        workers = filter(lambda worker:not worker.done(), workers)
    
        #if smaning mode running
        if  getSnapingRun() or getConfig(): 
            if not (getConfig() or getSnapingRun())  == oldConfig_var:
                cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
                #cv2.setMouseCallback(WINDOW_NAME, click_and_crop)
            cv2.imshow(WINDOW_NAME, copyGray)    
        else:
            if not  getConfig() == oldConfig_var:
                cv2.destroyWindow(WINDOW_NAME)

        oldConfig_var = getConfig() or getSnapingRun()
        #calculate FPS
        fps = int(1.0 /(time.time()-prev))
        prev = time.time()
        print fps
        print "Activ workers ", len(workers)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            offConfig()
    # When everything is done, release the capture
    video_capture.release()
    cv2.destroyAllWindows()


