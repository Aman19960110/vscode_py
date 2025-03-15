import pandas as pd
data = pd.read_csv(r"C:\Users\amany\Downloads\2025-03-13T18-48_export.csv")
stock_list = data['Unnamed: 0'].unique()
mis_match = []
for stock in stock_list:
    if stock == 'ADANIGREEN':
        df = data[data['Unnamed: 0']==stock]
        sum_pe = df.groupby(by='Unnamed: 7').sum()
        if sum_pe['Unnamed: 9'][0]==sum_pe['Unnamed: 9'][1]==sum_pe['Unnamed: 9'][2]:
            print('position is matched')