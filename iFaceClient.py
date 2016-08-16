import threading
import os
import sys
import commentjson
from pprint import pprint

from gui import runGui
from faceDetect import runFaceDetect

def main():
	#laod config file
	file_ = open("config.json", "r")
	config_str = file_.read();

	config = commentjson.loads(config_str)

	t = threading.Thread(target=runFaceDetect, args=(sys.argv[1],config))
	t.start()
	runGui()

if __name__ == "__main__":
    main()


