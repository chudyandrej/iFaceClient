import json
import base64
import requests
import cv2
import time
import os
from threading import Lock
from gui import showNewPerson, showDefault
import urllib2
#-------------------------------------------------------
#                       Settings
#-------------------------------------------------------
URL_server_recognise = "http://192.168.1.157:8080/recognise"
URL_server_check = "http://192.168.1.157:8080/check"
TIMEOUT_BETWEEN_DETECTIONS = 4
TIMEOUT_TO_SEND_REQUEST = 4

########################################################

#-------------------------------------------------------
#                    Global variables
#-------------------------------------------------------
timeout = False
lock = Lock()
threadCount = 0
snapingRun = False
########################################################

#Color output
class Bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

#Function for send frame to iFace server
def send_fame_to_iFaceSERVER(person):
    global threadCount, timeout, lock
    #Counter of threads
    threadCount+=1
    #get cut window frame and code to b64
    frame = person.getWindow()
    encoded_img = code_B64(frame)
    #send request
    req = send_request(encoded_img)
   

    #If server not responding
    if not req == 404:
        #parse responze to JSON
       
        parsed_json = json.loads(req)
     

        #If the detected one person
        if parsed_json['status'] == 2 and parsed_json['detectFaces'] == 1:
            print Bcolors.OKGREEN + "Face detected " + Bcolors.ENDC
            #save confidence to detector object (mass snaping)
            person.setConfidence(int(parsed_json['faceConfidence']))
            try:
                print "Confidence : ",parsed_json['badDesc']
            except:
                print "ach"
            #If not run snaping mode and person been recognised.
            if not snapingRun and parsed_json['recognised'] == True:
                print Bcolors.OKGREEN + "Yes" + Bcolors.ENDC
                #person was detected
                if lock.acquire(False) == True:
                #Lockable block
                    #set timeout (stop create new send thread)
                    timeout = True
                    #show person and name in GUI
                    showNewPerson(decode_B64(parsed_json),parsed_json["name" + str(parsed_json["userId"])],parsed_json["enabled" + str(parsed_json["userId"])])
                    #voice_synthesizer(parsed_json)
                    #timeout between detections
                    time.sleep(TIMEOUT_BETWEEN_DETECTIONS)
                    #show defauld screen in GUI
                    showDefault()
                    #deactivate timeout
                    timeout = False
                    lock.release()
            else:
                print Bcolors.FAIL + "NO" + Bcolors.ENDC
        else:
            print Bcolors.WARNING + "Face not detected " + Bcolors.ENDC
    #end send thread
    threadCount-=1

#forewer comunication whit server (alive client and set snaping mode)
def liveCommunication(frequency):
    global snapingRun
    while True:
        time.sleep(frequency)
        try:
            req = urllib2.Request(URL_server_check, data="camraID=1")
            response = urllib2.urlopen(req,timeout=TIMEOUT_TO_SEND_REQUEST)
        except:
            print Bcolors.FAIL + "Sever not responding" + Bcolors.ENDC
            print "NO"
            continue
        #parse responze to JSON
        parsed_json = json.loads(response.read())
        if parsed_json['status'] == 2:
            snapingRun  =  parsed_json['massEnroll']
       
        print "OK"
        
          
        
#Function to code frame to jpg and B64
def code_B64(frame):
    img_str = cv2.imencode('.jpg', frame)[1].tostring()
    #encodestring
    encoded_img = base64.encodestring(img_str)
    #some bullshit (server requires)
    encoded_img = encoded_img.replace('+', '-')
    encoded_img = encoded_img.replace('/', '_')
    encoded_img = encoded_img.replace('=', '.')
    return encoded_img

#Function to decode B64 to jpg
def decode_B64(parsed_json):
    encoded_img = parsed_json["image" + str(parsed_json["id"])]
    #some bullshit (server requires)
    encoded_img = encoded_img.replace('-', '+')
    encoded_img = encoded_img.replace('_', '/')
    encoded_img = encoded_img.replace('.', '=')
    #decodestring
    decode_img = base64.decodestring(encoded_img)
    return decode_img
   
#Voice synthesizer
def voice_synthesizer(parsed_json):
    #get name
    name = parsed_json["name" + str(parsed_json["userId"])]
    #creat command
    command = "espeak -v sk --stdout '%s' | aplay" % (name)
    #apply command
    os.system(command.encode('UTF-8'))
  
#send request
def send_request(encoded_img):
    try:
        req = urllib2.Request(URL_server_recognise, data="image="+encoded_img+"&camraID=1&getUserInfo=1")
        response = urllib2.urlopen(req,timeout=TIMEOUT_TO_SEND_REQUEST)
        return response.read()
    except:
        print Bcolors.FAIL + "Sever not responding" + Bcolors.ENDC
        return 404

def getCounterThreads():
    return threadCount

def isTimeout():
    return timeout

def getSnapingRun():
    return snapingRun