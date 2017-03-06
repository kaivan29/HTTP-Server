#tcp client

from socket import *
serverName = 'localhost'
serverPort = input('Please enter the port number: ')

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, int(serverPort)))

filename = input('input something: ')
clientSocket.send(filename.encode())

rawContent = clientSocket.recv(8192)
content = rawContent.decode()
lines = content.split('\n')
print(len(lines))
for val in lines:
	print(val + '\n')
clientSocket.close()