import pandas as pd
import matplotlib.pyplot as plt

# === Load data ===
df = pd.read_csv('google-cluster-data-1.csv', delim_whitespace=True, engine='python')

# === Keep only records with non-zero CPU usage ===
df = df[df['NrmlTaskCores'] > 0].copy()

# === Convert TaskID to string ===
df['TaskID'] = df['TaskID'].astype(str)

# === Global statistics ===
max_cpu_row = df.loc[df['NrmlTaskCores'].idxmax()]
max_mem_row = df.loc[df['NrmlTaskMem'].idxmax()]

# Minimum (non-zero) values
min_cpu_row = df.loc[df['NrmlTaskCores'].idxmin()]
min_mem_row = df.loc[df['NrmlTaskMem'].idxmin()]

print("\nGlobal max/min resource usage:")
print(f"Max CPU usage: {max_cpu_row['NrmlTaskCores']:.4f} (TaskID: {max_cpu_row['TaskID']}, Time: {max_cpu_row['Time']})")
print(f"Min CPU usage: {min_cpu_row['NrmlTaskCores']:.4f} (TaskID: {min_cpu_row['TaskID']}, Time: {min_cpu_row['Time']})")
print(f"Max memory usage: {max_mem_row['NrmlTaskMem']:.4f} (TaskID: {max_mem_row['TaskID']}, Time: {max_mem_row['Time']})")
print(f"Min memory usage: {min_mem_row['NrmlTaskMem']:.4f} (TaskID: {min_mem_row['TaskID']}, Time: {min_mem_row['Time']})")

# === Track min/max CPU usage per TaskID ===
cpu_ranges = {}  # taskid -> [min, max]
for row in df.itertuples(index=False):
    tid = row.TaskID
    val = row.NrmlTaskCores
    if tid not in cpu_ranges:
        cpu_ranges[tid] = [val, val]
    else:
        cpu_ranges[tid][0] = min(cpu_ranges[tid][0], val)
        cpu_ranges[tid][1] = max(cpu_ranges[tid][1], val)

# === Calculate CPU usage range (max - min) per task ===
task_range_list = [(tid, max_val - min_val) for tid, (min_val, max_val) in cpu_ranges.items()]

# === Sort by CPU usage fluctuation and select top 10 ===
sorted_ranges = sorted(task_range_list, key=lambda x: x[1], reverse=True)[:16]

# === Print top fluctuating tasks ===
print("\n Top 10 tasks with highest CPU usage fluctuation:")
for tid, rng in sorted_ranges:
    print(f"TaskID {tid}: CPU Range = {rng:.6f}")

# === Plot CPU usage curves ===
plt.figure(figsize=(14, 6))
for tid, _ in sorted_ranges:
    task_df = df[df['TaskID'] == tid].sort_values(by='Time')
    plt.plot(task_df['Time'], task_df['NrmlTaskCores'], label=f'Task {tid[:6]}...')

plt.title('Top 10 Tasks with Largest CPU Usage Range')
plt.xlabel('Time (sec)')
plt.ylabel('Normalized CPU Usage')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# === Plot corresponding memory usage curves ===
plt.figure(figsize=(14, 6))
for tid, _ in sorted_ranges:
    task_df = df[df['TaskID'] == tid].sort_values(by='Time')
    plt.plot(task_df['Time'], task_df['NrmlTaskMem'], label=f'Task {tid[:6]}...')

plt.title('Top 10 Tasks - Corresponding Memory Usage')
plt.xlabel('Time (sec)')
plt.ylabel('Normalized Memory Usage')
plt.legend()
plt.grid(True)
plt.t
