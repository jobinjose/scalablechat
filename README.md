Simple Chat server implemented in Python 3

Submitted by:
Student Name: Jobin Jose
Student ID: 17312296
Student e-mail: josej@tcd.ie

The IP address of the default machine in which server code is run in SCSSnebula is 10.62.0.93



start.sh contents:
git pull
#to pull the latest commit to the local repo

python3 chatserver.py $1
#to execute the chatserver with one argument taken as the port number



The following libraries are used in the program:
socket
#Low-level networking interface

sys
#for getting port number as argument and for sys.exit() in case of errors

queue
#to store the message Queue

threading
#to implement threads

re
#for regular expression

random
#generating random nums
