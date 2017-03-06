from socket import *
import sys

serverName = sys.argv[1]
serverPort = int(sys.argv[2])
filename = sys.argv[3]

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName,serverPort))

message = 'GET ' + filename + ' HTTP/1.1 ' + 'Junk\r\n'
message += 'Host: www.cs.utexas.edu\r\n\r\n'  
clientSocket.send(message.encode())
response = clientSocket.recv(2048)
print ('From Server:' + response.decode())
clientSocket.close()