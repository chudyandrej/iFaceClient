import json
import base64
import requests
import cv2
import time
import datetime
import os
from threading import Lock
import threading
from gui import showNewPerson, showDefault, showUp, serverNotResponding
import urllib2
import copy

#-------------------------------------------------------
#                    Global variables
#-------------------------------------------------------
timeout = False
lock = Lock()
enrollRun = False
detectedMess = []
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
def send_fame_to_iFaceSERVER(person,config, logger):
    try:
        global timeout, lock, detectedMess
        detectedMess = filter(lambda a: (datetime.datetime.now() - a[1]) < datetime.timedelta(seconds=15), detectedMess)
        #Counter of threads
       
       

        #get cut window frame and code to b64
        frame = copy.copy(person.getWindow())
        try:
            encoded_img = code_B64(frame)
        except Exception,e: 
            logger.error("ENCODE FRAME TO SEND -> frame size: "+ str(len(frame))+" Problem with encoding image! "+str(type(e))+" | Error text: "+str(e))

        #send request
       
        req = send_request(config['URL_server_recognise'],config['cameraId'],str(config['transType']),encoded_img, person.getIdRectangle(),config['TIMEOUT_request'])
        #If server not responding
        if not req == 404:
            #parse responze to JSON
            parsed_json = json.loads(req)
            
            #If the detected one person
            if parsed_json['status'] == 2:
                if not abs(parsed_json['msgStatus']) == 2 :
                    person.setConfidence(int(parsed_json['faceConfidence']))
                if not enrollRun:
                    if parsed_json['msgStatus'] == 3:   #person was detected
                        print Bcolors.OKGREEN + parsed_json["name" + str(parsed_json["userId"])] + Bcolors.ENDC 
                        lock.acquire(True)
                        person.personRecognised()
                        detectedMess.append([parsed_json,datetime.datetime.now()])
                        #Lockable block
                        #set timeout (stop create new send thread)
                        timeout = True
                        #show person and name in GUI
                        showNewPerson(decode_B64(parsed_json),parsed_json["name" + str(parsed_json["userId"])],parsed_json["enabled" + str(parsed_json["userId"])], logger)
                        logger.info("Detected person: "+parsed_json["name" + str(parsed_json["userId"])])     
                        #voice_synthesizer(parsed_json)
                        #timeout between detections
                        time.sleep(config['TIMEOUT_between_display'])
                        #show defauld screen in GUI
                        showDefault()
                        #deactivate timeout
                        timeout = False
                        lock.release()

                    elif parsed_json['msgStatus'] == 2:
                        if not timeout:
                            time.sleep(1)
                        if  lock.acquire(False) == True:
                            #Lockable block
                            #set timeout (stop create new send thread)
                            timeout = True
                            try:
                                image = cv2.imencode('.jpg', frame)[1].tostring()
                            except Exception,e:
                                logger.error("UNKNOWN PERSON CODE IMAGE -> frame size: "+ str(len(frame))+" Problem with encoding image! "+str(type(e))+" | Error text: "+str(e))
                            showNewPerson(image,'',None, logger)
                            time.sleep(config['TIMEOUT_between_display'])
                            showDefault()
                            timeout = False
                            lock.release()

                    elif parsed_json['msgStatus'] == -2:
                        person.personRecognised()
                        print Bcolors.BOLD + "Person Banned" + Bcolors.ENDC
                        if not timeout:
                            time.sleep(1)
                        if lock.acquire(False) == True:
                            bannedPerson = None
                            for msg in detectedMess:
                                    if int(msg[0]['userId']) == parsed_json['lastRecognised']:
                                        msg[1] =  datetime.datetime.now()
                                        bannedPerson = msg
                            if not bannedPerson == None:
                                #Lockable block
                                timeout = True
                                showNewPerson(decode_B64(bannedPerson[0]),bannedPerson[0]["name" + str(bannedPerson[0]["userId"])],
                                    bannedPerson[0]["enabled" + str(bannedPerson[0]["userId"])], logger)
                                logger.info("Banned person detected: "+ bannedPerson[0]["name" + str(bannedPerson[0]["userId"])])     
                                time.sleep(config['TIMEOUT_between_display'] - 0.5)
                                showDefault()
                                timeout = False
                            lock.release()

                    elif parsed_json['msgStatus'] == 1:
                        print Bcolors.WARNING + "Walk up and do not move" + Bcolors.ENDC
                        print parsed_json['badDesc']
                        if  lock.acquire(False) == True:
                            showUp()
                            lock.release()
                    elif parsed_json['msgStatus'] == 0:
                        print Bcolors.UNDERLINE + "Face not detected " + Bcolors.ENDC
                    else:
                        print Bcolors.WARNING + "Message rejected" + Bcolors.ENDC
                        logger.warn("Server rejected a message.")
    except Exception,e:
        logger.error("FATAL ERROR !!! IN SENDING PART OF PROGRAM | Type: "+str(type(e))+" Description: "+str(e)+" msgStatus: "+parsed_json['msgStatus'])


            
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
def liveCommunication(url_server, wait_time, req_timeout, logger):
    global enrollRun
    while True:
        time.sleep(wait_time)
        try:
            req = requests.post(url=url_server, data="camraID=1", timeout=req_timeout)
        except:
            print Bcolors.FAIL + "Sever not responding" + Bcolors.ENDC
            serverNotResponding()
            logger.warn("Sever not responding! Waited "+ str(req_timeout)+"s")
            continue
        #parse responze to JSON
        parsed_json = json.loads(req.text)
        if parsed_json['status'] == 2:
            enrollRun  =  parsed_json['massEnroll']
  

def send_request(url_server,camraID ,transType , encoded_img, idRectangle,req_timeout):
    try:
        req = requests.post(
            url=url_server, 
            data="image="+encoded_img+"&camraID="+camraID+"&transType="+transType+"&getUserInfo=1&faceId="+str(idRectangle), 
            timeout=req_timeout)
        return req.text
    except:
        serverNotResponding()
        print Bcolors.FAIL + "Sever not responding" + Bcolors.ENDC
        logger.warn("Sever not responding! Waited "+ str(req_timeout)+"s")
   

def isTimeout():
    return timeout

def getEnrollRun():
    return enrollRun




