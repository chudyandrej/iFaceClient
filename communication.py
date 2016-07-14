import json
import base64
import requests
import cv2
import time
import os
from threading import Lock
import numpy as np
from gui import showNewPerson, showDefault


apis_logo = ()
threadCount = 0
coun = 0
URL_server = "http://192.168.1.157:8080/recognise"
timeout = False
lock = Lock()

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
def send_fame_to_iFaceSERVER(frame):
    global threadCount, timeout, lock
    threadCount+=1
   
    encoded_img = code_B64(frame)
    req = send_request(encoded_img)
    
    if not req == 404:
        parsed_json = json.loads(req.text)
        if parsed_json['detectFaces'] == 1:
            print Bcolors.OKGREEN + "Face detected " + Bcolors.ENDC
            if parsed_json['recognised'] == True:
                print Bcolors.OKGREEN + "Yes" + Bcolors.ENDC
                if lock.acquire(False) == True:
                    timeout = True
                    showNewPerson(decode_B64(parsed_json),parsed_json["name" + str(parsed_json["userId"])],parsed_json["enabled" + str(parsed_json["userId"])])
                    voice_synthesizer(parsed_json)
                    showDefault()
                    timeout = False
                    lock.release()
            else:
                print Bcolors.FAIL + "NO" + Bcolors.ENDC
        else:
            print Bcolors.WARNING + "Face not detected " + Bcolors.ENDC

    threadCount-=1

def code_B64(frame):
    global coun

    img_str = cv2.imencode('.jpg', frame)[1].tostring()
    encoded_img = base64.encodestring(img_str)
    encoded_img = encoded_img.replace('+', '-')
    encoded_img = encoded_img.replace('/', '_')
    encoded_img = encoded_img.replace('=', '.')
    return encoded_img

def decode_B64(parsed_json):
    encoded_img = parsed_json["image" + str(parsed_json["id"])]
    encoded_img = encoded_img.replace('-', '+')
    encoded_img = encoded_img.replace('_', '/')
    encoded_img = encoded_img.replace('.', '=')
    decode_img = base64.decodestring(encoded_img)
    
    return decode_img
   

def voice_synthesizer(parsed_json):
    name = parsed_json["name" + str(parsed_json["userId"])]
    print name
    command = "espeak -v sk --stdout '%s' | aplay" % (name)
    os.system(command.encode('UTF-8'))
    time.sleep(4)
    
def send_request(encoded_img):
    try:    
        return requests.post (url=URL_server, data="image="+encoded_img+"&camraID=1&getUserInfo=1", timeout=4)
    except requests.exceptions.RequestException as e:
        print Bcolors.FAIL + "Sever not responding" + Bcolors.ENDC
        return 404

def getCounterThreads():
    return threadCount

def isTimeout():
    return timeout

