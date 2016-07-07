import threading
from gui import runGui
from faceDetect import runFaceDetect
    


if __name__ == "__main__":
    t = threading.Thread(target=runFaceDetect)
    t.start()
    runGui()
   





