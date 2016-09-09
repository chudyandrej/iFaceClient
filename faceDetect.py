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
from communication import send_fame_to_iFaceSERVER,isTimeout, liveCommunication, getEnrollRun

#-------------------------------------------------------
#                       Settings
#-------------------------------------------------------
MAX_DISTANCE_OBJ_FACE = 100
INTERVAL_UPDATE_WATCHDOG = 2   #minutes
TIME_EXPIRE_FACEOBJECT = 15  #second
#######################################################

LAST_RECORD_WATCHDOG = None
OBJECTS = []

cliced = False
MIN_SIZE_WINDOW = 30
PERSONID = random.randrange(0, 10000, 2) 


#object for color output in terminal
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
        self.validity = 3
        self.window = ()
        self.confidence = 0
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
        if getEnrollRun() or getView(): 
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
    map(lambda obj: rectangles_dist.append((obj,calsDistance(p1,obj.getPosition()))), OBJECTS)
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
    a = int(p1[1]-increaseY) if int(p1[1]-increaseY) >= 0 else 0  
    b = int(p2[1]+increaseY) if int(p2[1]+increaseY) <= height else height  
    c = int(p1[0]-increaseX) if int(p1[0]-increaseX) >= 0 else 0  
    d = int(p2[0]+ increaseX) if int(p2[0]+ increaseX)  <= width else width  
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
#-------------------------------------------------------
#                    Face detector
#-------------------------------------------------------
#Detect faces in frame-> faceCascade - loaded harr. cascade, gray - frame in grayscale (black white), It is multi thread function!!!
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



def drawActivePart(frame, points):

    font = cv2.FONT_HERSHEY_SIMPLEX
    if len(points) == 1:                #if existing only one point
        cv2.putText(frame,'o',(points[0][0]-7,points[0][1]+7), font,0.8,(0,0,255),7,cv2.LINE_AA)    #show point on frame
    elif len(points) == 2:              #if existing two points 
        cv2.putText(frame,'o',(points[0][0]-7,points[0][1]+7), font,0.8,(0,0,255),7,cv2.LINE_AA)    #show point
        cv2.putText(frame,'o',(points[1][0]-7,points[1][1]+7),font, 0.8,(0,100,255),7,cv2.LINE_AA)  #show point
        cv2.rectangle(frame, points[0], points[1], (0, 255, 0), 2)          #draw rectangle over points
        

def changeConfigFile(regex, newValue):
    file_ = open("config.json", "r")    #load config file
    config_str = file_.read();          #read file
    file_.close()
    file_ = open("config.json", "w")
    actualizedConfig = re.sub(regex, newValue ,config_str)      #replace settings of window
    file_.write(actualizedConfig)       #write a new settings
    file_.close()

#Main function of face detection 
def runFaceDetect(watchdog_name, config, logger):
    global LAST_RECORD_WATCHDOG, OBJECTS
#--------------------------------------------
#               init values    
#--------------------------------------------
    prev = time.time()      #save time because calculate FPS
    LAST_RECORD_WATCHDOG = datetime.datetime.now() 
    video_capture = cv2.VideoCapture(config['URL_CAMERA_STREAM'])      #Init camera stream argument -> URL / video 0 
    executor = futures.ThreadPoolExecutor(max_workers=config['WORKERS_count'])  #Create pool of workers 

    points = []                                                 #two points in settings mode   
    strPoints = config['FRAME_active_part'].split(' x ')        #load points from config file 
    points.append(make_tuple(strPoints[0]))                     #save loaded point
    points.append(make_tuple(strPoints[1]))                     #save loaded point
    points_backup = points                                      #create backup of points

    oldConfig_var = getView()           #old status of view window (on / off)
    oldSettings_var = getSettings()     #old status of settings window (on / off)

#--------------------------------------------
#          declarations variables    
#--------------------------------------------
    workers = []        #array of workers
    load_size = False     #if size of capture was loaded
    width = None            #width of frame
    height = None           #height of frame
       

#--------------------------------------------
#            load face cascade    
#--------------------------------------------
    if os.path.exists(config['PATH_HAARCASCADE']):            #if cascade exit
        faceCascade = cv2.CascadeClassifier(config['PATH_HAARCASCADE'])       #load cascade
    else:
        print Bcolors.FAIL + "Error: Haar cascade not found!" + bcolors.ENDC
        logger.error("Haar cascade not found!")
        sys.exit(1)

#--------------------------------------------
#         start asynchronous thread    
#--------------------------------------------
    thread.start_new_thread(liveCommunication,(config['URL_server_check'],config['TIMEOUT_live_mes'], config['TIMEOUT_request'], logger))
  
#--------------------------------------------
#         mani loop of program    
#--------------------------------------------
    while True:
        try: 
            updateWatchDogFile(watchdog_name)           #edit watch dog file (program is alive)
            ret, gray = video_capture.read()            #read new frame    #There program will be freez when camera will be disconect.
               
            if not  ret:            #read a new frame was unsucessful
                #Print error wait 2 s and try read again 
                print Bcolors.FAIL + "Error: Read fram from capture unsuccessful!" + Bcolors.ENDC
                print Bcolors.OKBLUE + "Recommend: Check connection of IP camera (ip addres, network)" + Bcolors.ENDC
                logger.error("Read fram from capture unsuccessful!")
                cameraError()           #show warning in GUI
                video_capture = cv2.VideoCapture(config['URL_CAMERA_STREAM'])       #try set new capture
                continue

            if not load_size:       #load size of frame one time
                loaded_size = True
                width = len(gray[1])
                height = len(gray) 
           
            settingsView = gray.copy()      #create copy of gray frame
            gray = gray[min(points,key=lambda point:point[1])[1]:max(points,key=lambda point:point[1])[1],
                        min(points,key=lambda point:point[0])[0]:max(points,key=lambda point:point[0])[0]]    #cut frame
            copyGray = gray.copy()      #copy of cute frame because of draw rectangle
            
            if getSettings():       #if settings is active, draw active part of frame
                drawActivePart(settingsView, points)
                
            if not getEnrollRun():      #if not enroll mode filter of expite objectis is active
                OBJECTS = filter(lambda person: not person.isExpire(), OBJECTS)

            faces = faceDetect(faceCascade, gray,config['SCALE_factor'],config['MIN_neighbors'], config['MIN_size_face'], config['MAX_size_face'])  #detect faces 
              
            #--------------------------------------------
            #  Program must find every face a new object 
            #--------------------------------------------
            for (x, y, w, h) in faces:
                p1 = (x,y)          #save point 1 of face
                p2 = (x+w,y+h)      #save point 2 of face

                #calc distance between face and object. Filter 
                bestObject = findBestObject(p1)
                cutedFrame = cutFrame(gray, p1, p2, width, height)      #cut face form frame
                if not cutedFrame == None:          #If cut of face be successful
                    if len(cutedFrame) == 0:
                         logger.error("SAVE CUT FRAME TO OBJ is 0")
                    if not bestObject == None:      #If exist match any object update or create new
                        bestObject.setPosition(p1,p2)
                        bestObject.setWindow(cutedFrame.copy())
                    else:
                        newObject = Person(p1,p2)           #create new
                        newObject.setWindow(cutedFrame.copy())
                        OBJECTS.append(newObject)

            #-------------------------------------------------------
            #         Drow rectangle and send object (frame)
            #------------------------------------------------------- 
            for obj in OBJECTS:
                #if is object still valid
                if obj.getValidity() > 0:
                    if obj.getTrust():
                        obj.drowRectangle(copyGray)         #use object drow rectangle and decrement vakidity flag

                        if len(workers) < config['WORKERS_count'] and not isTimeout() and not obj.isRecognised():       #if worked pool in not full and not timeout and not object recognised.
                            #send request
                            workers.append(executor.submit(send_fame_to_iFaceSERVER, obj,config, logger))           #send obj to recognised
                else:
                    OBJECTS.remove(obj)
            ########################################################
            #Delete done instances of worker pool
            workers = filter(lambda worker:not worker.done(), workers)      #remove done jobs
            

            #if smaning mode running
            if  getEnrollRun() or getView():            #if switch on enroll or view flag 
                if not (getView() or getEnrollRun())  == oldConfig_var:     #if view status be switch on right now (first view)
                    cv2.namedWindow(config['VIEW_window_name'], 3)   #Init window
                    cv2.moveWindow(config['VIEW_window_name'], config['VIEW_window_x_pos'], config['VIEW_window_y_pos'])
                cv2.imshow(config['VIEW_window_name'], copyGray)     #show frame in window
                
            else:
                if not  getView() == oldConfig_var:         #if View mode was shut down right now 
                    cv2.destroyWindow(config['VIEW_window_name'])    #destroy view window

            if not oldSettings_var and  getSettings():     #if settings status be switch on right now (first view) 
                cv2.namedWindow(config['SETTINGS_window_name'], 3)      #init window
                cv2.moveWindow(config['SETTINGS_window_name'], config['SETTINGS_window_x_pos'], config['SETTINGS_window_y_pos'])             
                cv2.setMouseCallback(config['SETTINGS_window_name'], click_and_crop , param=(width,height,points))      #set window listener
                points_backup = copy.copy(points)   #and make copy of actual points of active frame

                
            if oldSettings_var and  not getSettings():   #if settings mode was shut down right now 
                cv2.destroyWindow(config['SETTINGS_window_name'])              #destroy settings window
                if len (points) == 2 and not config['FRAME_active_part'] == str(points[0])+' x '+str(points[1]):    #save select active area to congig
                    changeConfigFile('(?<="FRAME_active_part")\s*:\s*"[0-9,x() ]+"', ' : "'+str(points[0])+' x '+str(points[1])+'"')
        
            if getSettings():       #show frame in window
                cv2.imshow(config['SETTINGS_window_name'], settingsView)

            #make backup of flags
            oldSettings_var = getSettings()
            oldConfig_var = getView() or getEnrollRun()
            #calculate FPS
            fps = int(1.0 /(time.time()-prev))
            prev = time.time()
            
            #print "Activ workers ", len(workers)
            #kays listners
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
        except Exception,e:
            logger.error("FATAL ERROR !!! IN MAIN LOOP | Type: "+str(type(e))+" Description: "+str(e))
            
    # When everything is done, release the capture
    video_capture.release()
    cv2.destroyAllWindows()


