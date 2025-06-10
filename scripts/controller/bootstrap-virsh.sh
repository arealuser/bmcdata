#!/bin/sh
# Test VMs with identical configurations. To test VMs with random configurations, use other scripts.
# Argument 1: Number of VMs to start
# Argument 2: Number of cores per VM
# 1. Start qemu
if [ ! $1 ]; then
        echo 'usage: ./bootstrap.sh <vms>'
        exit 0
fi
curl --request POST "http://192.168.1.102:8086/api/v2/write?org=iie&bucket=default&precision=s" --header "Authorization: Token wS6oSOQqpAsmr7OscYrZ8IC-kNGwvBlcKfMPH9jAycW1gBDJvwnrj8Aqr5BU1cahQgM8AIMfuI8lyE-ljmMjNA==" -H "Content-Type: text/plain" -d "sdgp,device_id=eventgen name=\"bootstrap\""



for i in $(seq 1 $1); do
  virsh start vm$i
  #获取pid
  pid=`ps -ef | grep "vm$i," | grep -v grep | awk '{print $2}'`
  echo $pid
  #设置亲和性
  #group=$((i-1))
  #STARTCORE=$((group*$2))
  #ENDCORE=$((STARTCORE + $2 - 1))
  #taskset -pca $STARTCORE-$ENDCORE $pid
done
wait

