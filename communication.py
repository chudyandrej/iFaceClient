import json
import base64
import requests
import cv2

count = 0
URL_server = "http://192.168.1.121:8080/recognise"

#Function for send frame to iFace server
def send_fame_to_iFaceSERVER(frame):
   
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    #Blury detection
    
    if cv2.Laplacian(gray_frame, cv2.CV_64F).var() > 300:
        print "Blurr OK"
    	encoded_img = frame_to_imgB64(frame)
    	req = requests.post (url=URL_server, data="image="+encoded_img+"&camraID=1")
        #parsed_json = json.loads(req.text)
        #print "nacitanych tvari" , parsed_json['detectFaces']
    	print req.text
    	#if espeak:
    #		voice_synthesizer(req.text)
    else:
        print "Skiped. To blurry !!!"





def frame_to_imgB64(frame):
    global count
    count+=1
    img_str = cv2.imencode('.jpg', frame)[1].tostring()
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