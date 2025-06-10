#!/bin/sh
cpupower -c 0-127 frequency-set -g performance
cpupower -c 0-127 frequency-set -f 2100000

pids=$(ps -eo pid=,comm= | grep -v "^\[" | awk '{print $1}')
for pid in $pids; do
    taskset -p 0xFFFFFFFFFFFFFFFF $pid
done

max_cores=128
min_cores=32
numa_cores=8
numa_nodes=16
current_cores=$max_cores
idx=0

offline_cpu() {
    local cpu=$1
    if ((cpu >= 1 && cpu <= 127)); then
        echo 0 > /sys/devices/system/cpu/cpu$cpu/online
	echo offline $1
    fi
}

online_cpu() {
    local cpu=$1
    if ((cpu >= 1 && cpu <= 127)); then
        echo 1 > /sys/devices/system/cpu/cpu$cpu/online
	echo online $1
    fi
}

resume_vms() {
    local vm_list=$(virsh list --name | grep -v '^$')
    for vm_name in $vm_list; do
        virsh resume "$vm_name"
    done
}

pause_vms() {
    local vm_list=$(virsh list --name | grep -v '^$')

    for vm_name in $vm_list; do
        virsh suspend "$vm_name"
    done
}

set_cpuset() {
    sleep 3
    # pause_vms
    local cpuset_cores=$1
    local cpusetfiles=$(find /sys/fs/cgroup/cpuset/machine.slice -name cpuset.cpus)
    local max_retries=4
    local retries=0
    local success=false
    
    while [ $retries -lt $max_retries ]; do
        for cpusetfile in $cpusetfiles; do
            echo "$cpuset_cores" > "$cpusetfile"
            echo "$cpuset_cores > $cpusetfile"
        done

        success=true
        for cpusetfile in $cpusetfiles; do
            local content=$(cat "$cpusetfile")
            if [ "$content" != "$cpuset_cores" ]; then
                success=false
                break
            fi
        done

        if [ "$success" = true ]; then
            echo "cpuset success"
            break
        fi

        retries=$((retries + 1))
        sleep 1  # 可以适当增加延迟时间
    done

    if [ "$success" = false ]; then
        echo "fail to set cpuset"
    fi
}

update_cpuset() {
    local cpu_list=$1
    local mode=$2
    local current_cpuset="0-127"
    local updated_cpuset=""
    local cpus_to_remove=(${cpu_list//,/ })

    if [ "$mode" = "remove" ]; then
        for cpu in $(seq 0 127); do
            if [[ ! " ${cpus_to_remove[@]} " =~ " ${cpu} " ]]; then
                updated_cpuset="${updated_cpuset},${cpu}"
            fi
        done
        updated_cpuset=${updated_cpuset:1}  # Remove the leading comma
    else
        updated_cpuset="0-127"
    fi

    set_cpuset "$updated_cpuset"
}

for ((i = 0; i < max_cores; i++)); do
	online_cpu $i
done

set_cpuset "0-127"

while true
do
    sleep 5
    echo -n "."

    output=$(usbbmc -t redfish -d '[{"method":"PUT","url":"/hyperbmc/run-script/request-instruction/0"}]' | jq -r '.data.output')
    echo $output
    if [[ "$output" == "hot-freqset"* ]]; then
        cpu_list=${output#hot-freqset-}
        for cpu in ${cpu_list//,/ }; do
            cpupower -c $cpu frequency-set -f 1100000
            echo "cpupower -c $cpu frequency-set -f 1100000"
        done
        update_cpuset "$cpu_list" "remove"
        echo "Hot - Frequency set to 1100000 for CPUs: $cpu_list"
    elif [[ "$output" == "cold-freqset"* ]]; then
        cpu_list=${output#cold-freqset-}
        for cpu in ${cpu_list//,/ }; do
            cpupower -c $cpu frequency-set -f 2100000
            echo "cpupower -c $cpu frequency-set -f 2100000"
        done
        update_cpuset "$cpu_list" "recover"
        echo "Cold - Frequency set to 2100000 for CPUs: $cpu_list"
    elif [ "$output" = "hot" ]; then
        if [ $current_cores -gt $min_cores ]; then
            idx=$((idx + 1))
            for ((i = 0; i < numa_nodes; i++)); do
                offline_cpu $((i * numa_cores + idx))
            done
            current_cores=$((current_cores - numa_nodes))
            echo " Cold - Remaining cores：$current_cores"
        fi
    elif [ "$output" = "cold" ]; then
        if [ $current_cores -lt $max_cores ]; then
            idx=$((idx - 1))
            if [ $idx -lt 0 ]; then
                idx=0
            fi
            for ((i = 0; i < numa_nodes; i++)); do
                online_cpu $((i * numa_cores + idx))
                idx=$((idx - 1))
            done
	    #update cpuset
        set_cpuset "0-127"
	    current_cores=$((current_cores + numa_nodes))
            echo "Cold - Remaining cores: $current_cores"
        fi
    elif [[ "$output" == "tunerange-"* ]]; then
        # 从输出中获取分配方案
        cpu_alloc=${output#tunerange-}
        # 分割为数组
        IFS=',' read -r -a vm_cpu_array <<< "$cpu_alloc"
        vm_count=${#vm_cpu_array[@]}

        for ((i = 0; i < vm_count; i++)); do
            # 获取当前虚拟机名称
            vm_name="vm$((i + 1))"
            pid=`ps -ef | grep "$vm_name," | grep -v grep | awk '{print $2}'`
            # 获取虚拟机的 CPU 分配
            vm_cpus=${vm_cpu_array[i]}
            # 判断 vm_cpus 是否小于 0
            if [ "$vm_cpus" -lt 0 ]; then
                echo "The number of CPUs ($vm_cpus) for VM $vm_name is invalid, skipping this VM."
                continue
            fi
             
            STARTCORE=$((i*8))
            ENDCORE=$((STARTCORE + vm_cpus - 1))
            taskset -pca $STARTCORE-$ENDCORE $pid
        done
    elif [[ "$output" == "noise-"* ]]; then
        # 格式: noise-<busy_cpus>-<idle_cpus>
        busycores=$(echo "$output" | cut -d '-' -f 2)
        idlecores=$(echo "$output" | cut -d '-' -f 3)

        echo " busy cores: $busycores"
        echo " idle cores: $idlecores"

        # 对于 busycores 中的每个 CPU，先查询唯一的线程组ID (tgid)
        for cpu in ${busycores//,/ }; do
            # 使用 ps 输出 tgid、psr 和 comm，过滤掉以 [ 开头的内核线程,反正taskset不会迁移这些内核线程
            # 然后利用 sort 和 uniq 去重，只保留唯一的 tgid
            tgids=$(ps -eo tgid,psr,comm | awk -v target="$cpu" '$2==target && $3 !~ /^\[/ && $3 !~ /noise/ && $3 !~ /nc_/ {print $1}' | sort -n | uniq)
            
            count=0
            for tgid in $tgids; do
                # 仅迁移一半的进程
                if [ $((count % 2)) -eq 0 ]; then
                    # 迁移整个线程组
                    taskset -pca "$idlecores" "$tgid"
                    echo "taskset -pca $idlecores $tgid"
                    echo "(tgid: $tgid) -> CPU: $idlecores"
                fi
                count=$((count + 1))
            done
        done
    else
        echo " Empty - Remaining cores: $current_cores"
    fi
done
