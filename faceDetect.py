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
import re
import numpy as np
from concurrent import futures
from ast import literal_eval as make_tuple

from gui import getView, viewer, offViewer, cameraError, getSettings, settings,offSettings
from communication import send_fame_to_iFaceSERVER,isTimeout, liveCommunication, getenrollRun

#-------------------------------------------------------
#                       Settings
#-------------------------------------------------------
MAX_DISTANCE_OBJ_FACE = 100
INTERVAL_UPDATE_WATCHDOG = 2   #minutes
TIME_EXPIRE_FACEOBJECT = 10  #second
#######################################################

LAST_RECORD_WATCHDOG = None
persons = []

cliced = False
MIN_SIZE_WINDOW = 30
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
        if self.confidence <= 1000:
            status = " Bad"
        elif self.confidence > 1000 and self.confidence <= 3000:
            status = " Good"
        elif self.confidence > 3000 and self.confidence <= 4000:
            status = " Ecelent"
        elif self.confidence > 4000:
            status = " The best"
        self.validity-=1
        if getenrollRun() or getView(): 
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
        return (datetime.datetime.now() - self.timestamp) > datetime.timedelta(seconds=TIME_EXPIRE_FACEOBJECT)


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
def cutFrame(frame, p1, p2,width, height):
    #set size bonus edges -> %
    increaseX = p2[0] * 0.1    
    increaseY = p2[1] * 0.1
    #size of frame

    #trim edges
    a = int(p1[1]-increaseY*2) if int(p1[1]-increaseY) >= 0 else 0  
    b = int(p2[1]+increaseY) if int(p2[1]+increaseY) <= width else width  
    c = int(p1[0]-increaseX) if int(p1[0]-increaseX) >= 0 else 0  
    d = int(p2[0]+ increaseX) if int(p2[0]+ increaseX)  <= height else height  
    #width of window must be divisible 4

    if (b-a) > MIN_SIZE_WINDOW and (d-c) > MIN_SIZE_WINDOW: 
        residue = (d - c) % 4
        if not residue == 0:
            if c > 4:
                c = c + residue
            else:
                d = d + residue
        #cut frame
        result = frame[a:b,c:d]
        #cv2.imshow("Face", result)
        return result
    else:
        return None

#Detect faces in frame-> faceCascade - loaded harr. cascade, gray - frame in grayscale (black white)
def faceDetect(faceCascade, gray,scale,minNeig, min_size, max_size):
    faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=scale,
        minNeighbors=minNeig,     #Count of matches
        minSize=(min_size, min_size)
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
    if (datetime.datetime.now() - LAST_RECORD_WATCHDOG) >= datetime.timedelta(minutes=INTERVAL_UPDATE_WATCHDOG):
        LAST_RECORD_WATCHDOG= datetime.datetime.now()
        fo = open(watchdog_name, "wb")
        fo.write( "modify");
        fo.close()
########################################################

def click_and_crop(event, x, y, flags, param):
    # grab references to the global variables
    global cliced
    points = param[2]
  
    if event == cv2.EVENT_LBUTTONDOWN or (cliced and event == cv2.EVENT_MOUSEMOVE):
        if x <= param[1] and y <= param[0] and  x >= 0 and  y >= 0:
            cliced = True
            d0 = calsDistance(points[0],[x,y])
            d1 = calsDistance(points[1],[x,y])
            if d0 < d1:
                if abs(points[1][0] - x) > MIN_SIZE_WINDOW and abs(points[1][1] - y) > MIN_SIZE_WINDOW:
                    points[0] = (x,y)
            else:
                if abs(points[0][0] - x) > MIN_SIZE_WINDOW and abs(points[0][1] - y) > MIN_SIZE_WINDOW:
                    points[1] = (x,y)

    elif event == cv2.EVENT_LBUTTONUP:
        cliced = False



def showActivePart(frame, points):

    font = cv2.FONT_HERSHEY_SIMPLEX
    if len(points) == 1:
        cv2.putText(frame,'o',(points[0][0]-7,points[0][1]+7), font,0.8,(0,0,255),7,cv2.LINE_AA)
    elif len(points) == 2:
        cv2.putText(frame,'o',(points[0][0]-7,points[0][1]+7), font,0.8,(0,0,255),7,cv2.LINE_AA)
        cv2.putText(frame,'o',(points[1][0]-7,points[1][1]+7),font, 0.8,(0,100,255),7,cv2.LINE_AA)
        cv2.rectangle(frame, points[0], points[1], (0, 255, 0), 2)
        

def changeConfigFile(regex, newValue):
    file_ = open("config.json", "r")
    config_str = file_.read();
    file_.close()
    file_ = open("config.json", "w")
    actualizedConfig = re.sub(regex, newValue ,config_str)
    file_.write(actualizedConfig)
    file_.close()

#Main function of face detection 
def runFaceDetect(watchdog_name, config, logger):
#########    init values    ##############
    global LAST_RECORD_WATCHDOG, persons
    window = ()
    prev = time.time()
    LAST_RECORD_WATCHDOG = datetime.datetime.now() 
    video_capture = cv2.VideoCapture(config['URL_CAMERA_STREAM'])      #Init camera stream argument -> URL / video 0 
    executor = futures.ThreadPoolExecutor(max_workers=config['WORKERS_count'])
    workers = []
    oldConfig_var = getView()
    oldSettings_var = getSettings()
  
    loaded_size = False
    width = None
    height = None
    points = []
    points_backup = []
       
#------------------------------------------

#######   load face cascade    ###########
    if os.path.exists(config['PATH_HAARCASCADE']):            #if cascade exit
        faceCascade = cv2.CascadeClassifier(config['PATH_HAARCASCADE'])       #load cascade
    else:
        print Bcolors.FAIL + "Error: Haar cascade not found!" + bcolors.ENDC
        logger.error("Haar cascade not found!")
        sys.exit(1)
#----------------------------------------
    #run forewer live communication
    thread.start_new_thread(liveCommunication,(config['URL_server_check'],config['TIMEOUT_live_mes'], config['TIMEOUT_request']))
    
    strPoints = config['FRAME_active_part'].split(' x ')
    points.append(make_tuple(strPoints[0]))
    points.append(make_tuple(strPoints[1]))

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
            logger.error("Read fram from capture unsuccessful!")
            cameraError()
            video_capture = cv2.VideoCapture(config['URL_CAMERA_STREAM'])
            continue  
        if not loaded_size:
            loaded_size = True
            width = len(gray)
            height = len(gray[1]) 
       
        settingsView = gray.copy()
        gray = gray[min(points,key=lambda point:point[1])[1]:max(points,key=lambda point:point[1])[1],min(points,key=lambda point:point[0])[0]:max(points,key=lambda point:point[0])[0]]
        copyGray = gray.copy()
        showActivePart(settingsView, points)
            
        
        if not getenrollRun():
            persons = filter(lambda person: not person.isExpire(), persons)
        #detect faces

        faces = faceDetect(faceCascade, gray,config['SCALE_factor'],config['MIN_neighbors'], config['MIN_size_face'], config['MAX_size_face'] )
        
        for (x, y, w, h) in faces:
            p1 = (x,y)
            p2 = (x+w,y+h)

            #calc distance between face and object. Filter 
            bestObject = findBestObject(p1)
            cutedFrame = cutFrame(gray, p1, p2, width, height)
            if not cutedFrame == None:
                if not bestObject == None:
                    bestObject.setPosition(p1,p2)
                    bestObject.setWindow(cutedFrame)
                else:
                    person = Person(p1,p2)
                    person.setWindow(cutedFrame)
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

                    if len(workers) < config['WORKERS_count'] and not isTimeout() and not person.isRecognised():
                        #send request
                        workers.append(executor.submit(send_fame_to_iFaceSERVER, person,config, logger))
            else:
                persons.remove(person)
        ########################################################
        #Delete done instances of worker pool
        workers = filter(lambda worker:not worker.done(), workers)
        

        #if smaning mode running
        if  getenrollRun() or getView(): 
            if not (getView() or getenrollRun())  == oldConfig_var:
                cv2.namedWindow(config['WINDOW_name'], 3)
            cv2.imshow(config['WINDOW_name'], copyGray)
            
        else:
            if not  getView() == oldConfig_var:
                cv2.destroyWindow(config['WINDOW_name'])

        if not oldSettings_var and  getSettings():
            cv2.namedWindow('Settings', 3)
            cv2.setMouseCallback('Settings', click_and_crop , param=(width,height,points))
            points_backup = copy.copy(points)

            
        if oldSettings_var and  not getSettings():
            cv2.destroyWindow('Settings')
            if len (points) == 2 and not config['FRAME_active_part'] == str(points[0])+' x '+str(points[1]):
                changeConfigFile('(?<="FRAME_active_part")\s*:\s*"[0-9,x() ]+"', ' : "'+str(points[0])+' x '+str(points[1])+'"')
    
        if getSettings():
            cv2.imshow('Settings', settingsView)

        oldSettings_var = getSettings()
        oldConfig_var = getView() or getenrollRun()
        #calculate FPS
        fps = int(1.0 /(time.time()-prev))
        prev = time.time()
        #print "FPS: ", fps
        #print "Activ workers ", len(workers)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('w'):
            viewer(None)
        elif key == ord('s'):
            settings(None)

        elif key == 27:
            offViewer()
            offSettings()
            oldSettings_var = False
            cv2.destroyWindow('Settings')
            points = points_backup
            


    # When everything is done, release the capture
    video_capture.release()
    cv2.destroyAllWindows()


