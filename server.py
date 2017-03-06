#!/usr/bin/env python3

# -------------------------------
# cs356-http/server-zjg95.py
# Copyright (C) 2015
# Zachary J. Goodman
# -------------------------------

# -------
# imports
# -------

from socket	import *
from sys import argv, exit
import os
import time

# ----------------
# server meta data
# ----------------

path = os.path.dirname(os.path.abspath(__file__))
serverName = "TastyTTP"
serverVersion = "2.6"
listening = True
MAX_FILE_SIZE = 8192
endl = "\r\n"

months = {
	"Jan" : 1, "Feb" : 2, "Mar" : 3, "Apr" : 4,
	"May" : 5, "Jun" : 6, "Jul" : 7, "Aug" : 8,
	"Sep" : 9, "Oct" : 10, "Nov" : 11, "Dec" : 12
}

# ----------
# HTTP codes
# ----------

codeDict = {
	200 : "200 OK",
	304 : "304 Not Modified",
	400 : "400 Bad Request",
	404 : "404 Not Found",
	405 : "405 Method Not Allowed",
	415 : "415 Unsupported Media Type",
	418 : "418 I'm a teapot",
	505 : "505 HTTP Version Not Supported"
}

# -----------------
# exception classes
# -----------------


class NonGetRequestException (Exception) :
	"""
    indicates the requested method was not GET
    """
	pass

class NotFoundException (Exception) :
	"""
    indicates the requested file was not found
    """
	pass

class BadRequestException (Exception) :
	"""
    indicates invalid HTTP syntax in the request
    """
	pass

class FileTypeNotSupportedException (Exception) :
	"""
    indicates the requested file is unsupported
    """
	pass

class HTTPVersionNotSupportedException (Exception) :
	"""
    indicates an unsupported version of HTTP in request
    """
	pass

class CoffeePotException (Exception) :
	"""
    indicates BREW method in request
    """
	pass

class NotModifiedException (Exception) :
	"""
    indicates file has not been modified
    """
	pass

# ------------
# time methods
# ------------

def getCurrentTime () :
	"""
    return a time struct of the current time
    """
	return time.gmtime()

def getCurrentTimeString () :
	"""
    return the current time (GMT) in the form of a string
    """
	tnow = getCurrentTime()
	return time.strftime('%a, %d %b %Y %H:%M:%S GMT', tnow)

def getModifiedTime (fileName) :
	"""
    fileName the name and path to the file
    return a time struct representing the last modification of the file
    """
	modtime = os.path.getmtime(fileName)
	return time.gmtime(modtime)

def getModifiedTimeString (fileName) :
	"""
    fileName the name and path to the file
    return the time a file was last modified (GMT) in the form of a string
    """
	gmtime = getModifiedTime(fileName)
	return time.strftime('%a, %d %b %Y %H:%M:%S GMT', gmtime)

def timeStringDict (timeString) :
	"""
    parse a string into a dictionary containing the time values
    raises BadRequestException if the time cannot be parsed
    timeString a string representation of a time (GMT)
    return a dictionary
    """
	timeDict = {}
	try :

		# split the calendar time
		timeList = timeString.split(' ')
		timeDict["dayName"] = timeList[0][:1]
		timeDict["day"] = int(timeList[1])
		timeDict["month"] = months[timeList[2]]
		timeDict["year"] = int(timeList[3])
		timeDict["zone"] = timeList[5]
		# split the clock time
		timeList = timeList[4].split(':')
		timeDict["hour"] = int(timeList[0])
		timeDict["minute"] = int(timeList[1])
		timeDict["second"] = int(timeList[2])

	except IndexError :
		raise BadRequestException

	return timeDict

def compareDateTo (date1, date2) :
	"""
    compares two dates
    date1 a dictionary containing the values of the first date
    date2 a dictionary containing the values of the second date
    return 0 if equal, -1 if date1 comes before date2, and 1 vice-versa
    """
	if date1["year"] != date2["year"] :
		return (1, -1)[date1["year"] < date2["year"]]
	if date1["month"] != date2["month"] :
		return (1, -1)[date1["month"] < date2["month"]]
	if date1["day"] != date2["day"] :
		return (1, -1)[date1["day"] < date2["day"]]
	if date1["hour"] != date2["hour"] :
		return (1, -1)[date1["hour"] < date2["hour"]]
	if date1["minute"] != date2["minute"] :
		return (1, -1)[date1["minute"] < date2["minute"]]
	if date1["second"] != date2["second"] :
		return (1, -1)[date1["second"] < date2["second"]]
	return 0

# --------
# get port
# --------

def getPort () :
	"""
    parse the port number from the command line; if failure, terminate program
    return an int value containing the port number
    """
	if len(argv) != 2 :
		print("Usage requires exactly one command line argument! python3 httpServer <port>")
		exit()
	return int(argv[1])

# ---------------
# request methods
# ---------------

def getRequest (socket) :
	"""
    receive bytes from a socket
    socket the socket of the client
    return a string containing the client's request
    """
	# receive the request
	request = socket.recv(MAX_FILE_SIZE)
	request = bytes.decode(request)
	return request

def parseRequest (request) :
	"""
    parse the pieces of the request, store in a dictionary
    request a string containing the client's request
    raise HTTPVersionNotSupportedException if anything but HTTP/1.1 is received
    raise NonGetRequestException if any method but GET is received
    raise BadRequestException if proper HTTP syntax is not upheld in request
    raise CoffeePotException if the BREW method is in the request
    return a dictionary
    """
	# dictionary to hold values
	details = {}
		# raise NotModifiedException
	try :

		# list of lines in request
		lines = request.split('\r\n')
		# components of line
		parts = lines[0].split(' ')
		details["method"] = parts[0].upper()
		if '/' == parts[1][0] :
			parts[1] = path + parts[1]
		else :
			parts[1] = path + '/' + parts[1]
		details["url"] = parts[1]
		details["version"] = parts[2].upper()

		print(details["method"] + " " + details["url"] + " " + details["version"])

		if details["method"] == "BREW" :
			raise CoffeePotException
		if details["version"] != "HTTP/1.1" :
			raise HTTPVersionNotSupportedException
		if details["method"] != "GET" :
			raise NonGetRequestException

		for line in lines :
			if "If-Modified-Since:" in line :
				trash, date = line.split("If-Modified-Since: ")
				details["if-modified-since"] = date
				break

	except IndexError :
		raise BadRequestException

	return details

# ------------
# file methods
# ------------

def openFile (fileName, openType) :
	"""
    open a file
    fileName the string name/path to the file
    openType a string indicating what mode of open to use
    raise NotFoundException if file does not exist
    return the opened file
    """
	try:
		inputfile = open(fileName, openType)
	except IOError:
		raise NotFoundException
	return inputfile

def openBinaryFile (fileName) :
	"""
    open a file in binary mode
    fileName the string name/path to the file
    return the opened file
    """
	# Supported files: JPEG (.jpg or .jpeg)
	inputFile = openFile(fileName, "rb")
	return inputFile.read()

def openTextFile (fileName) :
	"""
    open a text file
    fileName the string name/path to the file
    raise FileTypeNotSupportedException if contents cannot be extracted
    return the opened file
    """
	# Supported files: HTML (.html or .htm), text (.txt)
	inputFile = openFile(fileName, "r")
	try :
		fileContents = inputFile.read()
	except UnicodeDecodeError :
		raise FileTypeNotSupportedException
	return fileContents

def getFileType (fileName) :
	"""
    get the extension of the file
    fileName the string name of the file
    raise NotFoundException if file does not exist
    return a string
    """
	parts = fileName.split('.')
	if len(parts) == 0 :
		raise NotFoundException
	if len(parts) == 1 :
		return "txt"
	return parts[len(parts) - 1].lower()

# ----------------
# response methods
# ----------------

def getResponse (details) :
	"""
    create a string response containing the appropriate HTTP headers
    details a dictionary containing the header data
    return a string
    """
	# check if we are sending an image
	image = (False, True)[details["content-type"] == "image/jpeg"]
	response  = ""
	response += details["version"] + " " + details["code"] + endl
	response += "Date: " + getCurrentTimeString() + endl
	response += "Server: " + serverName + "/" + serverVersion + " (" + os.name + ")" + endl
	if details["code"] == codeDict[200] :
		response += "Last-Modified: " + details["modified"] + endl
	response += "Content-Length: " + str(len(details["content"])) + endl
	response += "Content-Type: " + details["content-type"] + endl
	response += endl
	if image :
		# encode the response, excluding the content
		response = response.encode()
	# add the content
	response += details["content"]
	if not image :
		# encode the response, including the content
		response = response.encode()
	return response

def returnResponse (response, socket) :
	"""
    send bytes over a socket
    response the bytes to send
    socket the client socket to use
    """
	# return the result to the client
	socket.send(response)

# ------
# listen
# ------

def listen () :
	"""
    listen for clients, accept the connection, handle the request, close the connection
    """
	while listening:

		# accept the connection to a client
		clientSocket, addr = serverSocket.accept()

		# obtain the request through the wire
		rawRequest = getRequest(clientSocket)

		# dictionary to hold the server's response
		responseDict = {
			"version" : "HTTP/1.1",
			"content-type" : "text/html"
		}

		try :

			# dictionary to hold client's request
			requestDict = parseRequest(rawRequest)

			try :

				# extract the contents of the file
				fileName = requestDict["url"]

				try :

					# check if the file has been modified since the cached copy
					cacheDate = timeStringDict(requestDict["if-modified-since"])
					modDate = timeStringDict(getModifiedTimeString(fileName))

					compare = compareDateTo(cacheDate, modDate)

					if compare == 1 :
						raise NotModifiedException

				except KeyError :
					pass

				except FileNotFoundError :
					raise NotFoundException

				fileType = getFileType(fileName)
				if fileType == "jpeg" or fileType == "jpg" :
					responseDict["content"] = openBinaryFile(fileName)
					responseDict["content-type"] = "image/" + fileType
				else :
					responseDict["content"] = openTextFile(fileName)
					responseDict["content-type"] = "text/" + fileType
				# exception thrown if unsuccessful
				print(codeDict[200])
				responseDict["code"] = codeDict[200]
				# obtain the time last modified
				responseDict["modified"] = getModifiedTimeString(requestDict["url"])

			except NotFoundException :
				# file not found
				print(codeDict[404])
				responseDict["content"] = responseDict["code"] = codeDict[404]

			except FileTypeNotSupportedException :
				# file not found
				print(codeDict[415])
				responseDict["content"] = responseDict["code"] = codeDict[415]

		except NotModifiedException :
			print(codeDict[304])
			responseDict["content"] = responseDict["code"] = codeDict[304]

		except NonGetRequestException :
			# not a GET request
			print(codeDict[405])
			responseDict["content"] = responseDict["code"] = codeDict[405]

		except BadRequestException :
			# invalid syntax or nonsense request
			print(codeDict[400])
			responseDict["content"] = responseDict["code"] = codeDict[400]

		except HTTPVersionNotSupportedException :
			# unsupported version of HTTP
			print(codeDict[505])
			responseDict["content"] = responseDict["code"] = codeDict[505]

		except CoffeePotException :
			# BREW request
			print(codeDict[418])
			responseDict["content"] = responseDict["code"] = codeDict[418]

		# add the headers to the response
		rawResponse = getResponse(responseDict)

		# send the response over the wire
		returnResponse(rawResponse, clientSocket)

		#close the connection
		clientSocket.close()

# ----
# main
# ----

print("------------")
print(serverName + "/" + serverVersion)
print("------------")

# define port number and socket
port = getPort()
serverSocket = socket(AF_INET, SOCK_STREAM)

# activate socket
serverSocket.bind(('', port))
serverSocket.listen(1)
listen()
Contact GitHub API Training Shop Blog About
© 2016 GitHub, Inc. Terms Privacy Security Status Help