# -*- coding: UTF-8 -*-
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Read data from CSV file
df = pd.read_csv('collapse.csv')

# Data cleaning and processing
df = df.drop_duplicates()
df = df.fillna(0)

# Format date
df_mintime = pd.to_datetime(df['_time']).min()
df['_time'] = pd.to_datetime(df['_time']) - df_mintime
df['_time'] = df['_time'].dt.total_seconds()  # Convert time to seconds
df["Cpu1_Temp_Diff"] = df["Cpu1_Temp"].diff()
df["Cpu2_Temp_Diff"] = df["Cpu2_Temp"].diff()
df["AVG_CPU_TEMP"] = (df["Cpu1_Temp"] + df["Cpu2_Temp"])/2
df["AVG_CPU_TEMP_Diff"] = df["AVG_CPU_TEMP"].diff()
df["AVG_PSU_FAN"] = (df["PSU1_FAN"] + df["PSU2_FAN"])/2
df["Inlet_Temp_Diff"] = df["Inlet_Temp"].diff()
df['Total_Power'] = (df['PSU1_Total_Power'] + df['PSU2_Total_Power'])
df['P-Zone_Cores'] = 16 * sum((df[f'freq{i}'] == 2.1) for i in range(1, 9))
df['Thermal_Elasticity'] = (df['Total_Power']/(df['Inlet_Temp_Diff'] + 5))

df = df.fillna(0)

# Calculate statistical indicators
mean_fan = (df['FAN1'] + df['FAN2'] + df['FAN3'] + df['FAN4']) / 4
mean_fan_avg = mean_fan.mean()

# Create figure and main axis
fig, ax1 = plt.subplots(figsize=(8, 4.5))

# Plot temperature curve (left y-axis)
ax1.plot(df['_time'], df['AVG_CPU_TEMP'], label='AVG_CPU_TEMP', linestyle="-", color='r')
ax1.set_ylabel('Temperature (℃)')
ax1.set_xlabel('Time')
ax1.set_ylim(10, 60)

# Create second axis and plot power curve (right y-axis)
ax2 = ax1.twinx()
ax2.plot(df['_time'], df['Total_Power'], label='Power', linestyle="-.", color='g')
ax2.set_ylabel('Power (W)')

# Create third axis and plot fan speed curve (right y-axis)
ax3 = ax1.twinx()
ax3.set_ylim(1000, 9000)
ax3.spines['right'].set_position(('outward', 50))  # Adjust the position of the third axis
ax3.plot(df['_time'], df['PSU1_FAN'], label='PSU1_FAN', linestyle=":", color='b')
ax3.set_ylabel('Fan Speed')

ax4 = ax1.twinx()
ax4.set_ylim(-4, 104)
ax4.spines['right'].set_position(('outward', 120))  # Adjust the position of the fourth axis
ax4.plot(df['_time'], df['cpu_usage'], label='CPU Usage', linestyle="-", color='#ff9900', marker='+', markevery=5)
ax4.set_ylabel('Ratio (%)')

lines = [ax1.get_lines()[0], ax2.get_lines()[0], ax3.get_lines()[0], ax4.get_lines()[0]]
labels = [line.get_label() for line in lines]
plt.legend(lines, labels, loc='right', bbox_to_anchor=(0.7, 0.15))

plt.tight_layout()
plt.show()