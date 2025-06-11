import os
import time
import psutil
import random
import re

def set_cpu_frequency(core_range, freq):
    os.system(f"cpupower -c {core_range} frequency-set -f {freq}")

def get_pid(process_name, PID_TO_NAME):
    pids = []
    for p in psutil.process_iter(['pid', 'name']):
        if process_name in p.info['name']:
            pid = int(p.info['pid'])
            PID_TO_NAME[pid] = process_name  
            pids.append(pid)
    return pids

def get_vm_pid(process_name, PID_TO_NAME):
    pids = []

    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            
            cmdline = p.info['cmdline']
            if cmdline is not None:
                cmdline_str = ' '.join(cmdline)
                
                if (process_name + ",") in cmdline_str:
                    pid = int(p.info['pid'])
                    PID_TO_NAME[pid] = process_name  
                    pids.append(pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            
            continue
    return pids



# initinit
BG_WORKLOAD = [
    'virt-manager', 'kubelet', 'pmdaproc', 'dockerd', 'kube-apiserver', 'etcd', 'sssd_nss', 
    'kube-controller', 'sysinfo.sh', 'systemd', 'Xorg', 'libvirtd', 'dbus-daemon', 'pmdalinux', 
    'containerd', 'kube-scheduler', 'python2', 'irqbalance', 'mate-indicators', 'systemd-journal', 
    'rsyslogd', 'pmdaxfs', 'containerd-shim'
]
KEY_WORKLOAD = ['vm1', 'vm2', 'vm3', 'vm4', 'vm5', 'vm6', 'vm7', 'vm8', 'vm9', 'vm10', 'vm11', 'vm12', 'vm13', 'vm14', 'vm15', 'vm16']

# EER
EER = {
    'vm1': 1.498867979, 'vm2': 1.498867979, 'vm3': 1.498867979, 'vm4': 1.498867979, 'vm5': 1.498867979,
    'vm6': 1.498867979, 'vm7': 1.498867979, 'vm8': 1.498867979, 'vm9': 1.498867979, 'vm10': 1.498867979,
    'vm11': 1.498867979, 'vm12': 1.498867979, 'vm13': 1.498867979, 'vm14': 1.498867979, 'vm15': 1.498867979, 
    'vm16': 1.498867979, 'virt-manager': 0.996880568, 'kubelet': 1.349174515, 'pmdaproc': 0.830022042, 
    'dockerd': 0.822222104, 'kube-apiserver': 0.805427996, 'etcd': 0.904172138, 'sssd_nss': 0.853351085,
    'kube-controller': 0.650313306, 'sysinfo.sh': 0.132334365, 'systemd': 7.208607532, 'Xorg': 0.6600612,
    'libvirtd': 0.767561321, 'dbus-daemon': 0.851615676, 'pmdalinux': 0.828285893, 'containerd': 1.344935543,
    'kube-scheduler': 0.454533326, 'python2': 0.768752213, 'irqbalance': 0.85963623, 'mate-indicators': 0.846391651,
    'systemd-journal': 0.845705604, 'rsyslogd': 1.034104319, 'pmdaxfs': 0.895151189, 'containerd-shim': 0.844010759
}

# standardize
eer_values = list(EER.values())
min_eer = min(eer_values)
max_eer = max(eer_values)
print("min_eer:", min_eer, "max_eer:", max_eer)
EER_normal = {k: (v - min_eer) / (max_eer - min_eer) for k, v in EER.items()}

print("EER_normal", EER_normal)
# set cpu frequency
BIG_CLUSTER = "0-63"
LITTLE_CLUSTER = "64-127"
set_cpu_frequency(BIG_CLUSTER, "2100000000")  # big
set_cpu_frequency(LITTLE_CLUSTER, "1100000000")  # little

SLEEP_TIME = 10

PID_TO_NAME = {}

BG_PIDS = sum([get_pid(name, PID_TO_NAME) for name in BG_WORKLOAD], [])
KEY_PIDS = sum([get_vm_pid(name, PID_TO_NAME) for name in KEY_WORKLOAD], [])

print("PID_TO_NAME:", PID_TO_NAME)


K = {pid: 0 for pid in BG_PIDS + KEY_PIDS} 


def calculate_scores(pids, EER_normal):
    scores = {}
    for pid in pids:
        eer_value = EER_normal.get(PID_TO_NAME[pid], 0.5)  #default eer_value is 0.5
        k_value = K.get(pid, 1)  
        scores[pid] = eer_value + (eer_value / 0.5 - 1) * k_value
    return scores

for pid in BG_PIDS + KEY_PIDS:
	core_range = random.choice([BIG_CLUSTER, LITTLE_CLUSTER])
	print(f"taskset -pc {core_range} {pid}")
	os.system(f"taskset -pc {core_range} {pid}")


while True:
    scores = calculate_scores(BG_PIDS + KEY_PIDS, EER_normal)
    print("scores:", scores)
    print("K:", K)
    

    for pid in BG_PIDS + KEY_PIDS:
        try:
            process = psutil.Process(pid)
            score = scores[pid]
            core_range = ""

            if score > 0.9:
                core_range = BIG_CLUSTER
                K[pid] = 0  
            elif score < 0.1:
                core_range = LITTLE_CLUSTER
                K[pid] = 0  
            else:
            
                core_range = random.choice([BIG_CLUSTER, LITTLE_CLUSTER])
                K[pid] += 1  # increase the waiting epochs
            
            print(f"taskset -pc {core_range} {pid}")
            os.system(f"taskset -pc {core_range} {pid}")

        except Exception as e:
            print(f"Error setting affinity for PID {pid}: {e}")
            
	## We are not considering fairness here. If fairness needs to be considered, you must measure the SPEC performance at different big cluster frequencies and then calculate an array.
    
    time.sleep(SLEEP_TIME)
