
from Tkinter import *
import Image
import PIL.ImageTk as ImageTk
import tkFont
import threading
from StringIO import StringIO
import os

#Display resolution
w = 1366
h = 768


#GUI INIT VALUES
root = Tk()
mainCanvas = None

font = tkFont.Font(family="system", size=60,weight='bold')

unknown_person = None
rejected = None
approved = None
ok = None
no = None

actual_person = None

x_posImage = w / 2.5
y_posImage = h / 2.3

w_photo = int(w/2.4)
h_photo = int(h/1.5)

personLabel = None
nameLabel = None
alertLabel = None
okLabel = None

config = False


def runGui():
	global nameLabel, personLabel ,unknown_person, actual_person, mainCanvas,approved,rejected, ok, no

	root.title("iFaceClient")
	root.attributes('-fullscreen', True)

	mainCanvas = Canvas(root, width=w, height=h)
	mainCanvas.pack()

	thickness_frame = 9

	logo = ImageTk.PhotoImage(file='./images/ApisLogo.gif')
	rejected = ImageTk.PhotoImage(file='./images/rejected.gif')
	approved = ImageTk.PhotoImage(file='./images/ok2.gif')
	ok = ImageTk.PhotoImage(file='./images/ok.gif')
	no = ImageTk.PhotoImage(file='./images/x.gif')
	
	unknown_person = Image.open("./images/unknown_person.jpg", mode='r' )
	unknown_person = unknown_person.resize((w_photo,h_photo), Image.ANTIALIAS) 
	unknown_person = ImageTk.PhotoImage(image=unknown_person)

	mainCanvas.create_image(w-180,80,image=logo)

	actual_person = unknown_person
	nameLabel = mainCanvas.create_image(x_posImage,y_posImage, image=actual_person)

	mainCanvas.bind_all('<q>', quit) 
	mainCanvas.bind_all('<s>', settings) 
	root.mainloop()
  
def quit(event):
	root.destroy()
	os._exit(0)

def settings(event):
	global  config
	config = not config

def showNewPerson(photo,name, permition):
	global nameLabel, personLabel, actual_person, alertLabel, okLabel
		
	mainCanvas.delete(personLabel)
	print len(photo)
	if not len(photo) == 0 :
		try:
			actual_person = Image.open(StringIO(photo + "LL"))
			actual_person = actual_person.resize((w_photo,h_photo), Image.ANTIALIAS) 
			actual_person = ImageTk.PhotoImage(image=actual_person)
		except:
			actual_person = unknown_person
			print "Rase................"
	personLabel = mainCanvas.create_image(x_posImage,y_posImage, image=actual_person)
	nameLabel = mainCanvas.create_text(w/2.5 ,h-h/7, text=name, font=font)


	if permition == 1:
		alertLabel = mainCanvas.create_image(x_posImage -8 , y_posImage +120, image=approved)
		okLabel = mainCanvas.create_image(x_posImage + 500,y_posImage +70 , image=ok)
	
	else:
		alertLabel = mainCanvas.create_image(x_posImage -8 , y_posImage +130 , image=rejected)
		okLabel = mainCanvas.create_image(x_posImage + 500,y_posImage +70 , image=no)
	

def showDefault():
	global personLabel, unknown_person, actual_person
		
	mainCanvas.delete(personLabel)
	mainCanvas.delete(alertLabel)
	mainCanvas.delete(okLabel)
	actual_person = unknown_person
	personLabel = mainCanvas.create_image(x_posImage,y_posImage, image=unknown_person)
	mainCanvas.delete(nameLabel)
	
def getConfig():
	return config 
def offConfig():
	global config
	config = False


		
		


