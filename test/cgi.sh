#!/bin/sh

export REQUEST_METHOD="GET"
export SERVER_NAME="localhost"
export SERVER_PORT="8080"
export SERVER_PROTOCOL="HTTP/1.0"
export REQUEST_URI="" #U: params
export PATH_INFO="/heroes/" #U: the url = handler

cd ../src #U: very important, change to the app directory
./main.cgi 
