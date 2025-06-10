#!/bin/sh
if [ ! $1 ]; then
   echo 'usage: ./realscript.sh <loop times>'
   exit 0
fi
LOOPCOUNT=$1
num=0
while :
do

	sleep 0
	num=$((num+1))
	if [ $num -eq $LOOPCOUNT ]; then
		break		
	fi
done

echo $num

