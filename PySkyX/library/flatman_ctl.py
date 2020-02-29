#!/usr/bin/env python
import sys
import serial
import time
import getopt

FLIPFLAP=99
FLATMAN=19
FLATMANXL=10
FLATMANL=15
FLATMASK=18
# motor state
NOT_RUNNING=0
RUNNING=1
# flap state
FLAP_UNKNOWN=0
FLAP_CLOSED=1
FLAP_OPEN=2
FLAP_TIMEOUT=3
#light state
LIGHT_OFF=0
LIGHT_ON=1

class FlatMan(object):

	__serialPort = None
	__serialCon = None
	__data = None
	__str = ""
	__model = 0
	__stateFlipFlat = FLAP_UNKNOWN
	__debug = False
	__motorState = NOT_RUNNING
	__lightState = LIGHT_OFF

	def __init__(self, serial_port, debug = False, model = FLATMAN):
		if(serial_port):
			self.__serialPort = serial_port
		self.__debug = debug
		self.__model = model

	def Connect(self):
		try:
			self.__serialCon = serial.Serial(self.__serialPort, 9600, timeout=0, rtscts=False, dsrdtr=False)
		except Exception as e :
			if self.__debug:
				print ("connection error : {0}" . format(e))
			return False
		# Magic dance
		self.__serialCon.dtr = True
		self.__serialCon.rts = True

		self.__serialCon.dtr = True
		self.__serialCon.rts = False
		time.sleep(1.1)

		self.__serialCon.dtr = False
		self.__serialCon.rts = False
		time.sleep(1.1)

		if self.__debug:
			print ("Connection opened")
		return True


	def Disconnect(self):
		self.__serialCon.close()
		self.__serialCon = None


	def ReadData(self) :
		s = self.__serialCon.read(1)
		s=s.decode()
		if len(s) and s.find("\n")!=-1:
			self.__str+=s
			tmp = self.__str.split("\n")
			self.__data = tmp[0]
			self.__str = ""
		else :
			self.__str+=s
			time.sleep(0.001)
		if self.__debug:
			if self.__data:
				print ("[ReadData] data from device : %s" % self.__data)

	def Ping(self):
		self.__data = None
		self.__serialCon.write(str.encode(">P000\n"))
		timeout = time.time() + 2
		while True:
			self.ReadData()
			if(self.__data and self.__data.startswith("*P")):
				# extract model
				self.__model=int(self.__data[2:4])
				if self.__debug:
					print ("Model = %d\n" % self.__model)
				break;
			now = time.time()
			if(now > timeout):
				if self.__debug:
					print ("[Ping] Timeout waiting for response")
				return False
		return True

	def Open(self):
		self.__data = None
		if self.__model != FLIPFLAP and self.__model != FLATMASK:
			print ("Model is not a Flip-Flat : %d\n" % self.__model)
			return False
		self.__serialCon.write(str.encode(">O000\n"))
		timeout = time.time() + 60
		while True:
			self.ReadData()
			if(self.__data and self.__data.startswith("*O")):
				break;
			now = time.time()
			if(now > timeout):
				if self.__debug:
					print ("[Open] Timeout waiting for response")
				return False
		# wait for pannel to fully open
		timeout = time.time() + 60
		if self.__debug:
			print ("[Open]  Waiting for flap to fully open")

		while True :
			if self.__debug:
				if sys.version_info[0] < 3:
					print ("."),
				else :
					print (".", end='')
			self.GetState()
			if self.__stateFlipFlat == FLAP_OPEN:
				break
			now = time.time()
			if(now > timeout):
				if self.__debug:
					print ("[Open] Timeout waiting for response")
			time.sleep(1)
		return True

	def Close(self):
		self.__data = None
		if self.__model != FLIPFLAP and self.__model != FLATMASK:
			print ("Model is not a Flip-Flat : %d\n" % self.__model)
			return False
		self.__serialCon.write(str.encode(">C000\n"))
		timeout = time.time() + 60
		while True:
			if self.__debug:
				print (".",)
			self.ReadData()
			if(self.__data and self.__data.startswith("*C")):
				break;
			now = time.time()
			if(now > timeout):
				if self.__debug:
					print ("[Close] Timeout waiting for response")
				return False
		# wait for pannel to fully close
		timeout = time.time() + 60
		if self.__debug:
			print ("[Close]  Waiting for flap to fully closed")
		while True :
			self.GetState()
			if self.__stateFlipFlat == FLAP_CLOSED:
				break
			now = time.time()
			if(now > timeout):
				if self.__debug:
					print ("[Open] Timeout waiting for response")
			time.sleep(1)
		return True

	def GetState(self):
		self.__data = None
		self.__serialCon.write(str.encode(">S000\n"))
		timeout = time.time() + 60
		while True:
			self.ReadData()
			if(self.__data and self.__data.startswith("*S")):
				break;
			now = time.time()
			if(now > timeout):
				if self.__debug:
					print ("[GetState] Timeout waiting for response")
				return False
		try:
			if self.__debug:
				print ("self.__data = %s" % self.__data);
			self.__motorState = int(self.__data[4])
			self.__lightState =  int(self.__data[5])
			self.__stateFlipFlat =  int(self.__data[6])
			if self.__debug:
				print ("self.__motorState = %d" % self.__motorState)
				print ("self.__lightState = %d" % self.__lightState)
				print ("self.__stateFlipFlat = %d" % self.__stateFlipFlat)

		except Exception as e:
			print("[GetState] Invalid response")
			print(e)
			return


	def Light(self, state):
		self.__data = None
		# FlipFlat need to be closed before we can switch the light on.
		if (self.__model == FLIPFLAP or self.__model == FLATMASK) and self.__stateFlipFlat != FLAP_CLOSED:
			if not self.Close():
				return False
		if(state == "ON" ):
			self.__serialCon.write(str.encode(">L000\n"))
		else :
			self.__serialCon.write(str.encode(">D000\n"))

		timeout = time.time() + 2
		while True:
			self.ReadData()
			if(self.__data and (self.__data.startswith("*L") or self.__data.startswith("*D") ) ):
				break;
			now = time.time()
			if(now > timeout):
				if self.__debug:
					print ("[Light] Timeout waiting for response")
				return False
		return True

	def Brightness(self, level):
		self.__data = None
		if level > 255:
			level = 255
		if level < 0:
			level = 0
		self.__serialCon.write(str.encode(">B%03d\n" % level))
		timeout = time.time() + 2
		while True:
			self.ReadData()
			if(self.__data and self.__data.startswith("*B")):
				break;
			now = time.time()
			if(now > timeout):
				if self.__debug:
					print ("[Brightness] Timeout waiting for response")
				return False
		return True

	def Status(self):
		self.__data = None
		self.__serialCon.write(str.encode(">S000\n"))
		timeout = time.time() + 2
		while True:
			self.ReadData()
			if(self.__data and self.__data.startswith("*S")):
				# parse status
				# TBD
				break;
			now = time.time()
			if(now > timeout):
				if self.__debug:
					print ("[Status] Timeout waiting for response")
				return False
		return True


def usage():
	print ("flatman_ctl.py  --port=</dev/port> [--open | --close | --light={on|off} | --level=<brightness_level>][--debug] [--help]")
	return


def main():
	debug = False
	serial_port = None
	commands = []
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hd",["port=",
        											"open",
													"close",
													"light=",
													"level=",
													"debug",
													"help"])
	except getopt.GetoptError as e:
		print ("Error parsing options : {0}" . format(e))
		usage()
		return 1

	for o, a in opts:
		if o == "--port":
			serial_port = a.strip()
		if o == "--open":
			commands.append("OPEN")
		if o == "--close":
			commands.append("CLOSE")
		if o == "--light":
			if a.strip().upper() == "ON":
				commands.append("LIGHT_ON")
			if a.strip().upper() == "OFF":
				commands.append("LIGHT_OFF")
		if o == "--level":
			commands.append("LEVEL:%s" % a.strip())
		if o == "--debug":
			debug =True

	if not serial_port:
		usage()
		return 1

	if debug:
		print (commands)

	panel = FlatMan(serial_port, debug)

	if not panel.Connect():
		return 1

	if not panel.Ping():
		if debug :
			print ("Error on Ping.. exiting")
		panel.Disconnect()
		return 1

	allOk = True
	for cmd in commands:
		if debug :
			print ("cmd = %s" % cmd)
		if cmd == "OPEN" :
			allOk = panel.Open()
		elif cmd == "CLOSE" :
			allOk = panel.Close()
		elif cmd == "LIGHT_ON" :
			allOk = panel.Light("ON")
		elif cmd == "LIGHT_OFF" :
			allOk = panel.Light("OFF")
		elif cmd.startswith("LEVEL") :
			allOk = panel.Brightness(int(cmd.split(":")[1]))

		if not allOk:
			if debug :
				print ("Error on command %s" % cmd)
			return 1

	panel.Disconnect()
	return 0

if __name__ == '__main__':
    sys.exit(main())

