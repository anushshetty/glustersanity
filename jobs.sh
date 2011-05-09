#!/bin/sh

set -x

if [ $# -ne 2 ]
then
        echo "Not enough arguments"
        exit 1
fi

TESTNAME=$1
MOUNTPOINT=$2

if [ "$TESTNAME" = "dbench" ] 
then
    dbench -s 10 -D $MOUNTPOINT -t 10 2> /dev/null > /dev/null
fi
