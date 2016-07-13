import threading
import os
import sys
from gui import runGui
from faceDetect import runFaceDetect




def main():


    t = threading.Thread(target=runFaceDetect, args=(sys.argv[1],))
    t.start()
    runGui()

if __name__ == "__main__":
    main()


