import pandas as pd
import time
import subprocess

max_requests = 2000
access_token="11d2dd26350836839f36272767d7981e9d"

df = pd.read_csv('apache.out.csv')

df = df.sort_values(by='time')

min_time = df['time'].min()

if min_time < 0:
    df['time'] = df['time'] - min_time

df = df.head(max_requests)
lasttime = None

for index, row in df.iterrows():
    job_name = row['job_name']
    curtime = int(row['time'])
    if lasttime == None:
        sleep_time = 0
    else:
        sleep_time = curtime - lasttime
    lasttime = curtime

    timestamp = int(time.time())  
    curl_command = f"curl -u admin:{access_token} http://192.168.1.113:8080/job/{job_name}/build?token=teap&timestamp={timestamp}"

    print(curl_command)

    subprocess.run(curl_command, shell=True)

    time.sleep(sleep_time)


print(f"done {max_requests}")
