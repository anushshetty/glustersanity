#!/usr/bin/python

import os
import string
import sys
import commands
import time
import datetime
import socket

from config import *
from multiprocessing import Process,Pipe,Event
from OpenSSL.SSL import SSLv3_METHOD
from twisted.mail.smtp import ESMTPSenderFactory
from twisted.python.usage import Options, UsageError
from twisted.internet.ssl import ClientContextFactory
from twisted.internet.defer import Deferred
from twisted.internet import reactor

PATCHFILE=""

def LogSummary (logline):
        CONTROL_LOG.write(logline)
#        if CONTROL_LOG <> sys.stdout:
#                sys.stdout.write(logline)
        CONTROL_LOG.flush()

def create_bricks():
    VOL_PAR=""
    if REPLICA:
	    VOL_PAR +=" replica 2"

    if TRANSPORT:
	    VOL_PAR +=" transport " + TRANSPORT

    if len(BRICKS_IPADDRS) == 1:
	    if REPLICA:
		    NUM_BRICKS=2
	    NUM_BRICKS=int(NUM_BRICKS)
	    for i in range(NUM_BRICKS):
		    VOL_PAR += " " + BRICKS_IPADDRS[0] + ":" + SERVER_EXPORT + "/"+ str(i)
    else:
	    for i in BRICKS_IPADDRS:
		    VOL_PAR += " " + i + ":" + SERVER_EXPORT + "/1"
    return VOL_PAR

	
def sendmail(
    authenticationUsername, authenticationSecret,
    fromAddress, toAddress,
    messageFile,
    smtpHost, smtpPort=25
    ):
    """
    @param authenticationUsername: The username with which to authenticate.
    @param authenticationSecret: The password with which to authenticate.
    @param fromAddress: The SMTP reverse path (ie, MAIL FROM)
    @param toAddress: The SMTP forward path (ie, RCPT TO)
    @param messageFile: A file-like object containing the headers and body of
    the message to send.
    @param smtpHost: The MX host to which to connect.
    @param smtpPort: The port number to which to connect.

    @return: A Deferred which will be called back when the message has been
    sent or which will errback if it cannot be sent.
    """
   
    # Create a context factory which only allows SSLv3 and does not verify
    # the peer's certificate.
    contextFactory = ClientContextFactory()
    contextFactory.method = SSLv3_METHOD

    resultDeferred = Deferred()

    senderFactory = ESMTPSenderFactory(
        authenticationUsername,
        authenticationSecret,
        fromAddress,
        toAddress,
        messageFile,
        resultDeferred,
        contextFactory=contextFactory)

    reactor.connectTCP(smtpHost, smtpPort, senderFactory)

    return resultDeferred


def cbSentMessage(result):
    """
    Called when the message has been sent.

    Report success to the user and then stop the reactor.
    """
    reactor.stop()


def ebSentMessage(err):
    """
    Called if the message cannot be sent.

    Report the failure to the user and then stop the reactor.
    """
    reactor.stop()


def SendResultsInMail ():
        CONTROL_LOG.close()
        log = file (CONTROL_LOGFILE)
	print CONTROL_LOGFILE
        result = sendmail(MAILUSER, MAILPWD, MAILUSER, MAILTO, log, MAILSRV)
        result.addCallbacks(cbSentMessage, ebSentMessage)
        reactor.run()


def WriteLog(logline):
        LOGFILEFD.write(logline)
        LOGFILEFD.flush()
        return


def WriteBrickLog(logpipe, brick, loglines):
        timestr = time.strftime("%a %H:%M:%S %d/%m/%y", time.localtime())
        loglist = loglines.split("\n")
        for line in loglist:
                newline = brick + " " + timestr + " -- " + line + "\n"
                logpipe.send (newline)

        return


def WaitForAllEvents(events):
        for ev in events.values():
                ev.wait()

def SetupBrick(brick, controlpipe, startvols, eventlist):
        LogSummary("Cloning repo on " +  brick +"\n")
        WriteBrickLog (controlpipe, brick, "Cloning repo on " + brick)
        (status, output) = commands.getstatusoutput("ssh root@"+brick+" cd /tmp\;git clone git://github.com/gluster/glusterfs.git "+SRC_DOWNLOAD_DIR);
        WriteBrickLog (controlpipe, brick, output)

        if status <> 0:
                LogSummary("Cloning repo on " +  brick + "..FAILED\n")
                WriteBrickLog (controlpipe, brick, "Cloning repo on " +  brick + "..FAILED")
                sys.exit(-1)
        else:
                LogSummary("Cloning repo on " +  brick + "..DONE\n")
                WriteBrickLog (controlpipe, brick, "Cloning repo on " +  brick + "..DONE")

        if len(PATCHFILE) > 0:
                LogSummary("Uploading patch " +  brick+"\n")
                WriteBrickLog (controlpipe, brick, "Uploading patch " +  brick) 
                (status, output) = commands.getstatusoutput("scp " + PATCHFILE + " root@"+brick+":"+SRC_DOWNLOAD_DIR+"\;");
                WriteBrickLog (controlpipe, brick, output)

                if status <> 0:
                        WriteBrickLog (controlpipe, brick, "Uploading patch " +  brick + "..FAILED")
                        LogSummary("Uploading patch " +  brick + "..FAILED\n")
                        sys.exit(-1)
                else:
                        LogSummary("Uploading patch " +  brick + "..DONE\n")
                        WriteBrickLog (controlpipe, brick, "Uploading patch " +  brick + "..DONE")

                LogSummary("Applying patch: " + PATCHFILE + " on " + brick +"\n")
                WriteBrickLog (controlpipe, brick, "Applying patch: " + PATCHFILE + " on " + brick) 
                (status, output) = commands.getstatusoutput("ssh root@"+brick+" cd "+SRC_DOWNLOAD_DIR+"\;git am " + os.path.basename(PATCHFILE));
                WriteBrickLog (controlpipe, brick, output)

                if status <> 0:
                        LogSummary("Applying patch: " + PATCHFILE + " on " + brick + "..FAILED\n")
                        WriteBrickLog (controlpipe, brick, "Applying patch: " + PATCHFILE + " on " + brick + "..FAILED")
                        sys.exit(-1)
                else:
                        LogSummary("Applying patch: " + PATCHFILE + " on " + brick + "..DONE\n")
                        WriteBrickLog (controlpipe, brick, "Applying patch: " + PATCHFILE + " on " + brick + "..DONE")

        LogSummary("Running autogen on " + brick +"\n")
        WriteBrickLog (controlpipe, brick, "Running autogen on " + brick)
        (status, output) = commands.getstatusoutput("ssh root@"+brick+" cd "+SRC_DOWNLOAD_DIR+"\;./autogen.sh\;");
        WriteBrickLog (controlpipe, brick, output)

        if status <> 0:
                LogSummary("Running autogen on " + brick + "..FAILED\n")
                WriteBrickLog (controlpipe, brick, "Running autogen on " + brick + "..FAILED")
                sys.exit(-1)
        else:
                LogSummary("Running autogen on " + brick + "..DONE\n")
                WriteBrickLog (controlpipe, brick, "Running autogen on " + brick + "..DONE")

        LogSummary("Running configure on " + brick+"\n")
        WriteBrickLog (controlpipe, brick, "Running configure on " + brick)
        (status, output) = commands.getstatusoutput("ssh root@"+brick+" cd "+SRC_DOWNLOAD_DIR+"\;./configure\;");
        WriteBrickLog (controlpipe, brick, output)

        if status <> 0:
                LogSummary("Running configure on " + brick + "..FAILED\n")
                WriteBrickLog (controlpipe, brick, "Running configure on " + brick + "..FAILED")
                sys.exit(-1)
        else:
                LogSummary("Running configure on " + brick + "..DONE\n")
                WriteBrickLog (controlpipe, brick, "Running configure on " + brick + "..DONE")

        LogSummary("Building and installing on " + brick +"\n")
        WriteBrickLog (controlpipe, brick, "Building and installing on " + brick)
        (status, output) = commands.getstatusoutput("ssh root@"+brick+" cd "+SRC_DOWNLOAD_DIR+"\;make install\;");
        WriteBrickLog (controlpipe, brick, output)

        if status <> 0:
                LogSummary("Building and installing on " + brick + "..FAILED\n")
                WriteBrickLog (controlpipe, brick, "Building and installing on " + brick + "..FAILED")
                sys.exit(-1)
        else:
                LogSummary ("Building and installing on " + brick + "..DONE\n")
                WriteBrickLog (controlpipe, brick, "Building and installing on " + brick + "..DONE")

        LogSummary("Cleaning source dir on " + brick +"\n")
        WriteBrickLog (controlpipe, brick, "Cleaning source dir on " + brick)
        (status, output) = commands.getstatusoutput("ssh root@"+brick+" rm -rf "+SRC_DOWNLOAD_DIR+"\;");
        WriteBrickLog (controlpipe, brick, output)

        if status <> 0:
                LogSummary("Cleaning source dir on " + brick + "..FAILED\n")
                WriteBrickLog (controlpipe, brick, "Cleaning source dir on " + brick + "..FAILED")
                sys.exit(-1)
        else:
                LogSummary ("Cleaning source dir on " + brick + "..DONE\n")
                WriteBrickLog (controlpipe, brick, "Cleaning source dir on " + brick + "..DONE")


def NextChan (procs):
        for (proc, mychan, brickchan) in procs:
                if mychan.poll():
                        return mychan

        return None

def AllDone (procs):
        status = False

        for (proc, mychan, brickchan) in procs:
                if proc.exitcode is None:
                        return status

        return True


def AnyProcessFailed (procs):
        
        for (proc, mychan, brickchan) in procs:
                if proc.exitcode is not None:
                        if proc.exitcode <> 0:
                                return (proc, mychan, brickchan)

        return None


def TerminateProcs(procs):

        for (proc, mychan, brickchan) in procs:
                proc.terminate()


def StartProcs(allprocs):
        for (proc, mychan, brickchan) in allprocs:
                proc.start()

def RunProcMonitorLoop(allprocs):
        alldone = False

        StartProcs(allprocs)
        procinfo = AnyProcessFailed(allprocs)
        while procinfo is None:
                chan = NextChan (allprocs)

                if chan is None:
                        if AllDone(allprocs):
                                alldone = True
                                break
                        else:
                                time.sleep(1)
                else:
                        WriteLog (chan.recv())

                procinfo = AnyProcessFailed(allprocs)

        if not alldone:
                (proc, mychan, brickchan) = procinfo
                while mychan.poll():
                        log = mychan.recv()
                        WriteLog (log)
                        time.sleep(1)

                TerminateProcs(allprocs)

        return alldone

def SetupBricks():
        allsuccess = False
        allprocs = []
        startvols = False

        events = {}
        ev = None
        for brick in BRICKS_IPADDRS: 
                ev = Event ()
                ev.clear()
                events[brick] = ev

        for brick in BRICKS_IPADDRS: 
                mychan,brickchan = Pipe()
                startvols = False
                if brick == NFSSERVER_ADDR:
                        startvols = True
                proc = Process (target=SetupBrick, args=(brick, brickchan, startvols, events,))
                allprocs.append ((proc, mychan, brickchan))

        if FUSE:
                ev = Event ()
                ev.clear()
                events[NFSCLIENT_ADDR] = ev
                mychan,brickchan = Pipe()
                startvols = False
                proc = Process (target=SetupBrick, args=(NFSCLIENT_ADDR, brickchan, startvols, events,))
                allprocs.append ((proc, mychan, brickchan))

        allsuccess = RunProcMonitorLoop(allprocs)
        return allsuccess

def StartUpVolumesOnBrick (brick, controlpipe, startvols, eventlist):

        LogSummary("Stopping NFS server on " + brick+"\n")
        WriteBrickLog (controlpipe, brick, "Stopping NFS server on " + brick)
        (status, output) = commands.getstatusoutput("ssh root@"+brick+" /etc/init.d/nfs-kernel-server stop\;/etc/init.d/nfs stop\;/etc/init.d/portmap stop\; /etc/init.d/portmap start\;/etc/init.d/rpcbind stop\;/etc/init.d/rpcbind start\;");
        WriteBrickLog (controlpipe, brick, output)

        if startvols:

                for volume in TESTVOLUME:
                        LogSummary("Stopping volume " + volume + " on " + brick +"\n")
                        WriteBrickLog (controlpipe, brick, "Stopping volume " + volume + " on " + brick)
                        (status, output) = commands.getstatusoutput("ssh root@"+brick+" gluster volume stop " +volume+" --mode=script\;")

                (status, output) = commands.getstatusoutput("ssh root@"+brick+" killall glusterd\;killall glusterfs\;killall glusterfsd\;");
                LogSummary("Stopping volumes on " + brick + "..DONE\n")
                WriteBrickLog (controlpipe, brick, "Stopping volumes on " + brick +"..DONE")
                WriteBrickLog (controlpipe, brick, output)
                eventlist[NFSSERVER_ADDR].set()
        else:
                LogSummary (brick+ " waiting for "+NFSSERVER_ADDR+" to stop volumes\n")
                WriteBrickLog (controlpipe, brick, "Waiting for "+NFSSERVER_ADDR+" to stop volumes")
                eventlist[NFSSERVER_ADDR].wait()
                LogSummary ("Stopping glusterd on " + brick +"\n")
                WriteBrickLog (controlpipe, brick, "Stopping glusterd on " + brick)
                (status, output) = commands.getstatusoutput("ssh root@"+brick+" killall glusterd\;");
                WriteBrickLog (controlpipe, brick, output)


        LogSummary ("Starting glusterd on " + brick + "\n")
        WriteBrickLog (controlpipe, brick, "Starting glusterd on " + brick)
        (status, output) = commands.getstatusoutput("ssh root@"+brick+" killall glusterfs\; killall glusterfsd\; killall glusterd\; rm -rf /etc/glusterd\; glusterd\;");
        WriteBrickLog (controlpipe, brick, output)


        if status <> 0:
                print "Starting glusterd on " + brick + "..FAILED"
                WriteBrickLog (controlpipe, brick, "Starting glusterd on " + brick + "..FAILED")
                sys.exit(-1)
        else:
                LogSummary ("Starting glusterd on " + brick + "..DONE\n")
                WriteBrickLog (controlpipe, brick, "Starting glusterd on " + brick + "..DONE")

        if not startvols:
                LogSummary(brick + " told " + NFSSERVER_ADDR + " it can start volumes now\n")
                WriteBrickLog (controlpipe, brick, brick + " told " + NFSSERVER_ADDR + " it can start volumes now")
                eventlist[brick].set()
        else:
                LogSummary(NFSSERVER_ADDR + " waiting for remaining bricks to start glusterd\n")
                WriteBrickLog (controlpipe, brick, NFSSERVER_ADDR + " waiting for remaining bricks to start glusterd")
                WaitForAllEvents(eventlist)
                LogSummary("All bricks started glusterd..Starting volumes on " + brick + "\n")
                WriteBrickLog (controlpipe, brick, "All bricks started glusterd..Starting volumes on " + brick)

                for volume in TESTVOLUME:
			LogSummary("Creating volume " + volume +" on " + brick + "\n")
                        WriteBrickLog (controlpipe, brick, "Create volume " + volume + " on " + brick)
                        (status, output) = commands.getstatusoutput("ssh root@"+brick+" gluster volume create " + volume + " " + str(VOL_PAR) + "\;")
			WriteBrickLog (controlpipe, brick, output)

                        LogSummary("Starting volume " +volume +" on " + brick + "\n")
                        WriteBrickLog (controlpipe, brick, "Starting volume " + volume + " on " + brick)
                        (status, output) = commands.getstatusoutput("ssh root@"+brick+" gluster volume start " + volume+"\;")
                        WriteBrickLog (controlpipe, brick, output)

                        if status <> 0:
                                LogSummary("Starting volume " +volume+" on " + brick + "..FAILED\n")
                                WriteBrickLog (controlpipe, brick, "Starting volume "+ volume+" on " + brick + "..FAILED")
                                sys.exit(-1)
                        else:
                                LogSummary ("Starting volume "+volume+" on " + brick + "..DONE\n")
                                WriteBrickLog (controlpipe, brick, "Starting volume " + volume+" on " + brick + "..DONE")

			time.sleep(5)

			if FUSE:
				LogSummary("Mounting FUSE client on  " + NFSCLIENT_ADDR + "\n")
                                WriteBrickLog (controlpipe, brick, "Mounting FUSE client on  " + NFSCLIENT_ADDR)
                                (status, output) = commands.getstatusoutput("ssh root@"+NFSCLIENT_ADDR+ " mkdir -p " + MOUNTPOINT + "\; glusterfs -s " + NFSSERVER_ADDR + " --volfile-id=" + volume + "  " + MOUNTPOINT + "\;")
                                WriteBrickLog (controlpipe, brick, output)
                                
			else:
				LogSummary("Mounting NFS client on  " + NFSCLIENT_ADDR + "\n")
				WriteBrickLog (controlpipe, brick, "Mounting NFS client on  " + NFSCLIENT_ADDR)
				(status, output) = commands.getstatusoutput("ssh root@"+NFSCLIENT_ADDR+ " mkdir -p " + MOUNTPOINT + "\; mount "+ NFSCLIENT_ADDR + ":/" + volume + " " + MOUNTPOINT + "\;")
				WriteBrickLog (controlpipe, brick, output)

				if status <> 0:
					LogSummary("Mounting NFS Client on" + NFSCLIENT_ADDR + "..FAILED\n")
					WriteBrickLog (controlpipe, brick, "Mounting NFS Client on " + NFSCLIENT_ADDR + "..FAILED")
					sys.exit(-1)
				else:
					LogSummary("Mounting NFS Client on" + NFSCLIENT_ADDR + "..DONE\n")
                                        WriteBrickLog (controlpipe, brick, "Mounting NFS Client on " + NFSCLIENT_ADDR + "..DONE")


def StartUpVolumesOnBricks():
        allprocs = []
        startvols = False
        allsuccess = False

        events = {}
        ev = None
        for brick in BRICKS_IPADDRS: 
                ev = Event ()
                ev.clear()
                events[brick] = ev

        for brick in BRICKS_IPADDRS: 
                mychan,brickchan = Pipe()
                startvols = False
                if brick == NFSSERVER_ADDR:
                        startvols = True
                proc = Process (target=StartUpVolumesOnBrick, args=(brick, brickchan, startvols, events,))
                allprocs.append ((proc, mychan, brickchan))

        allsuccess = RunProcMonitorLoop(allprocs)
        return allsuccess

def DoToolsCheck():
        return


def frametestcommand(testinfo, volume):
        cmd = []
        cmd.append (TESTBOT_DOWNLOAD_DIR+"/testrunner.py")
        cmd.append ("-t")
        cmd.append (testinfo)
        cmd.append ("-s")
        cmd.append (NFSSERVER_ADDR)
        cmd.append ("-e")
        cmd.append (volume)
        cmd.append ("-m")
        cmd.append (MOUNTPOINT)

        return string.join(cmd, " ")


def RunTestFromList(testarg):
	LogSummary("############# RUNNING " + testarg + " ###############\n")
        WriteLog("############# RUNNING " + testarg + " ###############\n")
	(status, output) = commands.getstatusoutput("ssh root@"+NFSCLIENT_ADDR+" " + TESTS_DOWNLOAD_DIR + "/jobs.sh " + testarg + " "  + MOUNTPOINT +" \;");
	if status <> 0:
		LogSummary("Dbench failed\n")
                WriteLog ("Dbench..FAILED")
		sys.exit(-1)
	else:
                LogSummary("Dbench..DONE\n")
		WriteLog ("Dbench..DONE")
	
def RunTests():
        LogSummary("############# RUNNING TESTS ###############\n")
        WriteLog("############# RUNNING TESTS ###############\n")
	(status, output) = commands.getstatusoutput("ssh root@"+NFSCLIENT_ADDR+" git clone git://github.com/anushshetty/glustersanitytools.git "+TESTS_DOWNLOAD_DIR+"\;");

        for testitem in TESTNAMES:
                RunTestFromList(testitem);
	LogSummary("Umounting client " + MOUNTPOINT + "\n")
        WriteLog("Umounting client " + MOUNTPOINT + "\n")
	(status, output) = commands.getstatusoutput("ssh root@"+NFSCLIENT_ADDR+" rm -rf " + MOUNTPOINT + "\; rm -rf "+TESTS_DOWNLOAD_DIR+"\;  umount " + MOUNTPOINT + "\;");
	if status <> 0:
                LogSummary("Umount failed\n")
                WriteLog("Umount..FAILED")
                sys.exit(-1)
	else:
                LogSummary("Umount..DONE\n")
                WriteLog ("Umount..DONE")



def ReportResults():
        END = time.time()
        td = datetime.timedelta (seconds=(END-START))
        LogSummary("Time taken: " + str(td) + "\n")
        WriteLog("Time taken: " + str(td) + "\n")

        LOGFILEFD.close()
        if len(LOGSCPURL) > 0:
#                LogSummary ("Copying log to " + LOGSCPURL + "\n")
#                WriteLog ("Copying log to " + LOGSCPURL + "\n")
                (status, output) = commands.getstatusoutput ("scp " + LOGFILE + " " + LOGSCPURL)

#                if status <> 0:
#                        LogSummary("Copying log to " + LOGSCPURL + "..FAILED\n")
#                        WriteLog ("Copying log to " + LOGSCPURL + "..FAILED\n")
#                else:
#                        LogSummary("Copying log to " + LOGSCPURL + "..DONE\n")
#                        WriteLog ("Copying log to " + LOGSCPURL + "..DONE\n")

        if EMAILCONTROLLOG:
                SendResultsInMail()

def main():
        DoToolsCheck()
        retval = False

        if DAEMONIZE:
                try:
                        pid = os.fork()
                        if pid > 0:
                                sys.exit(0)

                except OSError, e:
                        print "Fork failed: %s" % e.strerror
                        sys.exit(1)

                os.setsid()

        if SETUPBRICKS:
                retval = SetupBricks()
                if not retval:
                        LogSummary("Bricks setup failed\n")
                        ReportResults()
                        sys.exit(1)
        else:
                LogSummary ("Bricks will not be setup\n")


        if RUNTESTS:
                retval = StartUpVolumesOnBricks()

        if not retval:
                LogSummary("Volumes start-up failed\n")
                ReportResults()
                sys.exit(1)
        
        if RUNTESTS:
		RunTests()
        else:
                LogSummary ("Tests will not be run\n")

        ReportResults()

def PrintConfig():

        WriteLog ("Controller: Patchfile: " + PATCHFILE + "\n")
        LogSummary ("Controller: Patchfile: " + PATCHFILE + "\n")
        WriteLog ("Controller: Bricks: " + str(BRICKS_IPADDRS) + "\n")
        LogSummary ("Controller: Bricks: " + str(BRICKS_IPADDRS) + "\n")
        WriteLog ("Controller: Logfile: " + LOGFILE + "\n")
        LogSummary ("Controller: Logfile: " + LOGFILE + "\n")
        WriteLog ("Controller: RunTests: " + str(RUNTESTS) + "\n")
        LogSummary ("Controller: RunTests: " + str(RUNTESTS) + "\n")

def usage():
        print "USAGE: testcontroller -p <patch-to-test> -b <brick1,brick2,brick3,...brickN>"
        print "\t-p <patch-to-apply> is optional, if not specified, will just setup the bricks with latest git"
        print "\t-b <branch> git branch for GlusterFS"

 
if __name__ == "__main__":
        timestr = START_TIMESTR
        if "-h" in sys.argv or "--help" in sys.argv:
                usage()
                sys.exit(0)

        if "-p" in sys.argv:
                PATCHFILE = sys.argv[sys.argv.index("-p") + 1]
        
	LOGFILE = LOGFILE + timestr
	LOGFILEFD = open (LOGFILE, "a")

        if "-t" in sys.argv:
                RUNTESTS = True

	if len(BRICKS_IPADDRS) == 0:
		BRICKS_IPADDRS = [socket.gethostname()]
	
	if "-n" in sys.argv:
                NFSSERVER_ADDR = sys.argv[sys.argv.index("-n") + 1]
        else:
                NFSSERVER_ADDR = BRICKS_IPADDRS[0]

        
        if CLIENT_IP:
                NFSCLIENT_ADDR = CLIENT_IP
	else:
	        NFSCLIENT_ADDR = BRICKS_IPADDRS[0]

        if RUNTESTS and len(NFSCLIENT_ADDR) == 0:
                print "Tests cannot be run without a NFS client address."
                usage ()
                sys.exit(0)
	
	if "-s" in sys.argv:
                SETUPBRICKS = True

        
	if EMAILCONTROLLOG:
	       try:
		       os.remove(CONTROL_LOGFILE)
	       except:
		       pass 
	       
	       CONTROL_LOG = open (CONTROL_LOGFILE, "w")
	       CONTROL_LOG.write ("Subject: Testbot logs for test started on " + timestr + "\n")
	       LogSummary ("Complete log available at " + LOGFILE + " on controller\n")
	       if len(LOGDOWNLOADURL) > 0:
		       LogSummary ("Complete log available at " + LOGDOWNLOADURL + "/"+os.path.basename(LOGFILE) +"\n")
	       elif len(LOGSCPURL) > 0:
		       LogSummary ("Complete log available at " + LOGSCPURL + "/"+os.path.basename(LOGFILE) +"\n")
	else:
		CONTROL_LOG = sys.stdout
	
	if RUNTESTS:
		VOL_PAR = create_bricks()

        if "-N" in sys.argv:
                DAEMONIZE = False

        PrintConfig()
        main ()
