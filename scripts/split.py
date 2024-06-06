import pandas as pd

def split_and_process_text(input_file):
    with open(input_file, 'r') as file:
        content = file.readlines()

    sections = []
    current_section = None
    bmcidx=-1
    hostidx=-1
    
    for line in content:
        if len(line)==0:
            continue

        if line.startswith("#group"):
            items=[]
            sections.append(items)
        elif line.startswith("#"):
            continue
        else:
            if "_time" in line or "bmc" in line or "host" in line:
                sections[-1].append(line.rstrip('\n'))
            
                if "bmc" in line.lower():
                    if bmcidx == -1:
                        bmcidx = len(sections) - 1
                elif "host" in line.lower():
                    if hostidx == -1:
                        hostidx = len(sections) - 1


    bmc_df = pd.DataFrame([row.split(',') for row in sections[bmcidx][1:]], columns=sections[bmcidx][0].split(','))
    host_df = pd.DataFrame([row.split(',') for row in sections[hostidx][1:]], columns=sections[hostidx][0].split(','))
    
    cols_to_drop = [0, 1, 2, 3, 4, 6, 7]
    bmc_df.drop(columns=bmc_df.columns[cols_to_drop], inplace=True)
    host_df.drop(columns=host_df.columns[cols_to_drop], inplace=True)
    

    bmc_df.to_csv('bmc.csv', index=False)
    host_df.to_csv('host.csv', index=False)


input_txt_file = '../data/202309222035.csv'  # The path to csv
split_and_process_text(input_txt_file)
