#!/bin/bash
#running on host
# Define InfluxDB parameters
cpu_cores=$(lscpu | awk '/^CPU:/ {print $2}')
echo $cpu_cores

while [ 1 ]; do
    sleep 1
    # Get CPU usage percentage
    cpu_usage=$(top -bn1 | awk '/Cpu/ {printf "%.2f", $2+$4}')
    # Get system load average
    loadoutput=$(uptime)
    IFS=' ' read -ra loadarr <<< "$loadoutput"
    load_1=${loadarr[-3]%,}
    load_5=${loadarr[-2]%,}
    load_15=${loadarr[-1]}
    # Get memory usage percentage
    mem_usage=$(free | awk '/Mem/ {printf "%.2f", $3/$2 * 100.0}')
    mpstat_output=$(mpstat -P ALL 1 1)
    core_usage=($(echo "$mpstat_output" | awk '/平均时间:/ && $2 ~ /^[0-9]+$/ {print 100-$NF}'))
    
    # Get perf stats
    perf_stats=$(sudo perf stat -a -e bus-cycles,context-switches,cpu-migrations,page-faults,cycles,instructions,branch-misses,cache-misses,cache-references,kvm:kvm_entry,kvm:kvm_exit,kvm:kvm_vcpu_wakeup,L1-dcache-load-misses,L1-dcache-loads,L1-dcache-store-misses,L1-dcache-stores,L1-icache-load-misses,L1-icache-loads,dTLB-load-misses,iTLB-load-misses \
    sleep 1 2>&1 | sed 's/,//g' | awk '/bus-cycles/ {bus_cycles=$1} /context-switches/ {ctx_switches=$1} /cpu-migrations/ {cpu_migrations=$1} \
    /page-faults/ {page_faults=$1} /cycles/ {cycles=$1} /instructions/ {instructions=$1} /branches/ {branches=$1} /branch-misses/ {branch_misses=$1} \
    /cache-misses/ {cache_misses=$1} /cache-references/ {cache_references=$1} /kvm:kvm_entry/ {kvm_entry=$1} /kvm:kvm_exit/ {kvm_exit=$1} /kvm:kvm_vcpu_wakeup/ {kvm_vcpu_wakeup=$1} \
    /L1-dcache-load-misses/ {L1_dcache_load_misses=$1} /L1-dcache-loads/ {L1_dcache_loads=$1} /L1-dcache-store-misses/ {L1_dcache_store_misses=$1} \
    /L1-dcache-stores/ {L1_dcache_stores=$1} /L1-icache-load-misses/ {L1_icache_load_misses=$1} /L1-icache-loads/ {L1_icache_loads=$1} \
    /dTLB-load-misses/ {dTLB_load_misses=$1} /iTLB-load-misses/ {iTLB_load_misses=$1} \
    END {print "bus_cycles=" bus_cycles ",ctx_switches=" ctx_switches ",cpu_migrations=" cpu_migrations ",page_faults=" page_faults ",cycles=" cycles \
    ",instructions=" instructions ",branch_misses=" branch_misses ",cache_misses=" cache_misses ",cache_references=" cache_references ",kvm_entry=" kvm_entry ",kvm_exit=" kvm_exit ",kvm_vcpu_wakeup=" kvm_vcpu_wakeup \
    ",L1_dcache_load_misses=" L1_dcache_load_misses ",L1_dcache_loads=" L1_dcache_loads ",L1_dcache_store_misses=" L1_dcache_store_misses \
    ",L1_dcache_stores=" L1_dcache_stores ",L1_icache_load_misses=" L1_icache_load_misses ",L1_icache_loads=" L1_icache_loads \
    ",dTLB_load_misses=" dTLB_load_misses ",iTLB_load_misses=" iTLB_load_misses}')

    core_line=""
    closed_cores=()
    closed_cores_index=0
    core_usage_index=0

    # 寻找关闭的核心
    for ((i=1; i<$cpu_cores; i++)); do
    if [ "$(cat /sys/devices/system/cpu/cpu$i/online)" = "0" ]; then
            closed_cores+=($i)
    fi
    done

    # 关闭核心的标记,0是全部开启
    flag1=0
    flag2=0
    flag3=0
    flag4=0

    for core in "${closed_cores[@]}"; do
    if [ $core -lt 32 ]; then
        flag1=$((flag1 | (1 << $core)))
    elif [ $core -lt 64 ]; then
        flag2=$((flag2 | (1 << ($core - 32))))
    elif [ $core -lt 96 ]; then
        flag3=$((flag3 | (1 << ($core - 64))))
    else
        flag4=$((flag4 | (1 << ($core - 96))))
    fi
    done

    # Create InfluxDB line protocol for per-core CPU usage
    for ((i=0; i<$cpu_cores; i++)); do
    if [ $closed_cores_index -lt ${#closed_cores[@]} ] && [ $i -eq ${closed_cores[$closed_cores_index]} ]; then
        core_line+=",core$i=-1"
        ((closed_cores_index++))
    else
        if [ $core_usage_index -lt ${#core_usage[@]} ]; then
            core_line+=",core$i=${core_usage[$core_usage_index]}"
            ((core_usage_index++))
        else
            core_line+=",core$i=-1"
        fi
    fi
    done

    core_line+=",flag1=$((flag1)),flag2=$((flag2)),flag3=$((flag3)),flag4=$((flag4))"

    
    # Create InfluxDB line protocol for host CPU, memory and load
    influxline="$influxdb_measurement,device_id=host cpu_usage=$cpu_usage,load_1=$load_1,load_5=$load_5,load_15=$load_15,mem_usage=$mem_usage,$perf_stats$core_line"
    
    ptemps=$(sensors -u | grep "temp[1-8]_input" | awk '{print $2}')
    ptempsi=1
    for temp in $ptemps
    do
    influxline+=",temp$ptempsi=$temp"
    ((ptempsi++))
    done

    for ((i=0; i<8; i++))
    do
        # 获取当前核心的频率信息
        output=$(cpupower -c $((i*16)) frequency-info | grep "current CPU frequency" | awk '{print $4}')
        # 如果频率信息为空，则将其填充为0
        if [ -z "$output" ]; then
            output="0"
        fi
        # 将频率信息拼接到结果字符串中
        influxline+=",freq$((i+1))=${output}"
    done

    total_vm=$(virsh list --name | grep -v '^$' | wc -l)
    influxline+=",total_vm=${total_vm}"

    total_vcpu=0
    vms=$(virsh list --name)
    for vm in $vms
    do
        vcpu_count=$(virsh vcpupin $vm | tail -n +3 | grep -v '^$' | wc -l)
        # 将虚拟机的vcpu数量加到总数上
        total_vcpu=$((total_vcpu + vcpu_count))
    done
    influxline+=",total_vcpu=${total_vcpu}"

    echo $influxline
    # send to controller via BMC
done

