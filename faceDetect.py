import cv2
import sys
import thread
import concurrent.futures
import time
import datetime
import math
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
MIN_SIZE_FACE = 60                  #Distance from camera  (Big influence to performace)
MAX_SIZE_FACE = 250                 #Distance from camera  (Big influence to performace)
INTERVAL_UPDATE_WATCHDOG = [0,40]   #[minute , second]
VALIDITY_FRAMES_STREAM = 15
WINDOW_NAME = "Camera"
#######################################################

LAST_RECORD_WATCHDOG = None
persons = []
bannObjects = []
printOKCount = 0
pointPrint = ()


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
        self.p1 = p1
        self.p2 = p2
        self.R = 255
        self.G = 0
        self.B = 0
        self.validity = 10
        self.window = ()
        self.confidence = 0
        self.fakeDetectCount = 0
        self.fakeObject = False
        self.trust = False
        
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
        font = cv2.FONT_HERSHEY_SIMPLEX
        #drow text an value of confidence
        cv2.putText(frame,str(self.confidence)+ status,(self.p1[0] - 15,self.p1[1] - 15), font, 0.8,(self.B, self.G,self.R ),3,cv2.LINE_AA)
        #drow rectangle
        return cv2.rectangle(frame, (self.p1[0],self.p1[1]), (self.p2[0],self.p2[1]), (self.B, self.G,self.R ), 6)
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
        self.validity = 10
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


#-------------------------------------------------------
#            Click event Banning fake objects
#-------------------------------------------------------
def click_and_crop(event, x, y, flags, param):
#Click event function (callback). Find fake object. 
    global bannObjects
    if event == cv2.EVENT_LBUTTONDOWN:
        p1 = (x,y)
        rectangles_dist = filterPersons(p1,100)
        if len(rectangles_dist):
            for bann in bannObjects:
                if calsDistance(rectangles_dist[0][0].p1,bann.p1) < 20 and calsDistance(rectangles_dist[0][0].p2,bann.p2) < 20:
                    return
            clickPrintOK(0,None,rectangles_dist[0][0].p1)
            bannObjects.append(copy.deepcopy(rectangles_dist[0][0]))
            persons.remove(rectangles_dist[0][0])
        print "POCET BANOV :",len(bannObjects)

def clickPrintOK(code, frame, point):
    global printOKCount, pointPrint
    if code == 0:
        printOKCount = 5
        pointPrint = point
    elif code == 1:
        if printOKCount >= 1:
            cv2.putText(frame,"OK",(pointPrint[0],pointPrint[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.8,(0, 255,0 ),3,cv2.LINE_AA)
            printOKCount-=1
########################################################

#-------------------------------------------------------
#            Mini calculate functions
#-------------------------------------------------------            
def calsDistance(p1,p2):
    #calc absolut distance
    a = (p1[0] - p2[0]) 
    b = (p1[1] - p2[1])
    return  math.sqrt(a**2 + b**2)

def filterPersons(p1,limit_distance):
#Calculate distance, sort, filter smaller as limit
    rectangles_dist = []
    map(lambda obj: rectangles_dist.append((obj,calsDistance(p1,obj.getPosition()))), persons)
    rectangles_dist = sorted(rectangles_dist, key=lambda object: object[1])
    rectangles_dist = filter(lambda object: object[1] < limit_distance,rectangles_dist)
    return rectangles_dist
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
        minNeighbors=2,     #Count of matches
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
    global LAST_RECORD_WATCHDOG, persons
    window = ()
    prev = time.time()
    count_validity = VALIDITY_FRAMES_STREAM 
    person_comed = False  
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
    thread.start_new_thread(liveCommunication,(3,))
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
            time.sleep(2)
            video_capture = cv2.VideoCapture(URL_IPCAMERA)
            continue
        #convert to GRAY
        #detect faces
        faces = faceDetect(faceCascade, gray)
        copyGray = gray.copy()
        for (x, y, w, h) in faces:
            p1 = (x,y)
            p2 = (x+w,y+h)

            ##### assignment found face to object or creat new object  #####
            rectangles_dist = filterPersons(p1,120)

            if len(rectangles_dist) > 0:
                rectangles_dist[0][0].setPosition(p1,p2)
                rectangles_dist[0][0].setWindow(cutFrame(gray, p1, p2))
            else:
                isBan = False
                for ban in bannObjects:
                    if calsDistance(ban.p1,p1) < 30 and calsDistance(ban.p2,p2) < 30:
                        isBan = True
                if not isBan:
                    person = Person(p1,p2)
                    person.setWindow(cutFrame(gray, p1, p2))
                    #person.setWindow(gray)
                    persons.append(person)

        #-------------------------------------------------------
        #            Drow rectangle and send person (frame)
        #------------------------------------------------------- 
        for person in persons:
            #if is object still valid
            if person.getValidity() > 0:
                if  person.getTrust():
                    person.drowRectangle(copyGray)
                    #if threads pool is not full and is not timeout
                    if len(workers) < 10 and not isTimeout():
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
                cv2.setMouseCallback(WINDOW_NAME, click_and_crop)
            clickPrintOK(1, copyGray, None)
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


