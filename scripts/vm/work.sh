#!/bin/bash
if [ ! $1 ]; then
  echo 'usage: ./testscript.sh <loopcount>'
  exit 0
fi

sh $PWD/realscript.sh $1  &
sh $PWD/realscript.sh $1  &
sh $PWD/realscript.sh $1  &
sh $PWD/realscript.sh $1  &
wait
