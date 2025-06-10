import os
import time
import pandas as pd
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score
import joblib
from influxdb_client import InfluxDBClient
import json
import sys
import requests
from algorithms import genetic_algorithm #引入启发式算法
from algorithms import greedy_algorithm

import datetime
import requests



bmchost="192.168.1.114"
influxhost="192.168.1.102:8086"
DEBUG_TIMING = True


def gettoken():
  token=""
  url = "https://" + bmchost + "/login"
  postdatas = {"username" :  "root", "password" :  "0penBmc"}
  res = requests.post(url, json=postdatas, verify=False)
  token = res.json()['token']
  return token

redfishtoken = gettoken()
print("redfishtoken: " + redfishtoken)

def report_time_to_influx(event_name: str, duration: float):
    if not DEBUG_TIMING:
        return
    timestamp = int(time.time())
    line = f"teap_timing,device_id=eventgen {event_name}={duration:.6f}"
    influx_token = os.environ.get("INFLUXDB_TOKEN")
    influx_write_url = f"http://{influxhost}/api/v2/write?org=iie&bucket=default&precision=s"
    headers = {
        "Authorization": f"Token {influx_token}",
        "Content-Type": "text/plain"
    }
    try:
        response = requests.post(influx_write_url, headers=headers, data=line)
        if response.status_code >= 300:
            print(f"[InfluxDB] Failed to report {event_name}: {response.text}")
    except Exception as e:
        print(f"[InfluxDB] Error reporting {event_name}: {e}")


def sendbmccmd(action, value, token):
  # auto-fan-control#auto: Fixed at 10% PWM (tentative), fully relies on TEAP for thermal regulation
  # auto-fan-control#cold-fixed: Decrease fan speed by 10%
  # auto-fan-control#hot-fixed: Increase fan speed by 10%
  # sdpm-cmd#cold or hot: Disabling CPU cores (deprecated)
  # sdpm-cmd#cold-freqset- or hot-freqset-: Adjust CPU P/E cluster frequency
  url = "https://" + bmchost + "/hyperbmc/run-script/" + action + "/" + value
  print(url)
  headers = {'X-Auth-Token': token, 'XSRF-TOKEN': token}
  res = requests.put(url, headers=headers, data=None, verify=False)
  print(res)


token = os.environ.get("INFLUXDB_TOKEN")
org = "iie"
url = "http://" + influxhost
client = InfluxDBClient(url=url, token=token, org=org)

svm = joblib.load('svm_model.joblib')
onecount=0
zerocount=0
waitnum = 1
numa_node_to_reduce=""
last_merged_cores = 128


while True:

    time.sleep(30)

    if DEBUG_TIMING:
        fetch_start = time.time()

    query_api = client.query_api()
    query = '''
        from(bucket: "default")
        |> range(start: -1m)
        |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> filter(fn: (r) => r.device_id == "bmc") 
        |> keep(columns: ["Chipset2_Temp", "Chipset_Temp", "Cpu1_Temp", "Cpu2_Temp", "FAN1", "FAN2", "FAN3", "FAN4", "IO_Outlet_Temp", "Inlet_Temp", "Outlet_Temp", "PSU1_FAN", "PSU1_Inlet", "PSU1_Total_Power", "PSU1_VIN", "PSU2_FAN", "PSU2_Inlet", "PSU2_Total_Power", "PSU2_VIN"])
    '''
    tables = query_api.query(query)

    query_host = '''
        from(bucket: "default")
        |> range(start: -1m)
        |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> filter(fn: (r) => r.device_id == "host") 
        |> keep(columns: ["core0", "core1", "core2", "core3", "core4", "core5", "core6", "core7", "core8", "core9", "core10",
                        "core11", "core12", "core13", "core14", "core15", "core16", "core17", "core18", "core19", "core20",
                        "core21", "core22", "core23", "core24", "core25", "core26", "core27", "core28", "core29", "core30",
                        "core31", "core32", "core33", "core34", "core35", "core36", "core37", "core38", "core39", "core40",
                        "core41", "core42", "core43", "core44", "core45", "core46", "core47", "core48", "core49", "core50",
                        "core51", "core52", "core53", "core54", "core55", "core56", "core57", "core58", "core59", "core60",
                        "core61", "core62", "core63", "core64", "core65", "core66", "core67", "core68", "core69", "core70",
                        "core71", "core72", "core73", "core74", "core75", "core76", "core77", "core78", "core79", "core80",
                        "core81", "core82", "core83", "core84", "core85", "core86", "core87", "core88", "core89", "core90",
                        "core91", "core92", "core93", "core94", "core95", "core96", "core97", "core98", "core99", "core100",
                        "core101", "core102", "core103", "core104", "core105", "core106", "core107", "core108", "core109",
                        "core110", "core111", "core112", "core113", "core114", "core115", "core116", "core117", "core118",
                        "core119", "core120", "core121", "core122", "core123", "core124", "core125", "core126", "core127", "total_vm", "total_vcpu"
                        ])
        '''

    tables_host = query_api.query(query_host)

    if DEBUG_TIMING:
        fetch_time = time.time() - fetch_start
        report_time_to_influx("fetch_time", fetch_time)
        predict_start = time.time()

    data_host = []
    for table in tables_host:
        for record in table.records:
            data_host.append(record.values)
    vm_info_data = pd.DataFrame(data_host)


    core_usage = []
    for i in range(128):
        core_name = f'core{i}'
        if core_name in vm_info_data.columns:
            core_usage.append(vm_info_data[core_name].values[0])

    total_vm = vm_info_data['total_vm'].values[0]

    total_usage = sum(core_usage)
    total_vcpu = round(total_usage / 50) 
    print(f"problem to solve: {total_usage},{total_vcpu}")

    # 将查询结果转换为 DataFrame
    data = []
    for table in tables:
        for record in table.records:
            data.append(record.values)
    test_data = pd.DataFrame(data)
    print(test_data.columns)

    if "result" in test_data.columns:
        test_data.drop(columns=["result"], inplace=True)
    if "table" in test_data.columns:
        test_data.drop(columns=["table"], inplace=True)


    test_data["Chipset2_Diff"] = test_data["Chipset2_Temp"].diff()
    test_data["Chipset1_Diff"] = test_data["Chipset_Temp"].diff()
    test_data["IO_Outlet_Diff"] = test_data["IO_Outlet_Temp"].diff()
    test_data["Inlet_Diff"] = test_data["Inlet_Temp"].diff()
    test_data["Outlet_Diff"] = test_data["Outlet_Temp"].diff()

    fan_cols = ["FAN1", "FAN2", "FAN3", "FAN4"]
    test_data["FAN_MEAN"] = test_data[fan_cols].mean(axis=1)
    test_data["FAN_Diff"] = test_data["FAN_MEAN"].diff()

    test_data["PSU1_FAN_Diff"] = test_data["PSU1_FAN"].diff()
    test_data["PSU1_Inlet_Diff"] = test_data["PSU1_Inlet"].diff()
    test_data["PSU1_Power_Diff"] = test_data["PSU1_Total_Power"].diff()
    test_data["PSU2_FAN_Diff"] = test_data["PSU2_FAN"].diff()
    test_data["PSU2_Inlet_Diff"] = test_data["PSU2_Inlet"].diff()
    test_data["PSU2_Power_Diff"] = test_data["PSU2_Total_Power"].diff()

    test_data.drop(columns=["FAN1", "FAN2", "FAN3", "FAN4", "PSU1_VIN", "PSU2_VIN"], inplace=True)

    test_data["Effective"] = 0
    test_data = test_data.dropna(axis=0)


    test_features = test_data.iloc[:, :-1].values

    if len(test_features) == 0:
        continue
    predictions = svm.predict(test_features)

    if DEBUG_TIMING:
        predict_time = time.time() - predict_start
        report_time_to_influx("predict_time", predict_time)


    if len(predictions) > 0:
        pred = predictions[-1]
        print(f"Predicted: {pred}")
        if pred == 1:
            zerocount = 0
            if onecount < waitnum:
                onecount += 1
                print("1 next loop")
            else:
                onecount = 0
                print("deprovision")
                # sendbmccmd("auto-fan-control", "hot-fixed", redfishtoken)
                # sendbmccmd("auto-fan-control", "hot-pid", redfishtoken)
                # sendbmccmd("sdpm-cmd", "hot", redfishtoken)
                if total_vcpu <= 0:
                    continue
                # total_vcpu_aligned = total_vcpu + (16 - total_vcpu % 16) 
                total_vcpu_aligned = total_vcpu - total_vcpu % 16 

                if total_vcpu_aligned == last_merged_cores:
                    continue
                last_merged_cores = total_vcpu_aligned

                if DEBUG_TIMING:
                    algo_start = time.time()
                bitarr = genetic_algorithm(128, total_vcpu_aligned, core_usage, 16, 8)
                if DEBUG_TIMING:
                    algo_time = time.time() -algo_start
                    report_time_to_influx("algo_time", algo_time)
                print("bitmap：", bitarr)
                selected_cores = []
                for i in range(0, len(bitarr)):
                    if bitarr[i] == 0:
                        selected_cores.append(i)
                numa_node_to_reduce = ",".join(map(str, selected_cores))

                if(len(numa_node_to_reduce) > 0):
                    if DEBUG_TIMING:
                        send_start = time.time()
                    print("send cmd")
                    sendbmccmd("sdpm-cmd", f"hot-freqset-{numa_node_to_reduce}", redfishtoken)
                    if DEBUG_TIMING:
                        send_time = time.time() -send_start
                        report_time_to_influx("send_time", send_time)

        else:
            onecount = 0
            if zerocount < waitnum:
                zerocount += 1
                print("0 next loop ")
            else:
                zerocount = 0
                print("reprovision")
                # sendbmccmd("auto-fan-control", "cold-fixed", redfishtoken)
                # sendbmccmd("auto-fan-control", "cold-pid", redfishtoken)
                # sendbmccmd("sdpm-cmd", "cold", redfishtoken)
                if total_vcpu <= 0:
                    continue
                last_merged_cores = 128
                if(len(numa_node_to_reduce) > 0):
                    if DEBUG_TIMING:
                        send_start = time.time()
                    print("send cmd")
                    sendbmccmd("sdpm-cmd", f"cold-freqset-{numa_node_to_reduce}", redfishtoken)
                    if DEBUG_TIMING:
                        send_time = time.time() -send_start
                        report_time_to_influx("send_time", send_time)
                    numa_node_to_reduce=""
    else:
        print("Predicted N/A")
        
                
