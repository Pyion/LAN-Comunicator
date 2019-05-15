import socket
import os,sys
import threading
import curses
from random import randint
import signal

HOST = "10.0.254.249" #input("Enter host IP:\n")
PORT = 1201 #int( input("Enter port:\n") )
FILES_PORT = 3401
USERNAME = input("Username: ")
BUFFER_SIZE = 8192
MAX_COLOR = 0
ipToColor = {}
screenX = 0
screenY = 0
userDate = []
lines = []

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
filesSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
filesSocket.connect((HOST,FILES_PORT))
sock.send(USERNAME.encode('utf-8'))


def main(stdscr):
	initCurses(stdscr)
	filesThread = threading.Thread(target = getFiles, args = [stdscr,lines, userDate])
	t = threading.Thread(target = recieveData, args = [stdscr,lines,userDate] )
	t.start()
	filesThread.start()
	while(True):
		sendData(stdscr)

def initCurses(stdscr):
	screenY, screenX = stdscr.getmaxyx()
	lines = []
	curses.start_color()
	curses.use_default_colors()
	for i in range(0, curses.COLORS):
		curses.init_pair(i + 1, i, -1)
	stdscr.clear()

def sendData(stdscr):
	toSend = getMessage(stdscr)
	if(toSend):
		if(toSend[0] != ':'):
			sock.send(toSend.encode("utf-8"))
		else:
			specialInput(stdscr,toSend)

def getMessage(stdscr):
	stdscr.move(stdscr.getmaxyx()[0]-1, 0)
	stdscr.clrtoeol()
	stdscr.addstr(stdscr.getmaxyx()[0]-1, 0, ">>> ")
	return promptInput(stdscr)

def promptInput(stdscr):
	ERASE = 127
	chars = []
	while True:
		currentChar = stdscr.getch()
		if currentChar in (13, 10):
			break
		elif currentChar == ERASE:
			chars = eraseCharacter(stdscr,chars)
		elif(len(chars) < stdscr.getmaxyx()[1] - 6):
			chars.append(chr(currentChar))
			stdscr.addch(currentChar)
	return "".join(chars)

def eraseCharacter(stdscr,chars):
	y, x = stdscr.getyx()
	if(len(chars)>0):
		del chars[-1]
		stdscr.move(y, (x - 1))
	else:
		curses.beep()
	stdscr.clrtoeol()
	stdscr.refresh()
	return chars

def specialInput(stdscr,command):
	if(command == ':q'):
		os.system("clear")
		os.kill(os.getpid(), signal.SIGUSR1)
		os._exit(1)
	if(command[0:5] == ':send'):
		sendFiles(stdscr,open(command[6:],'rb'),command[6:].split("/")[-1])

def getFiles(stdscr,lines,userDate):
	while(True):
		data = filesSocket.recv(BUFFER_SIZE)
		fileArray = []
		for i in range(int(data.decode("utf-8").split("~")[0])):
			fileArray.append(filesSocket.recv(BUFFER_SIZE))
		recievedFile = open("recievedFile_"+data.decode("utf-8").split("~")[1],'wb')
		for i in range(int(data.decode("utf-8").split("~")[0])):
			recievedFile.write(fileArray[i])
		recievedFile.close()
		moveScreen(stdscr,lines,userDate);
		stdscr.move(len(lines)-1, 0)
		stdscr.addstr("File recieved, name of file: " + data.decode("utf-8").split("~")[1], curses.color_pair(0))
		lines.append("")
		userDate.append("File recieved, name of file: " + data.decode("utf-8").split("~")[1])

def sendFiles(stdscr,fileToSend,fileName):
	numberOfPackets = (len(fileToSend.read())+1)//1024
	filesSocket.send((str(numberOfPackets)+'~'+fileName).encode('utf-8'))
	for i in range(numberOfPackets):
		filesSocket.send(fileToSend.read(1024))


def recieveData(stdscr,lines,userDate):
	while True:
		data = sock.recv(BUFFER_SIZE)
		dataEncoded = data.decode("utf-8")
		if(dataEncoded):
			if(dataEncoded[0] != ':'):
				getNormalInput(stdscr,dataEncoded,lines,userDate)
				stdscr.move( stdscr.getmaxyx()[0] - 1, 5 )
				stdscr.refresh()
			else:
				getSpecialInput(dataEncoded)


def getNormalInput(stdscr,dataEncoded,lines,userDate):
	if(dataEncoded.split("~")[2] not in ipToColor):
		ipToColor[dataEncoded.split("~")[2]] = randint(2,255);
	userColor = ipToColor[dataEncoded.split("~")[2]]
	if (len(dataEncoded.split("~"))>1):
		userDate, lines = moveScreen(stdscr,lines,userDate);
		userDate.append('[' + dataEncoded.split("~")[1] + ']')

		lines.append([' '+ dataEncoded.split("~")[2]  + '~'.join(dataEncoded.split("~")[3:]),ipToColor[dataEncoded.split("~")[2]]])

		stdscr.move(len(lines)-1, 0)
		stdscr.addstr(userDate[len(userDate)-1], curses.color_pair(0))
		stdscr.addstr(lines[len(lines)-1][0], curses.color_pair(lines[len(lines)-1][1]))

def moveScreen(stdscr,lines,userDate):
	if len(lines) > stdscr.getmaxyx()[0]-3:
		del lines[0]
		del userDate[0]
		stdscr.clear()
		for i, line in enumerate(lines):
			stdscr.move(i, 0)
			stdscr.addstr(userDate[i], curses.color_pair(0))
			stdscr.addstr(lines[i][0], curses.color_pair(lines[i][1]))
		stdscr.addstr(stdscr.getmaxyx()[0]-1, 0, ">>> ")
	return userDate,lines

def getSpecialInput(command):
	pass



curses.wrapper(main)
