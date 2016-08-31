
from Tkinter import *
import Image
import PIL.ImageTk as ImageTk
import tkFont
import threading
from StringIO import StringIO
import os
import time

#Display resolution
w = 1366
h = 768


#GUI INIT VALUES
root = Tk()
mainCanvas = None

font = tkFont.Font(family="system", size=50,weight='bold')

unknown_person = None
rejected = None
approved = None
unrecognised = None
ok = None
no = None
up = None
server = None
camera = None

actual_person = None

x_posImage = w / 2.5
y_posImage = h / 2.3

w_photo = int(w/2.6)
h_photo = int(h/1.3)

personLabel = None
nameLabel = None
alertLabel = None
okLabel = None

view = False
setting = False

def runGui(config):
	global nameLabel, personLabel ,unknown_person, actual_person, mainCanvas,approved,rejected,unrecognised, ok, no, up, server, camera

	root.title("iFaceClient")
	root.attributes('-fullscreen', True)

	mainCanvas = Canvas(root, width=w, height=h)
	mainCanvas.pack()

	thickness_frame = 9

	logo = ImageTk.PhotoImage(file='./images/ApisLogo.gif')
	ok = ImageTk.PhotoImage(file='./images/ok.gif')
	no = ImageTk.PhotoImage(file='./images/x.gif')
	up = ImageTk.PhotoImage(file='./images/up.gif')
	server = ImageTk.PhotoImage(file='./images/server.gif')
	camera = ImageTk.PhotoImage(file='./images/camera.gif')


	if config['LANGUAGE'] == 'SK':
		if config['transType'] == 1:
			approved = ImageTk.PhotoImage(file='./images/entry_sk.gif')
		else:
			approved = ImageTk.PhotoImage(file='./images/exit_sk.gif')
		rejected = ImageTk.PhotoImage(file='./images/rejected_sk.gif')
		unrecognised = ImageTk.PhotoImage(file='./images/unrecognized_sk.gif')

	elif config['LANGUAGE'] == 'EN':
		if config['transType'] == 1:
			approved = ImageTk.PhotoImage(file='./images/entry_en.gif')
		else:
			approved = ImageTk.PhotoImage(file='./images/exit_en.gif')
		rejected = ImageTk.PhotoImage(file='./images/rejected_en.gif')
		unrecognised = ImageTk.PhotoImage(file='./images/unrecognized_en.gif')

	elif config['LANGUAGE'] == 'RU':
		if config['transType'] == 1:
			approved = ImageTk.PhotoImage(file='./images/entry_ru.gif')
		else:
			approved = ImageTk.PhotoImage(file='./images/exit_ru.gif')
		rejected = ImageTk.PhotoImage(file='./images/rejected_ru.gif')
		unrecognised = ImageTk.PhotoImage(file='./images/unrecognized_ru.gif')

	
	unknown_person = Image.open("./images/unknown_person.jpg", mode='r' )
	unknown_person = unknown_person.resize((w_photo,h_photo), Image.ANTIALIAS) 
	unknown_person = ImageTk.PhotoImage(image=unknown_person)

	mainCanvas.create_image(w-180,80,image=logo)

	actual_person = unknown_person
	nameLabel = mainCanvas.create_image(x_posImage,y_posImage, image=actual_person)

	mainCanvas.bind_all('<q>', quit) 
	mainCanvas.bind_all('<s>', settings) 
	mainCanvas.bind_all('<w>', viewer) 
	root.mainloop()
  
def quit(event):
	root.destroy()
	os._exit(0)

def offViewer():
	global view
	view = False

def viewer(event):
	global  view
	view = not view

def getView():
	return view 

def settings(event):
	global  setting
	setting = not setting

def getSettings():
	return setting 

def offSettings():
	global setting
	setting = False


def showUp():
	upLabel = mainCanvas.create_image(x_posImage + 500,y_posImage + 70 , image=up)
	time.sleep(0.1)
	mainCanvas.delete(upLabel)

def serverNotResponding():
	serverL = mainCanvas.create_image(x_posImage - 440,y_posImage - 240 , image=server)
	time.sleep(1)
	mainCanvas.delete(serverL)

def cameraError():
	cmaeraL = mainCanvas.create_image(x_posImage - 400,y_posImage - 200 , image=camera)
	time.sleep(5)
	mainCanvas.delete(cmaeraL)

def showNewPerson(photo,name, permition, logger):
	global nameLabel, personLabel, actual_person, alertLabel, okLabel
	mainCanvas.delete(personLabel)
	if not len(photo) == 0 :
		try:
			actual_person = Image.open(StringIO(photo + "LL"))
			actual_person = actual_person.resize((w_photo,h_photo), Image.ANTIALIAS) 
			actual_person = ImageTk.PhotoImage(image=actual_person)
		except:
			actual_person = unknown_person
			logger.error("GUI new person load photo!")
	personLabel = mainCanvas.create_image(x_posImage,y_posImage, image=actual_person)
	nameLabel = mainCanvas.create_text(w/2.5 ,h-h/8, text=name, font=font)
	print permition

	if permition == 1:
		alertLabel = mainCanvas.create_image(x_posImage - 8 , y_posImage + 140, image=approved)
		okLabel = mainCanvas.create_image(x_posImage + 500,y_posImage + 70 , image=ok)
	elif permition == -1:
		alertLabel = mainCanvas.create_image(x_posImage - 8 , y_posImage + 140 , image=rejected)
		okLabel = mainCanvas.create_image(x_posImage + 500,y_posImage + 70 , image=no)
	else: 
		alertLabel = mainCanvas.create_image(x_posImage - 8 , y_posImage + 140 , image=unrecognised)
		okLabel = mainCanvas.create_image(x_posImage + 500,y_posImage + 70 , image=no)
	

def showDefault():
	global personLabel, unknown_person, actual_person
		
	mainCanvas.delete(personLabel)
	mainCanvas.delete(alertLabel)
	mainCanvas.delete(okLabel)
	actual_person = unknown_person
	personLabel = mainCanvas.create_image(x_posImage,y_posImage, image=unknown_person)
	mainCanvas.delete(nameLabel)
	


		
		


