import json
import sys
import os
import requests
import time

bmchost="192.168.1.114"
influxhost="192.168.1.102:8086"
influxkey="wS6oSOQqpAsmr7OscYrZ8IC-kNGwvBlcKfMPH9jAycW1gBDJvwnrj8Aqr5BU1cahQgM8AIMfuI8lyE-ljmMjNA=="

def gettoken():
  token=""
  url = "https://" + bmchost + "/login"
  postdatas = {"username" :  "root", "password" :  "0penBmc"}
  res = requests.post(url, json=postdatas, verify=False)
  token = res.json()['token']
  return token

redfishtoken = gettoken()
print("redfishtoken: " + redfishtoken)

def fetchData(sensor, token):
  value=""
  url = "https://" + bmchost + "/redfish/v1/Chassis/1/Sensors/" + sensor
  headers = {'X-Auth-Token': token}
  res = requests.get(url, headers=headers, verify=False)
  json=res.json()
  print(json)
  if(res.status_code == 200):
    value = json["Reading"]
  return {'key': sensor, 'value': value, 'line': sensor + "=" + str(value)}

def formatValue(value, scale):
    scaled_value = value * 10**scale
    return round(scaled_value, 2)

def fetchDataInOneTime(token):
  value=""
  url = "https://" + bmchost + "/xyz/openbmc_project/sensors/enumerate"
  headers = {'X-Auth-Token': token}
  res = requests.get(url, headers=headers, verify=False)
  json=res.json()
  print(json)
  if(res.status_code == 200):
    return json

def uploadInflux():
  while True:
    time.sleep(10)
    line = "sdgp,device_id=bmc "

    jsonresult = fetchDataInOneTime(redfishtoken)
    result = []
    filter_array = ['PSU1_Total_Power', 'PSU2_Total_Power', 'FAN1', 'FAN2', 'FAN3', 'FAN4',
    "PSU1_FAN", "PSU2_FAN", "Chipset_Temp", "Chipset2_Temp", "Cpu1_Temp", "Cpu2_Temp", "IO_Outlet_Temp", "Inlet_Temp", "Outlet_Temp",
    "PSU1_Inlet", "PSU2_Inlet", "PSU1_VIN", "PSU2_VIN", "PSU1_CIN", "PSU2_CIN"]
    for path, values in jsonresult['data'].items():

        name = path.split('/')[-1]

        if name not in filter_array:
            continue

        value = values['Value']
        scale = values['Scale']
        formatted_value = formatValue(value, scale)

        result.append(f"{name}={formatted_value}")

    result_string = ",".join(result)
    line += result_string

    url = "http://" + influxhost + "/api/v2/write?org=iie&bucket=default&precision=s"
    headers = {'Authorization': "Token " + influxkey, "Content-Type":"text/plain"}
    res = requests.post(url, headers=headers, data=line)
    print(res)
  return True

#main loop
uploadInflux()
