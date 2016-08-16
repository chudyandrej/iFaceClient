import json
import base64
import requests
import cv2
import time
import datetime
import os
from threading import Lock
import threading
from gui import showNewPerson, showDefault
import urllib2

#-------------------------------------------------------
#                    Global variables
#-------------------------------------------------------
timeout = False
lock = Lock()
listLock = Lock()
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
def send_fame_to_iFaceSERVER(person,config):
    global threadCount, timeout, lock
    #Counter of threads
    threadCount+=1
    #get cut window frame and code to b64
    frame = person.getWindow()
    encoded_img = code_B64(frame)
    #send request
    req = send_request(config['URL_server_recognise'],config['cameraId'],config['transType'],encoded_img, person.getIdRectangle(),config['TIMEOUT_request'])
    #If server not responding
    if not req == 404:
        #parse responze to JSON
        parsed_json = json.loads(req)
        
        #If the detected one person
        if parsed_json['status'] == 2:
            person.setConfidence(int(parsed_json['faceConfidence']))
            if not snapingRun:
                if parsed_json['msgStatus'] == 3:
                    print Bcolors.OKGREEN + "Yes" + Bcolors.ENDC                   
                    person.personRecognised()
                   
                    #person was detected
                    lock.acquire(True)
                    #Lockable block
                    #set timeout (stop create new send thread)
                    timeout = True
                    #show person and name in GUI
                    showNewPerson(decode_B64(parsed_json),parsed_json["name" + str(parsed_json["userId"])],parsed_json["enabled" + str(parsed_json["userId"])])
                    #voice_synthesizer(parsed_json)
                    #timeout between detections
                    time.sleep(config['TIMEOUT_between_display'])
                    #show defauld screen in GUI
                    showDefault()
                    #deactivate timeout
                    timeout = False
                    lock.release()

                elif parsed_json['msgStatus'] == 2:
                    if  lock.acquire(False) == True:
                        print "BEGGER"
                        #Lockable block
                        #set timeout (stop create new send thread)
                        timeout = True
                        showNewPerson(cv2.imencode('.jpg', person.getWindow())[1].tostring(),'',None)
                        time.sleep(config['TIMEOUT_between_display'])
                        showDefault()
                        timeout = False
                        lock.release()
                elif parsed_json['msgStatus'] == -2:
                    person.personRecognised()
                    print Bcolors.FAIL + "Person Banned" + Bcolors.ENDC

                elif parsed_json['msgStatus'] == 1:
                    print Bcolors.WARNING + "Recognise unsuccessful" + Bcolors.ENDC
                elif parsed_json['msgStatus'] == 0:
                    print Bcolors.FAIL + "Face not detected " + Bcolors.ENDC
                else:
                    print Bcolors.WARNING + "Massage rejected" + Bcolors.ENDC
    #end send thread
    threadCount-=1
          
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
   
#forewer comunication whit server (alive client and set snaping mode)
def liveCommunication(url_server, wait_time, req_timeout):
    global snapingRun
    while True:
        time.sleep(wait_time)
        try:
            req = requests.post(url=url_server, data="camraID=1", timeout=req_timeout)
        except:
            print Bcolors.FAIL + "Sever not responding" + Bcolors.ENDC
            continue
        #parse responze to JSON
        parsed_json = json.loads(req.text)
        if parsed_json['status'] == 2:
            snapingRun  =  parsed_json['massEnroll']
  

def send_request(url_server,camraID ,transType , encoded_img, idRectangle,req_timeout):
    try:
        req = requests.post(
            url=url_server, 
            data="image="+encoded_img+"&camraID="+camraID+"&transType="+transType+"&getUserInfo=1&faceId="+str(idRectangle), 
            timeout=req_timeout)

        return req.text
    except:
        print "MSG ID: ",idMsg, " ",datetime.datetime.now()
        print Bcolors.FAIL + "Sever not responding" + Bcolors.ENDC
   

def getCounterThreads():
    return threadCount

def isTimeout():
    return timeout

def getSnapingRun():
    return snapingRun