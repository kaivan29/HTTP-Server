#!/usr/bin/env python3

# -------------------------------
# projects/collatz/TestCollatz.py
# Copyright (C) 2015
# Glenn P. Downing
# -------------------------------

# https://docs.python.org/3.4/reference/simple_stmts.html#grammar-token-assert_stmt

# -------
# imports
# -------

from io       import StringIO
from unittest import main, TestCase

from socket import *
import sys
import time
import os

serverName = 'localhost'
serverPort = 1200

def getCurrentTime () :
    return time.gmtime()

def getCurrentTimeString () :
    tnow = getCurrentTime()
    return time.strftime('%a, %d %b %Y %H:%M:%S GMT', tnow)

def getModifiedTime (fileName) :
    modtime = os.path.getmtime(fileName)
    return time.gmtime(modtime)

def getModifiedTimeString (fileName) :
    gmtime = getModifiedTime(fileName)
    return time.strftime('%a, %d %b %Y %H:%M:%S GMT', gmtime)

def parseResponse (request) :
    # dictionary to hold values
    details = {}

    # list of lines in request
    lines = request.split('\r\n')
    # components of line
    parts = lines[0].split(' ')

    details['version'] = parts[0]
    
    details['code'] = parts[1]

    parts = lines[1].split('Date: ')

    details['date'] = parts[1]

    if details['code'] == '200' :

        parts = lines[3].split('Last-Modified: ')

        details['last-modified'] = parts[1]

        parts = lines[5].split('Content-Type: ')

        details['content-type'] = parts[1]

    else :

        parts = lines[4].split('Content-Type: ')

        details['content-type'] = parts[1]

    return details

def getResponse (request) :
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName, serverPort))

    clientSocket.send(request.encode())
    modifiedSentence = clientSocket.recv(2048)
    try :

        response = modifiedSentence.decode()

    except UnicodeDecodeError :
        response = ""
        for byte in modifiedSentence :
            response += chr(byte)

    clientSocket.close()

    return parseResponse(response)

# ------------
# TestTastyTTP
# ------------

class TestTastyTTP (TestCase) :

    # ---
    # 200
    # ---

    def test_code_200_1 (self) :

        request = "GET /testfiles/index.html HTTP/1.1"

        responseDict = getResponse(request)

        self.assertEqual('200', responseDict['code'])

    def test_code_200_2 (self) :

        request = "GET /testfiles/tiny.jpeg HTTP/1.1"

        responseDict = getResponse(request)

        self.assertEqual('200', responseDict['code'])

    def test_code_200_3 (self) :

        request = "GET /testfiles/index.html HTTP/1.1\r\nIf-Modified-Since: Mon, 19 Oct 2005 07:01:06 GMT"

        responseDict = getResponse(request)

        self.assertEqual('200', responseDict['code'])

    # ---
    # 304
    # ---

    def test_code_304_1 (self) :

        request = "GET /testfiles/index.html HTTP/1.1\r\nIf-Modified-Since: " + getCurrentTimeString()

        responseDict = getResponse(request)

        self.assertEqual('304', responseDict['code'])

    def test_code_304_2 (self) :

        request = "GET /testfiles/index.html HTTP/1.1\r\nIf-Modified-Since: Mon, 19 Oct 2025 07:01:06 GMT"

        responseDict = getResponse(request)

        self.assertEqual('304', responseDict['code'])

    # ---
    # 400
    # ---

    def test_code_400_1 (self) :

        request = "BAD REQUEST"

        responseDict = getResponse(request)

        self.assertEqual('400', responseDict['code'])

    def test_code_400_2 (self) :

        request = "GET HTTP/1.1"

        responseDict = getResponse(request)

        self.assertEqual('400', responseDict['code'])

    def test_code_400_3 (self) :

        request = "GET /testfiles/index.html"

        responseDict = getResponse(request)

        self.assertEqual('400', responseDict['code'])

    # ---
    # 405
    # ---

    def test_code_405_1 (self) :

        request = "POST / HTTP/1.1"

        responseDict = getResponse(request)

        self.assertEqual('405', responseDict['code'])

    def test_code_405_2 (self) :

        request = "HEAD /NonexistentFile HTTP/1.1"

        responseDict = getResponse(request)

        self.assertEqual('405', responseDict['code'])

    # ---
    # 404
    # ---

    def test_code_404_1 (self) :

        request = "GET / HTTP/1.1"

        responseDict = getResponse(request)

        self.assertEqual('404', responseDict['code'])

    def test_code_404_2 (self) :

        request = "GET /NonexistentFile HTTP/1.1"

        responseDict = getResponse(request)

        self.assertEqual('404', responseDict['code'])

    def test_code_404_3 (self) :

        request = "GET /NonexistentFile.jpeg HTTP/1.1"

        responseDict = getResponse(request)

        self.assertEqual('404', responseDict['code'])

    # ---
    # 418
    # ---

    def test_code_418_1 (self) :

        request = "BREW / HTCPCP/1.0"

        responseDict = getResponse(request)

        self.assertEqual('418', responseDict['code'])

    # ---
    # 505
    # ---

    def test_code_505_1 (self) :

        request = "GET /testfiles/index.html HTTP/1.0"

        responseDict = getResponse(request)

        self.assertEqual('505', responseDict['code'])

    def test_code_505_2 (self) :

        request = "GET /NonexistentFile HTTP/1.0"

        responseDict = getResponse(request)

        self.assertEqual('505', responseDict['code'])

    # -------
    # version
    # -------

    def test_version_1 (self) :

        request = "GET /NonexistentFile HTTP/1.0"

        responseDict = getResponse(request)
        self.assertEqual('HTTP/1.1', responseDict['version'])

    def test_version_2 (self) :

        request = "GET /NonexistentFile HTTP/1.1"

        responseDict = getResponse(request)

        self.assertEqual('HTTP/1.1', responseDict['version'])

    def test_version_3 (self) :

        request = "GET /testfiles/index.html HTTP/1.1"

        responseDict = getResponse(request)

        self.assertEqual('HTTP/1.1', responseDict['version'])

    def test_version_4 (self) :

        request = "BREW / HTCPCP/1.0"

        responseDict = getResponse(request)

        self.assertEqual('HTTP/1.1', responseDict['version'])

    # ----
    # date
    # ----

    def test_date_1 (self) :

        request = "GET /NonexistentFile HTTP/1.0"

        responseDict = getResponse(request)

        self.assertEqual(getCurrentTimeString(), responseDict['date'])

    def test_date_2 (self) :

        request = "GET /NonexistentFile HTTP/1.1"

        responseDict = getResponse(request)

        self.assertEqual(getCurrentTimeString(), responseDict['date'])

    def test_date_3 (self) :

        request = "GET /testfiles/index.html HTTP/1.1"

        responseDict = getResponse(request)

        self.assertEqual(getCurrentTimeString(), responseDict['date'])

    # -------------
    # last-modified
    # -------------

    def test_last_modified_1 (self) :

        request = "GET /testfiles/index.html HTTP/1.1"

        responseDict = getResponse(request)

        self.assertEqual('200', responseDict['code'])
        self.assertEqual(getModifiedTimeString("testfiles/index.html"), responseDict['last-modified'])

    def test_last_modified_2 (self) :

        request = "GET /testfiles/tiny.jpeg HTTP/1.1"

        responseDict = getResponse(request)

        self.assertEqual('200', responseDict['code'])
        self.assertEqual(getModifiedTimeString("testfiles/tiny.jpeg"), responseDict['last-modified'])

    # ------------
    # content-type
    # ------------

    def test_content_type_1 (self) :

        request = "GET /testfiles/index.html HTTP/1.1"

        responseDict = getResponse(request)

        self.assertEqual('200', responseDict['code'])
        self.assertEqual('text/html', responseDict['content-type'])

    def test_content_type_2 (self) :

        request = "GET /testfiles/tiny.jpeg HTTP/1.1"

        responseDict = getResponse(request)

        self.assertEqual('200', responseDict['code'])
        self.assertEqual('image/jpeg', responseDict['content-type'])

# ----
# main
# ----

if __name__ == "__main__" :
    main()
