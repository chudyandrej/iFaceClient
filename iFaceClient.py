import threading
import os
import sys
import commentjson
import logging
import logging.handlers

from gui import runGui
from faceDetect import runFaceDetect

def main():
	############# Laod config file ##################
	file_ = open("config.json", "r")
	config_str = file_.read();
	file_.close()
	config = commentjson.loads(config_str)
	################################################

	################ Set logger ######################
	logger = logging.getLogger("iFace Clinet")
	logger.setLevel(logging.DEBUG)
	# create file handler which logs even debug messages
	fh = logging.handlers.RotatingFileHandler('./logs/'+ config['NAME_backup_file'], maxBytes=config['MAX_size_log'], backupCount=config['COUNT_backup'])
	fh.setLevel(logging.DEBUG)

	# create console handler with a higher log level
	ch = logging.StreamHandler()
	ch.setLevel(logging.ERROR)
	# create formatter and add it to the handlers
	formatter = logging.Formatter("%(asctime)s  - %(levelname)s - %(message)s")
	ch.setFormatter(formatter)
	fh.setFormatter(formatter)

	# add the handlers to logger
	logger.addHandler(ch)
	logger.addHandler(fh)
	################################################


	t = threading.Thread(target=runFaceDetect, args=(sys.argv[1],config, logger))
	t.start()
	runGui(config)

if __name__ == "__main__":
    main()


