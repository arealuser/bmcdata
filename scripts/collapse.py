import csv
import pandas as pd

with open('bmc.csv', 'r') as file1, open('host.csv', 'r') as file2:
    reader1 = csv.reader(file1)
    reader2 = csv.reader(file2)
    data1 = list(reader1)
    data2 = list(reader2)

df1 = pd.DataFrame(data1[1:], columns=data1[0])
df2 = pd.DataFrame(data2[1:], columns=data2[0])


df1['_time'] = pd.to_datetime(df1['_time'])
df2['_time'] = pd.to_datetime(df2['_time'])


merged_df = pd.merge_asof(df2, df1, on='_time', direction='nearest')


merged_df.to_csv('collapse.csv', index=False)
