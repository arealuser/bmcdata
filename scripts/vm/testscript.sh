#!/bin/sh
#environment
hostaddr=192.168.1.102
influxkey=jS6UphFh7BRxO0ZXkWAki6-9dxVQrnU_aUEk5r0DcPOx2hT0w9lt5C1dG2-8aKakBw94w7Wl8ws7hjA6wXLEXg==
if [ ! $1 ]; then
  echo 'usage: ./testscript.sh 9999'
  exit 0
fi
HOSTNAME=$(hostname)
curl --request POST "http://$hostaddr:8086/api/v2/write?org=iie&bucket=default&precision=s" --header "Authorization: Token jS6UphFh7BRxO0ZXkWAki6-9dxVQrnU_aUEk5r0DcPOx2hT0w9lt5C1dG2-8aKakBw94w7Wl8ws7hjA6wXLEXg==" -H "Content-Type: text/plain" -d "sdgp,device_id=$HOSTNAME event=\"startjob\""

LOOPCOUNT=$(($1/4))
echo start job..

echo preparing...
num=0
while :
do
	sleep 0
	num=$((num+1))
        if [ $num -eq $LOOPCOUNT ]; then
                break
        fi
done
echo running...

#time sh $PWD/work.sh $1
starttime=$(date +%s)
sh $PWD/work.sh $1
endtime=$(date +%s)
timespan=$(( $endtime-$starttime ))
echo result: $timespan s
echo $timespan > result.txt
cat result.txt
#cat result.txt
curl --request POST "http://$hostaddr:8086/api/v2/write?org=iie&bucket=default&precision=s" --header "Authorization: Token $influxkey" -H "Content-Type: text/plain" -d "sdgp,device_id=$HOSTNAME timecost=$timespan,loopcount=$1"


echo cold down....
num2=0
while :
do
	sleep 0
	num2=$((num2+1))
        if [ $num2 -eq $LOOPCOUNT ]; then
                break
        fi
done
curl --request POST "http://$hostaddr:8086/api/v2/write?org=iie&bucket=default&precision=s" --header "Authorization: Token jS6UphFh7BRxO0ZXkWAki6-9dxVQrnU_aUEk5r0DcPOx2hT0w9lt5C1dG2-8aKakBw94w7Wl8ws7hjA6wXLEXg==" -H "Content-Type: text/plain" -d "sdgp,device_id=$HOSTNAME event=\"endjob\""

echo done.

shutdown -h
