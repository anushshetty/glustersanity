#!/usr/bin/python

import os
import string
import sys
import commands
import time


TESTFILE = ""
NFSSERVER = ""
NFSEXP = ""
MOUNTPOINT = ""

class Test:
        __testinfo__ = ""
        __name__ = ""
        __description__ = ""
        __commandscript__ = ""

        def LoadTest(self, testinfo):
                tinfo = open (testinfo, "r")
                for line in tinfo:
                        tokens = line.split("=")
                        if tokens[0] == "name":
                                self.__name__ = tokens[1].strip()
                        elif tokens[0] == "description":
                                self.__description__ = tokens[1].strip()
                        elif tokens[0] == "commandscript":
                                self.__commandscript__ = tokens[1].strip()


        def __init__(self, testinfo):
                self.__testinfo__ = testinfo
                self.LoadTest (testinfo)

        def framecommand(self):
                testscript = os.path.dirname(self.__testinfo__) + "/" + self.__commandscript__
                cmd = []
                cmd.append ("sh")
                cmd.append (testscript)
                cmd.append (NFSSERVER)
                cmd.append (NFSEXP)
                cmd.append (MOUNTPOINT)

                return string.join(cmd, " ")

        def RunTest(self):
                (status,output) = commands.getstatusoutput (self.framecommand())
                print output

def main():

        test = Test (TESTFILE)

        test.RunTest()

def usage():
        print "\t-h             Prints this message."
        print "\t-t <testinfo-file> Loads the given test info file. Must be an absolute path."
        print "\t-s <nfssrv>        NFS server to mount."
        print "\t-e <export>        NFS export to mount."
        print "\t-m <mountpoint>    Directory to mount export at."
        return
 
if __name__ == "__main__":
        if "-h" in sys.argv or "--help" in sys.argv:
                usage()
                sys.exit(0)

        if len(sys.argv) < 3:
                print "Must provide some arguments"
                usage()
                sys.exit(0)

        if "-t" in sys.argv:
                TESTFILE = sys.argv[sys.argv.index("-t") + 1]

        if "-s" in sys.argv:
                NFSSERVER = sys.argv[sys.argv.index("-s") + 1]

        if "-e" in sys.argv:
                NFSEXP = sys.argv[sys.argv.index("-e") + 1]

        if "-m" in sys.argv:
                MOUNTPOINT = sys.argv[sys.argv.index("-m") + 1]

        if len(TESTFILE) == 0:
                print "No test info file provided."
                usage ()
                sys.exit(0)

        if len(NFSSERVER) == 0:
                print "No nfs server provided."
                usage ()
                sys.exit(0)

        if len(NFSEXP) == 0:
                print "No server export provided."
                usage ()
                sys.exit(0)

        if len(MOUNTPOINT) == 0:
                print "No mount point provided."
                usage ()
                sys.exit(0)

        main ()
