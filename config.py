#!/usr/bin/python                                                                                                                                           
import os
import string
import sys
import commands
import time
import datetime

START_TIMESTR = time.strftime("%d-%b-%Y-%H-%M-%S", time.localtime())
BRICKS_IPADDRS=['192.168.1.55']
SERVER_EXPORT='/mnt/'
TRANSPORT='tcp'
NUM_BRICKS=1
REPLICA= False
RUNTESTS= True
SETUPBRICKS = False
VOL_PAR=""
NFSSERVER_ADDR=''
FUSE=True
TESTVOLUME=['testvol']

CLIENT_IP='192.168.1.55'
MOUNTPOINT = "/tmp/sanity-testsdir-"+START_TIMESTR+"/"

LOGFILE = "/tmp/testbot-log-"
LOGSCPURL = ""
LOGDOWNLOADURL = "http://shell.gluster.com/~anush/testbot"

MAILUSER = "anush@gluster.com"
MAILPWD = ""
MAILSRV = "localhost"
MAILRECIEVER = "anushshetty@gmail.com"

TESTVOLUMES = []
START = time.time()
START_TIMESTR = time.strftime("%d-%b-%Y-%H-%M-%S", time.localtime())
END = None
SRC_DOWNLOAD_DIR = "/tmp/sanity-glusterfs-"+START_TIMESTR+"/"
CONTROL_LOGFILE = "/tmp/sanity-control-log-"+START_TIMESTR
TESTS_DOWNLOAD_DIR = "/tmp/sanitytools-"+START_TIMESTR+"/"
TESTBOT_DOWNLOAD_DIR = "/tmp/shehjart-testbot-"+START_TIMESTR+"/"
DAEMONIZE = True
TESTTYPE = ""
TESTNAMES = ["dbench"]
EMAILCONTROLLOG = True
