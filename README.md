BMCDATA
==============================

## Overview

This dataset stems from an Dual-socket Phytium S2500 (Arm64, 8x16-core NUMA) server featuring dual CPU sockets with 64 cores each, totaling 128 cores, backed by 128GB RAM and a 4TB HDD. 
Each NUMA node comprises 8 cores sharing an 8MB L3 cache, with clusters of 4 cores further benefiting from a shared 2MB L2 cache. 
Each core has 32KB each of L1d and L1i cache. 
The server utilizes DVFS with 16-core frenquency group for dynamic power and performance management.
Collected through both the server's Baseboard Management Controller (BMC) and a user-level application, it encompasses a wealth of experimental data. Experiments include Fork-And-Join workloads, Linux kernel compilations, stress tests, and the replication of real Jenkins build histories. Offering insights into power management, fan control, system performance, and reliability.

Data was initially pulled by custom scripts and uploaded to InfluxDB for streamlined management. Exported data, now available in the `data` directory, awaits your analysis.

```
bmcdata/
├── assets/
│   ├── spec/                   # SPEC 2006 Results
│   ├── googlereplay/           # scripts to process google cluster v1 data set
│   ├── baseline/                   # Implementations for HFEE and LADPM, and research records on characterization.
│   ├── apache.out.csv           # Apache Jenkins replay
│   ├── sources.list.txt           # Apache Jenkins projects specifics
│   ├── jenkinsjob.py           # Apache Jenkins replay trigger
│   └── event-gen.csv          # Synthetic Workload
├── script/
│   ├── controller/        # Scripts run in the controller
│   ├── executor/        # Scripts run in the executor
│   ├── vm/        # Scripts are fetched by the VM's rc.local at initialization and automatically run the test script
│   ├── split.py        # split the origin data
│   ├── collapse.py            # aggregate the bmc and host data
│   ├── scidata.py           # simple analysis
|   ├── collapse.csv       # demo result for collapse.py
├── data/
│   ├── *.csv                  # Data traces exported from InfluxDB
├── README.md
└── LICENSE
```


### InfluxDB Export Methodology

Data extraction from InfluxDB employs the following Flux query syntax:

```influx
from(bucket: "default")
  |> range(start: -1224h)
  |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
```

Please note, while the exported files bear a `.csv` extension, their structure deviates from conventional CSVs due to InfluxDB's metadata. Ignore lines beginning with `#group`, `#datatype`, and `#default`; these are metadata artifacts. Similarly, disregard columns named `result`, `table`, `_start`, and `_stop` as they do not contribute to data content.

Utilizing software such as Microsoft Excel or Google Sheets to view these files is a great option, and we have even provided [scripts](#useful-scripts) to facilitate their processing.

### Key Specifications

**BMC Collected Data**

| Column Name | Description |
|-------------|-------------|
| `_time` | Timestamp received by InfluxDB |
| `*measurement` | Name of the measurement |
| `device_id` | Identifier of the device |
| `Chipset2_Temp` | Temperature of Chipset 2 |
| `Chipset_Temp` | Temperature of Chipset |
| `Cpu1_Temp` | Temperature of CPU 1 |
| `Cpu2_Temp` | Temperature of CPU 2 |
| `FAN1` | Speed of Fan 1 |
| `FAN2` | Speed of Fan 2 |
| `FAN3` | Speed of Fan 3 |
| `FAN4` | Speed of Fan 4 |
| `IO_Outlet_Temp` | Temperature of I/O Outlet |
| `Inlet_Temp` | Temperature of Inlet |
| `Outlet_Temp` | Temperature of Outlet |
| `PSU1_CIN` | Input Current of Power Supply Unit 1 |
| `PSU1_FAN` | Fan Speed of Power Supply Unit 1 |
| `PSU1_Inlet` | Inlet Temperature of Power Supply Unit 1 |
| `PSU1_Total_Power` | Total Power of Power Supply Unit 1 |
| `PSU1_VIN` | Input Voltage of Power Supply Unit 1 |
| `PSU2_CIN` | Input Current of Power Supply Unit 2 |
| `PSU2_FAN` | Fan Speed of Power Supply Unit 2 |
| `PSU2_Inlet` | Inlet Temperature of Power Supply Unit 2 |
| `PSU2_Total_Power` | Total Power of Power Supply Unit 2 |
| `PSU2_VIN` | Input Voltage of Power Supply Unit 2 |

**Host Collected Data**


| Column Name | Description |
|-------------|-------------|
| `_time` | Timestamp received by InfluxDB |
| `*measurement` | Name of the measurement |
| `device_id` | Identifier of the device |
| `L1_dcache_load_misses` | Level 1 Data Cache Load Misses |
| `L1_dcache_loads` | Level 1 Data Cache Loads |
| `L1_dcache_store_misses` | Level 1 Data Cache Store Misses |
| `L1_dcache_stores` | Level 1 Data Cache Stores |
| `L1_icache_load_misses` | Level 1 Instruction Cache Load Misses |
| `L1_icache_loads` | Level 1 Instruction Cache Loads |
| `branch_misses` | Branch Misses |
| `bus_cycles` | Bus Cycles |
| `cache_misses` | Cache Misses |
| `cache_references` | Cache References |
| `coreX` | CPU core X(X ranges from 1-128) utilization rate |
| `cpu_migrations` | CPU Migrations |
| `cpu_usage` | CPU utilization rate |
| `ctx_switches` | Context Switches |
| `cycles` | CPU Cycles |
| `dTLB_load_misses` | Data Translation Lookaside Buffer Load Misses |
| `flag1` | A bitmap(int32) indicating the CPU cores(1-32) enabled via sysfs. |
| `flag2` | A bitmap(int32) indicating the CPU cores(33-64) enabled via sysfs. |
| `flag3` | A bitmap(int32) indicating the CPU cores(65-96) enabled via sysfs.|
| `flag4` | A bitmap(int32) indicating the CPU cores(97-128) enabled via sysfs. |
| `freq1` | Frequency of the host's cpupower command output |
| `freq2` | Frequency of the host's cpupower command output |
| `freq3` | Frequency of the host's cpupower command output |
| `freq4` | Frequency of the host's cpupower command output |
| `freq5` | Frequency of the host's cpupower command output |
| `freq6` | Frequency of the host's cpupower command output |
| `freq7` | Frequency of the host's cpupower command output |
| `freq8` | Frequency of the host's cpupower command output |
| `iTLB_load_misses` | Instruction Translation Lookaside Buffer Load Misses |
| `instructions` | Instructions |
| `kvm_entry` | KVM Entry Count |
| `kvm_exit` | KVM Exit Count |
| `kvm_vcpu_wakeup` | KVM vCPU Wakeup Count |
| `load_1` | Load Average (1 minute) |
| `load_15` | Load Average (15 minutes) |
| `load_5` | Load Average (5 minutes) |
| `mem_usage` | Memory Usage |
| `page_faults` | Page Faults |
| `temp1` | Temperature of the host's sensors command output |
| `temp2` | Temperature of the host's sensors command output|
| `temp3` | Temperature of the host's sensors command output |
| `temp4` | Temperature of the host's sensors command output |
| `temp5` | Temperature of the host's sensors command output |
| `temp6` | Temperature of the host's sensors command output |
| `temp7` | Temperature of the host's sensors command output |
| `temp8` | Temperature of the host's sensors command output |
| `temp9` | Temperature of the host's sensors command output |
| `total_vcpu` | Total vCPUs |
| `total_vm` | Total VMs |


**Workload**

The dataset encompasses a diverse set of workloads designed to stress-test system performance under various scenarios:

1. For-And-Join: Emulates a concurrent programming model where multiple processes are spawned to execute independently, later synchronizing to await their collective completion.
2. Stress X-Y-Z: Utilizes the stress tool with X CPU threads, Y Memory threads, and Z IO threads. 
3. Kernel: Involves decompressing and building the Linux Kernel version 5.15.1 from a tarball.
4. Jenkins: Replay the actual build history extracted from the Apache Software Foundation's Jenkins server (ci-builds.apache.org). The detailed events log is in the file `assets/apache.out.csv`.
5. Synthetic: A random load, the events log is in the file `assets/event-gen.csv`.
6. SPECInt2006: Run the well-known benchmark SPEC 2006, the results and perf outputs is in directory `assets/spec`.
7. Google-v1: Google cluster replay (https://github.com/google/cluster-data), see `testgoogle.py` and `testscript.google.sh`.
8. Idle: No critical tasks.

**TEAP**

Our ongoing research, not yet published, enables software-hardware collaborative resource provisioning.
The genetic algorithm, along with a greedy algorithm for comparison, is located in `scripts/controller/algorithms.py`.
The models implementation are in `scripts/controller/`.

**FAN Mode**

1.PWM x/255: fixed PWM, this value x is stored in an unsigned byte. 
2.PID x: Using PID control strategy to keep the inlet temperature at x °C.
3.TEAP: Controlled by TEAP's hardware control strategy.
4.None: Set PWM to 0.

## Useful Scripts

Located in the `scripts` directory, these Python scripts facilitate preprocessing:

1. **split.py**: Divides the combined export into `bmc.csv` and `host.csv`. For further segmentation, customize the script or manually adjust.
2. **collapse.py**: Integrates `bmc.csv` and `host.csv` based on `_time` into a unified dataset.
3. **scidata.py**: Generates a simple figure of the `collapse.py`  outputs.

## Dataset Inventory

For clarity, here's a synopsis of included datasets, detailing fan control strategies and associated workloads. 

| File Name | Fan Mode | Method(Linux Governor) | Workload Description |
|-----------|----------|------------------------|----------------------|
| 202304252143.csv| PWM 90/255 | performance  | Idle |
| 202304252201.csv| PWM 30/255 | performance  | Idle |
| 202306181509.csv| PWM 30/255 | performance  | Idle |
| 202307301643.csv| PWM 30/255 | performance  | Idle |
| 202304252221.csv| PID 35 | performance  | Idle |
| 202306181534.csv| PID 35 | performance  | Idle |
| 202306172153.csv| PWM 255/255 | performance  | Idle |
| 202304261725.csv| PWM 30/255 | performance  | For-And-Join & 1 VMs |
| 202304281022.csv| PWM 30/255 | performance  | For-And-Join & 16 VMs |
| 202307301707.csv| PWM 30/255 | performance  | For-And-Join & 16 VMs |
| 202304281100.csv| PWM 30/255 | performance  | For-And-Join & 32 VMs |
| 202307301734.csv| PWM 30/255 | performance  | For-And-Join & 32 VMs |
| 202304281222.csv| PWM 30/255 | performance  | For-And-Join & 64 VMs |
| 202401042141.csv| PWM 30/255 | performance  | For-And-Join & 64 VMs |
| 202304281641.csv| PID 35 | performance  | For-And-Join & 1 VMs |
| 202306181554.csv| PID 35 | performance  | For-And-Join & 1 VMs |
| 202304281701.csv| PID 35 | performance  | For-And-Join & 16 VMs |
| 202306181617.csv| PPID 35 | performance  | For-And-Join & 16 VMs |
| 202307301947.csv| PID 35 | performance  | For-And-Join & 16 VMs |
| 202304281732.csv| PID 35 | performance  | For-And-Join & 32 VMs |
| 202306181653.csv| PID 35 | performance  | For-And-Join & 32 VMs |
| 202307301932.csv| PID 35 | performance  | For-And-Join & 32 VMs |
| 202306191023.csv| PID 35 | performance  | For-And-Join & 64 VMs |
| 202306181746.csv| PID 35 | performance  | For-And-Join & 64 VMs |
| 202306191745.csv| PID 45（CPU_Temp） | performance  | For-And-Join & 64 VMs |
| 202304281925.csv| PID 35 | performance  | For-And-Join & 1 VMs & vcpu_pcpu_map[0-1]->[0]|
| 202304281945.csv| PID 35 | performance  | For-And-Join & 1 VMs & vcpu_pcpu_map[0-1]->[0-1]|
| 202304282010.csv| PID 35 | performance  | For-And-Join & 1 VMs & vcpu_pcpu_map[0-1]->[0-2]|
| 202304282021.csv| PID 35 | performance  | For-And-Join & 1 VMs & vcpu_pcpu_map[0-1]->[0-3]|
| 202304282031.csv| PID 35 | performance  | For-And-Join & 1 VMs & vcpu_pcpu_map[0-1]->[0-4]|
| 202304282047.csv| PID 35 | performance  | For-And-Join & 1 VMs & vcpu_pcpu_map[0-1]->[0-5]|
| 202304282100.csv| PID 35 | performance  | For-And-Join & 1 VMs & vcpu_pcpu_map[0-1]->[0-6]|
| 202304282115.csv| PID 35 | performance  | For-And-Join & 1 VMs & vcpu_pcpu_map[0-1]->[0-7]|
| 202304282127.csv| PID 35 | performance  | For-And-Join & 1 VMs & vcpu_pcpu_map[0-1]->[0-8]|
| 202304282137.csv| PID 35 | performance  | For-And-Join & 1 VMs & vcpu_pcpu_map[0-1]->[0-9]|
| 202304282150.csv| PID 35 | performance  | For-And-Join & 1 VMs & vcpu_pcpu_map[0-1]->[0-3, 8]|
| 202304282208.csv| PID 35 | performance  | For-And-Join & 1 VMs & vcpu_pcpu_map[0-1]->[0-2, 8]|
| 202304282221.csv| PID 35 | performance  | For-And-Join & 1 VMs & vcpu_pcpu_map[0-1]->[0-1, 8-9]|
| 202304282238.csv| PID 35 | performance  | For-And-Join & 1 VMs & vcpu_pcpu_map[0-1]->[0, 4, 8, 12]|
| 202304282254.csv| PID 35 | performance  | For-And-Join & 1 VMs & vcpu_pcpu_map[0-1]->[0, 32, 64, 96]|
| 202308022155.csv| PWM 30/255 | performance  | For-And-Join & 16 VMs & vcpu_pcpu_map[0-31]->[0-15,64-79]|
| 202308022222.csv| PWM 30/255 | performance  | For-And-Join & 16 VMs & vcpu_pcpu_map[0-31]->[0-15,64-79]|
| 202306191544.csv| PWM 30/255～255/255 | performance  | For-And-Join & 64 VMs |
| 202306191555.csv| PWM 0/255 | performance  | For-And-Join & 64 VMs |
| 202307052240.csv| PWM 0/255 | performance  | Idle |
| 202307052253.csv| PWM 0/255 & recording noise  | performance  | Idle |
| 202307052309.csv| PWM 0/255～255/255 & recording noise  | performance  | Idle |
| 202306191641.csv| PID 35~45| performance  | For-And-Join & 64 VMs |
| 202307060022.csv| PWM 30/255 | performance  | Idle |
| 202307072156.csv| PID 35 | performance  | Idle |
| 202307191620.csv| PWM 30/255 | performance  | For-And-Join & 16 VMs |
| 202307191736.csv| PWM 30/255 | performance  | For-And-Join & 32 VMs & vcpu_pcpu_map[0-64]->[64-128]|
| 202307191816.csv| PWM 30/255 | performance  | For-And-Join & 32 VMs & vcpu_pcpu_map[0-64]->[0-63]|
| 202307070110.csv| PWM 30/255 | performance  | Idle & sysfs_enable_cpu（128->32）|
| 202307081826.csv| PWM 30/255 | performance  | Idle & sysfs_enable_cpu（128->32）|
| 202307201456.csv| PWM 30/255 | powersave  | Idle |
| 202307201552.csv| PWM 30/255 | performance  | Stress 64-0-0 & sysfs_enable_cpu（128->64） |
| 202307201616.csv| PWM 30/255 | performance  | Stress 64-0-0 & sysfs_enable_cpu（128->32） |
| 202307201629.csv| PWM 30/255 | performance  | Stress 64-0-0 & sysfs_enable_cpu（128->2） |
| 202307201723.csv| PWM 30/255 | powersave  | For-And-Join & 32 VMs |
| 202308022059.csv| PWM 30/255 | powersave  | For-And-Join & 16 VMs |
| 202307211105.csv| PWM 30/255  | ondemand  | For-And-Join & 32 VMs |
| 202308022117.csv| PWM 30/255  | ondemand  | For-And-Join & 16 VMs |
| 202308022245.csv| PID 35 | ondemand  | For-And-Join & 16 VMs |
| 202307211526.csv| PWM 30/255  | performance  | Stress 64-0-0 |
| 202307211550.csv| PWM 30/255  | performance  | Stress 0-64-0 |
| 202307211606.csv| PWM 30/255  | performance  | Stress 0-0-64 |
| 202307211757.csv| PWM 30/255  | performance  | For-And-Join & 16 VMs & sysfs_enable_cpu（128->32） |
| 202307301819.csv| PWM 30/255  | performance  | Stress 0-0-0～64-0-0 |
| 202307301853.csv| PWM 30/255  | performance  | Stress 0-0-0～0-64-0 |
| 202307302018.csv| PWM 30/255  | performance  | Stress 0-0-0～0-0-64～16-16-16~24-24-0 |
| 202307302044.csv| PWM 30/255 | performance  | Stress 0-24-24～24-0-24 |
| 202307311829.csv| PID 35 | performance  | Stress 0-0-0～164-0-0～116-16-16 |
| 202307311855.csv| PWM 30/255 | performance  | Stress 0-0-0～128-0-0 |
| 202307311923.csv| PWM 30/255 | performance  | Stress 0-0-0～128-0-0 |
| 202401042237.csv| PWM 30/255 | performance  | Stress 16-16-16 |
| 202401042338.csv| PWM 30/255 | performance  | Stress 32-32-0 |
| 202401050043.csv| TEAP | performance  | Stress 32-32-0 |
| 202307231421.csv| PWM 30/255 | TEAP  | For-And-Join & 16 VMs |
| 202307231405.csv| PWM 30/255 | TEAP  | For-And-Join & 16 VMs |
| 202307231452.csv| PWM 30/255 | TEAP  | For-And-Join & 32 VMs |
| 202307231511.csv| TEAP | TEAP  | For-And-Join & 1 VMs |
| 202307231535.csv| TEAP | TEAP  | For-And-Join & 16 VMs |
| 202307231604.csv| TEAP | TEAP  | For-And-Join & 32 VMs |
| 202308011635.csv| PWM 30/255 | TEAP  | Kernel & 16 VMs |
| 202308011759.csv| PID 35 | TEAP  | Kernel & 16 VMs |
| 202308051600.csv| PID 35 | TEAP-LSTM  | For-And-Join & 16 VMs |
| 202308051718.csv| PID 35 | TEAP-LSTM-Greedy  | Kernel & 16 VMs |
| 202308051737.csv| TEAP | TEAP  | For-And-Join & 16 VMs |
| 202308051757.csv| TEAP | TEAP  | For-And-Join & 16 VMs |
| 202308051827.csv| TEAP | TEAP  | For-And-Join & 32 VMs |
| 202308052003.csv| TEAP | TEAP  | Kernel & 16 VMs |
| 202309212229.csv| PWM 30/255 | TEAP  | Kernel & 16 VMs |
| 202309221110.csv| PWM 30/255 | TEAP  | Kernel & 16 VMs |
| 202309222035.csv| PWM 30/255 | TEAP  | Synthetic & 16 VMs |
| 202310252044.csv| PWM 30/255 | TEAP  | For-And-Join  & 16 VMs |
| 202310252102.csv| PWM 30/255 | TEAP  | For-And-Join  & 16 VMs |
| 202310252230.csv| PWM 30/255 | TEAP+IO  | Kernel & 16 VMs |
| 202405241724.csv| PWM 30/255 | performance  | Jenkins & 16 VMs |
| 202405241940.csv| PID 35 | performance  | Jenkins & 16 VMs |
| 202405242053.csv| PWM 30/255| powersave  | Jenkins & 16 VMs |
| 202405242207.csv| PWM 30/255| ondemand  | Jenkins & 16 VMs |
| 202405242318.csv| PWM 30/255| TEAP  | Jenkins & 16 VMs |
| 202406132127.csv| PID 35 | performance  | Jenkins & 16 VMs |
| 202411022113.csv| PWM 30/255 | LADPM  | Jenkins & 16 VMs |
| 202411022233.csv| PWM 30/255 | HFEE  | Jenkins & 16 VMs |
| 202410222030.csv| PWM 30/255 | performance  | SPECInt2006 |
| 202410230835.csv| PWM 30/255 | powersave  | SPECInt2006 |
| 202410232015.csv| PWM 30/255 | ondemand  | SPECInt2006 |
| 202410240010.csv| PID 35 | performance  | SPECInt2006 |
| 202410241952.csv| PWM 30/255 | TEAP  | SPECInt2006 |
| 202411010058.csv| PWM 30/255 | HFEE  | SPECInt2006 |
| 202411012156.csv| PWM 30/255 | LADPM  | SPECInt2006 |
| 202506031650.csv| PWM 30/255 | TEAP(SVM+GA)  | Google-v1 |
| 202506031715.csv| PWM 30/255 | TEAP(MLP+GA)  | Google-v1 |
| 202506031736.csv| PWM 30/255 | TEAP(LSTM+GA)  | Google-v1 |
| 202506041628.csv| PWM 30/255 | MultiThread-TEAP(SVM+GA)  | Google-v1 |
| 202506050014.csv| PWM 30/255 | MultiThread-TEAP(SVM+Greedy)   | Google-v1 |


