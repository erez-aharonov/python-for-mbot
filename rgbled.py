from lib.mBot import *
import random

if __name__ == '__main__':
	bot = mBot()
	bot.startWithSerial("/dev/ttyUSB0")
	# bot.startWithHID()
	while(1):
		bot.doRGBLedOnBoard(1,random.randint(0, 255),random.randint(0, 255),random.randint(0, 255))
		sleep(0.5)
		# bot.doRGBLedOnBoard(1,0,100,0)
		# sleep(0.5)
		# bot.doRGBLedOnBoard(1, 0, 0, 100)
		# sleep(0.5)