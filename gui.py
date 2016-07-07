
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
actual_person = None

x_posImage = w / 2.5
y_posImage = h / 2.3

w_photo = int(w/2.4)
h_photo = int(h/1.5)

personLabel = None
nameLabel = None
alertLabel = None


def runGui():
	global nameLabel, personLabel ,unknown_person, actual_person, mainCanvas

	root.title("iFaceClient")
	root.attributes('-fullscreen', True)

	mainCanvas = Canvas(root, width=w, height=h)
	mainCanvas.pack()


	thickness_frame = 9

	logo = ImageTk.PhotoImage(file='ApisLogo.gif')
	noentry = ImageTk.PhotoImage(file='noentry.gif')
	rejected = ImageTk.PhotoImage(file='rejected.gif')
	approved = ImageTk.PhotoImage(file='approved.gif')
	

	unknown_person = Image.open("unknown_person.jpg", mode='r' )
	unknown_person = unknown_person.resize((w_photo,h_photo), Image.ANTIALIAS) 
	unknown_person = ImageTk.PhotoImage(image=unknown_person)

	
	mainCanvas.create_image(w-180,80,image=logo)


	actual_person = unknown_person
	nameLabel = mainCanvas.create_image(x_posImage,y_posImage, image=actual_person)
	#nameLabel = mainCanvas.create_image(x_posImage - 260, y_posImage - 180, image=noentry)

	
	
	
	

	#boxPhoto = Label(mainCanvas,background='#BFBFBF') 
	#photoL = Canvas(boxPhoto, image=unknown_person)
	#photoL.place(x=thickness_frame, y=thickness_frame)
	
	#boxPhoto.place(x=w/5, y=h/20,width=w_photo+thickness_frame * 2 +3, height=h_photo+thickness_frame * 2 +3)


	
	#font = tkFont.Font(family="Times New Roman", size=60,weight='bold')
	#nameLabel = mainCanvas.create_text(w/2.5 ,h-h/7, text = "I don't know", font=font)

 	#bind_all("<q>", quit)
	mainCanvas.bind_all('<q>', quit) 
	root.mainloop()

#def quit(self, event):
 #   sys.exit(0)     
def quit(event):
	
	root.destroy()
	os._exit(0)

def showNewPerson(photo,name, permition):
	global nameLabel, personLabel, actual_person, alertLabel
		
	mainCanvas.delete(personLabel)
	actual_person = Image.open(StringIO(photo))
	actual_person = actual_person.resize((w_photo,h_photo), Image.ANTIALIAS) 
	actual_person = ImageTk.PhotoImage(image=actual_person)
	personLabel = mainCanvas.create_image(x_posImage,y_posImage, image=actual_person)
	nameLabel = mainCanvas.create_text(w/2.5 ,h-h/7, text=name, font=font)

	if permition == 1:
		alertLabel = mainCanvas.create_image(x_posImage , y_posImage +120 , image=approved)

	else:
		alertLabel = mainCanvas.create_image(x_posImage , y_posImage +120 , image=rejected)




	

def showDefault():
	global personLabel, unknown_person, actual_person
		
	mainCanvas.delete(personLabel)
	mainCanvas.delete(alertLabel)
	actual_person = unknown_person
	personLabel = mainCanvas.create_image(x_posImage,y_posImage, image=unknown_person)
	mainCanvas.delete(nameLabel)
	


		
		


