#Project 1 HTTP server
#Name: Kaivan Shah
#EID: kks942

from socket import *
from datetime import datetime
from time import mktime
import time
import os
import sys

serverPort = sys.argv[1]
serverName = 'localhost'
path = os.path.dirname(os.path.abspath(__file__))   #get the pathname of the file

serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('',int(serverPort)))
serverSocket.listen(1)

print('The server is ready...')

#Type of content allowed
contentType = {
	'txt':'text/plain',
	'htm':'text/html',
	'html':'text/html',
	'jpeg':'image/jpeg',
	'jpg':'image/jpeg'}

#checks a string representing the date against all valid http
#date time/date formats, returns a time struct if the string is
#valid, None otherwise
def getTime(timeString):
	date = None
	try:
		date = time.strptime(timeString, '%a, %d %b %Y %H:%M:%S %Z')
	except ValueError:
		try:
			date = time.strptime(timeString)
		except ValueError:
			try:
				date = time.strptime(timeString, '%A, %d-%b-%y %H:%M:%S %Z')
			except ValueError:
				return None
	return date

#To check if the file was modified since the last request
def if_modified(lines):
	for line in lines:
		#Checks the request to see if If-Modified-Since exists or not
		if 'If-Modified-Since:' in line:
			time = line.split('If-Modified-Since: ')
			raw_time = getTime(time[1])
			#return the time in datetime format
			dt = datetime.fromtimestamp(mktime(raw_time))
			#print(dt)
			return dt	

#Determine the response message according to the status code
def response(statusCode):
	#Calculate current time
	tnow = time.gmtime()
	tnowstr = time.strftime('%a, %d %b %Y %H:%M:%S %Z', tnow)
	date = 'Date: ' + tnowstr + '\r\n'
	server = 'Server: ' + serverName + '\r\n'
	#print(modified_time)
	if statusCode == 200:
		#status code and status response
		value = 'HTTP/1.1 200 OK\r\n'
		#calculate modified time
		return value+date+server
	elif statusCode == 304:
		value = 'HTTP/1.1 304 Not Modified\r\n'
	elif statusCode == 404:
		value = 'HTTP/1.1 404 Not Found\r\n'
	elif statusCode == 415:
		value = 'HTTP/1.1 415 Media Type Not Supported\r\n'
	elif statusCode == 505:
		value = 'HTTP/1.1 505 HTTP Version Not Supported\r\n'
	elif statusCode == 400:
		value = 'HTTP/1.1 400 Bad Request\r\n'
	elif statusCode == 405:
		value = 'HTTP/1.1 405 Method Not Allowed\r\n'
	return value+date+server

#Keeps listening until a client sends a request
while 1:
	connectionSocket, addr = serverSocket.accept()
	message = connectionSocket.recv(8192)
	request = message.decode()
	length = len(request)
	if length == 0:
		#odd chrome thing so close and continue
		print('Zero length message')
		connectionSocket.close()
		continue
	else:
		#To get the header, request body and content
		lines = request.split('\r\n')
		#To split the header
		request_line = lines[0].split(' ')
		#Checking if the request header is correct
		if(len(request_line) == 3):
			if(request_line[0] == 'GET'):
				if(request_line[2] == 'HTTP/1.1'):
					filename = request_line[1]
					if(filename[0]!='/'): filename = '/'+ filename
					s = filename.find('.')
					#valid types of file allowed
					if filename[s:] in ('.htm','.jpeg','.jpg','.txt','.html'):			
						try:
							#Get the last modified time
							m_time = time.gmtime(os.path.getmtime(path))
							dt = datetime.fromtimestamp(mktime(m_time))
							#To check if the file requested again has been modified or not
							if(if_modified(lines) == dt):
								msg = response(304)
								connectionSocket.send(msg.encode())
							else:
								#if the file is valid, its content are read
								inputfile = open(filename[1:], 'rb')
								#I read it here as binary, so it is already in bytes. And hence no need to encode it
								content = inputfile.read()
								m_time= time.strftime('%a, %d %b %Y %H:%M:%S %Z', m_time)
								modified_time = 'Last-Modified: ' + m_time + '\r\n'
								content_length = 'Content-Length: ' + str(len(content)) + '\r\n'
								content_type = 'Content-Type: ' + contentType[filename[s+1:]] + '\r\n\r\n'
								msg = response(200) + modified_time + content_length + content_type
								connectionSocket.send(msg.encode())
								connectionSocket.send(content)
						except IOError:
							#If the file does not exist
							msg = response(404)
							connectionSocket.send(msg.encode())
					else:
						#invalid file type
						msg = response(415)
						connectionSocket.send(msg.encode())
				else:
					#wrong http version
					msg = response(505)
					connectionSocket.send(msg.encode())
			else:
				#Nothing other than get method is allowed
				msg = response(405)
				connectionSocket.send(msg.encode())
		else:
			#Bad request
			msg = response(400)
			connectionSocket.send(msg.encode())
		connectionSocket.close()