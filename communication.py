import json
import base64
import requests
import cv2



threadCount = 0
coun = 0
URL_server = "http://192.168.1.157:8080/recognise"



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
    global threadCount
    threadCount+=1
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    #Blury detection
    if cv2.Laplacian(gray_frame, cv2.CV_64F).var() > 1000:
        #print "Blurr OK Sending ..."
    	encoded_img = frame_to_imgB64(frame)
        req = send_request(encoded_img)
        
        if not req == 404:
            parsed_json = json.loads(req.text)
            if parsed_json['detectFaces'] == 1:
                print Bcolors.OKGREEN + "Face detected " + Bcolors.ENDC
            else:
                print Bcolors.WARNING + "Face not detected " + Bcolors.ENDC

        	#print req.text
        	#if espeak:s
        #		voice_synthesizer(req.text)
       #else:
          #  print "WUT"
    else:
        print "Skiped. To blurry !!!"
    threadCount-=1

def frame_to_imgB64(frame):
    global coun
    #coun+=1
    img_str = cv2.imencode('.jpg', frame)[1].tostring()
    #filename = "image"+str(coun)
    #f = open(filename,'w')
    #f.write(img_str) # python will convert \n to os.linesep
    #f.close()
    encoded_img = base64.encodestring(img_str)
    encoded_img = encoded_img.replace('+', '-')
    encoded_img = encoded_img.replace('/', '_')
    encoded_img = encoded_img.replace('.', '.')
    return encoded_img


def voice_synthesizer(json_message):
	parsed_json = json.loads(json_message)
	if parsed_json['count'] > 0:
		command = "espeak -v sk --stdout '%s %s' | aplay" % (parsed_json['first_name'], parsed_json['last_name'])
		os.system(command.encode('UTF-8'))


def send_request(encoded_img):
    try:
    
        return requests.post (url=URL_server, data="image="+encoded_img+"&camraID=1", timeout=4)
    except requests.exceptions.RequestException as e:
        print Bcolors.FAIL + "Sever not responding" + Bcolors.ENDC
        return 404

def getCounterThreads():
    return threadCount




