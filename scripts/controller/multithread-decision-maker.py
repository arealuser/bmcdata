
import os
import time
import pandas as pd
import numpy as np
import joblib
import requests
from sklearn.svm import SVC
from influxdb_client import InfluxDBClient
from gene_algo import genetic_algorithm
from threading import Thread
import warnings

warnings.filterwarnings("ignore")

bmchost = "192.168.1.114"
influxhost = "192.168.1.102:8086"
DEBUG_TIMING = True
NUM_BMC = 10
MOCK_SEND = True
MOCK_BASE_URL = "http://192.168.1.102"

svm = joblib.load("svm_model.joblib")
redfishtoken = requests.post(f"https://{bmchost}/login", json={"username": "root", "password": "0penBmc"}, verify=False).json()['token']
token = os.environ.get("INFLUXDB_TOKEN")
org = "iie"
client = InfluxDBClient(url=f"http://{influxhost}", token=token, org=org)

def report_time(event_name: str, duration: float, device_id: int = 0):
    if not DEBUG_TIMING:
        return
    line = f"teap_timing,device_id=bmc{device_id} {event_name}={duration:.6f}"
    headers = {"Authorization": f"Token {token}", "Content-Type": "text/plain"}
    url = f"http://{influxhost}/api/v2/write?org=iie&bucket=default&precision=s"
    try:
        res = requests.post(url, headers=headers, data=line)
        if res.status_code >= 300:
            print(f"[InfluxDB] Failed report for {device_id}: {res.text}")
    except Exception as e:
        print(f"[InfluxDB] Error report for {device_id}: {e}")

def sendbmccmd(action, value, token):
    url = f"https://{bmchost}/hyperbmc/run-script/{action}/{value}"
    headers = {'X-Auth-Token': token, 'XSRF-TOKEN': token}
    requests.put(url, headers=headers, data=None, verify=False)
def sendmockbmccmd(action, value, token):
    headers = {'X-Auth-Token': token, 'XSRF-TOKEN': token}
    requests.put(MOCK_BASE_URL, headers=headers, data=None, verify=False)

def fetch_data(query_api, device_type="bmc"):
    query = '''
        from(bucket: "default")
        |> range(start: -1m)
        |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> filter(fn: (r) => r.device_id == "bmc") 
        |> keep(columns: ["Chipset2_Temp", "Chipset_Temp", "Cpu1_Temp", "Cpu2_Temp", "FAN1", "FAN2", "FAN3", "FAN4", "IO_Outlet_Temp", "Inlet_Temp", "Outlet_Temp", "PSU1_FAN", "PSU1_Inlet", "PSU1_Total_Power", "PSU1_VIN", "PSU2_FAN", "PSU2_Inlet", "PSU2_Total_Power", "PSU2_VIN"])
    '''

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
    if device_type == "bmc":
        return query_api.query(query)
    else:
        return query_api.query(query_host)
    

def process_node(index):
    print(f"process bmc {index}")
    #thread local variable
    onecount=0
    zerocount=0
    waitnum = 1
    #已经被调频的cpu列表
    numa_node_to_reduce=""
    last_merged_cores = 128
    while True:
        try:
            time.sleep(30)
            print(f"bmc {index}: wake")
            query_api = client.query_api()

            t0 = time.time()
            tables_bmc = fetch_data(query_api, "bmc")
            tables_host = fetch_data(query_api, "host")
            report_time("fetch_time", time.time() - t0, index)


            # 将查询结果转换为 DataFrame
            data_host = []
            for table in tables_host:
                for record in table.records:
                    data_host.append(record.values)
            vm_info_data = pd.DataFrame(data_host)

            # 将每个核心的利用率存入一个列表
            core_usage = []
            for i in range(128):
                core_name = f'core{i}'
                if core_name in vm_info_data.columns:
                    core_usage.append(vm_info_data[core_name].values[0])

            total_vm = vm_info_data['total_vm'].values[0]
            # option 1, 返回虚拟机数和虚拟CPU数，计算所需的cpu数，此处应设计一种算法，例如观测VM负载得到。
            total_vcpu = vm_info_data['total_vcpu'].values[0]

            data = []
            for table in tables_bmc:
                for record in table.records:
                    data.append(record.values)
            test_data = pd.DataFrame(data)

            if "result" in test_data.columns:
                test_data.drop(columns=["result"], inplace=True)
            if "table" in test_data.columns:
                test_data.drop(columns=["table"], inplace=True)

            test_data["Chipset2_Diff"] = test_data["Chipset2_Temp"].diff()
            test_data["Chipset1_Diff"] = test_data["Chipset_Temp"].diff()
            test_data["IO_Outlet_Diff"] = test_data["IO_Outlet_Temp"].diff()
            test_data["Inlet_Diff"] = test_data["Inlet_Temp"].diff()
            test_data["Outlet_Diff"] = test_data["Outlet_Temp"].diff()
            # 计算 FAN_MEAN 和 FAN_Diff 列
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

            # 提取特征列
            test_features = test_data.iloc[:, :-1].values
            # 在测试集上进行预测
            if len(test_features) == 0:
                continue
            # predictions = svm.predict(test_features)

            t1 = time.time()
            pred = svm.predict(test_features)[-1]
            report_time("predict_time", time.time() - t1, index)

            if pred == 1:
                zerocount = 0
                if onecount < waitnum:
                    onecount += 1
                    print(f"bmc {index}: 1 next loop")
                else:
                    onecount = 0
                    print(f"bmc {index}: tune")
                    if total_vcpu <= 0:
                        continue
                    total_vcpu_aligned = total_vcpu + (16 - total_vcpu % 16) #可以尝试用这个值作为最小的P区

                    if total_vcpu_aligned == last_merged_cores:
                        continue
                    last_merged_cores = total_vcpu_aligned
                    #通过启发式或者贪心法求解
                    if DEBUG_TIMING:
                        algo_start = time.time()
                    bitarr = genetic_algorithm(128, total_vcpu_aligned, core_usage, 16, 8)
                    if DEBUG_TIMING:
                        algo_time = time.time() -algo_start
                        report_time("algo_time", algo_time, index)
                    print(f"bmc {index}:遗传算法选择的bitmap：", bitarr)
                    selected_cores = []
                    for i in range(0, len(bitarr)):
                        if bitarr[i] == 0:
                            selected_cores.append(i)
                    numa_node_to_reduce = ",".join(map(str, selected_cores))

                    if(len(numa_node_to_reduce) > 0):
                        if DEBUG_TIMING:
                            send_start = time.time()
                        if index == 0:
                            sendbmccmd("sdpm-cmd", f"hot-freqset-{numa_node_to_reduce}", redfishtoken)
                        else:
                            sendmockbmccmd("sdpm-cmd", f"hot-freqset-{numa_node_to_reduce}", redfishtoken)
                        if DEBUG_TIMING:
                            send_time = time.time() -send_start
                            report_time("send_time", send_time, index)

            else:
                onecount = 0
                if zerocount < waitnum:
                    zerocount += 1
                    print(f"bmc {index}: 0 next loop ")
                else:
                    zerocount = 0
                    print(f"bmc {index}: send recovery cmd")
                    if total_vcpu <= 0:
                        continue
                    last_merged_cores = 128
                    if(len(numa_node_to_reduce) > 0):
                        if DEBUG_TIMING:
                            send_start = time.time()
                        if index == 0:
                            sendbmccmd("sdpm-cmd", f"cold-freqset-{numa_node_to_reduce}", redfishtoken)
                        else:
                            sendmockbmccmd("sdpm-cmd", f"cold-freqset-{numa_node_to_reduce}", redfishtoken)
                        if DEBUG_TIMING:
                            send_time = time.time() -send_start
                            report_time("send_time", send_time, index)
                        numa_node_to_reduce=""
                    # 发送恢复CPU核心命令
                    # 我们同时控制风扇，一次减少10%，或者提高pid温度
        except Exception as e:
            print(f"[bmc {index}] error: {e}")

for i in range(NUM_BMC):
    Thread(target=process_node, args=(i,), daemon=True).start()

while True:
    # 模拟，等待更多的BMC接入事件
    time.sleep(36000)
