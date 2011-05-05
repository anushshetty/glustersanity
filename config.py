#!/usr/bin/python                                                                                                                                           
import os
import string
import sys
import commands
import time
import datetime

START_TIMESTR = time.strftime("%d-%b-%Y-%H-%M-%S", time.localtime())
BRICKS_IPADDRS=[]
SERVER_EXPORT='/mnt/sanity'
TRANSPORT='tcp'
NUM_BRICKS='1'
REPLICA= True
RUNTESTS= True
SETUPBRICKS = False
VOL_PAR=""
NFSSERVER_ADDR=''
FUSE=False
TESTVOLUME=['testvol']
MOUNTPOINT = "/tmp/sanity-testsdir-"+START_TIMESTR+"/"
LOGFILE = "/tmp/testbot-log-"
LOGSCPURL = ""
LOGDOWNLOADURL = "http://shell.gluster.com/~anush/testbot"
MAILUSER = "anush@gluster.com"
MAILPWD = ""
MAILSRV = "localhost"
MAILTO = "anushshetty@gluster.com"
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
EMAILCONTROLLOG = False
