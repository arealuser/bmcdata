#!/usr/bin/env python3

import os
import time
import csv
import math
import socket
import subprocess

hostaddr = "192.168.1.102"
influxkey = "wS6oSOQqpAsmr7OscYrZ8IC-kNGwvBlcKfMPH9jAycW1gBDJvwnrj8Aqr5BU1cahQgM8AIMfuI8lyE-ljmMjNA=="
trace_url = f"http://{hostaddr}/download/trace.csv"
trace_file = "trace.csv"

SCALE_FACTOR = 16
INTERVAL = 60
MAX_LINES = 1000000
COOLDOWN = 0

hostname = socket.gethostname()
vm_index = ''.join(filter(str.isdigit, hostname))
if not vm_index:
    print("Error: Cannot extract VM index from hostname")
    exit(1)
vm_index = int(vm_index)


print(f"Starting workload replay for VM{vm_index}...")
with open(trace_file, newline='') as csvfile:
    reader = csv.reader(csvfile)
    header = next(reader)  
    for linenumber, row in enumerate(reader, start=1):
        if linenumber > MAX_LINES:
            print(f"Reached max lines {MAX_LINES}")
            break

        try:
            col_index = (vm_index % 16) + 1  
            usage = float(row[col_index])
        except (IndexError, ValueError):
            print(f"[Line {linenumber}] Invalid row or usage")
            continue

        target_cores_float = usage * SCALE_FACTOR
        target_cores_int = int(target_cores_float)
        target_cores_frac = target_cores_float - target_cores_int


        if target_cores_int > 0:
            print(f"stress-ng --cpu {target_cores_int} --cpu-load 100", end=' ')
            subprocess.Popen([
                "stress-ng", "--cpu", str(target_cores_int),
                "--cpu-load", "100", "--timeout", str(INTERVAL)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if target_cores_frac > 0.01:
            load_percent = round(target_cores_frac * 100)
            print(f"+ stress-ng --cpu 1 --cpu-load {load_percent}", end=' ')
            subprocess.Popen([
                "stress-ng", "--cpu", "1",
                "--cpu-load", str(load_percent), "--timeout", str(INTERVAL)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


        line = f"sdgp,device_id=vm{vm_index} load={target_cores_float:.3f},idx={linenumber}"
        curl_cmd = (
            f"curl -s --request POST 'http://{hostaddr}:8086/api/v2/write?org=iie&bucket=default&precision=s' "
            f"--header 'Authorization: Token {influxkey}' "
            f"-H 'Content-Type: text/plain' "
            f"--data-raw '{line}'"
        )
        os.system(curl_cmd)


        time.sleep(INTERVAL)
        if COOLDOWN > 0:
            time.sleep(COOLDOWN)

        if COOLDOWN > 0:
            time.sleep(COOLDOWN)


done_line = f"sdgp,device_id=vm{vm_index} event=\"done\""
done_curl_cmd = (
    f"curl -s --request POST 'http://{hostaddr}:8086/api/v2/write?org=iie&bucket=default&precision=s' "
    f"--header 'Authorization: Token {influxkey}' "
    f"-H 'Content-Type: text/plain' "
    f"--data-raw '{done_line}'"
)
os.system(done_curl_cmd)

print(f"All done for VM{vm_index}")
