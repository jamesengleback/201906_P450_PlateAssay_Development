import os
import numpy as np
import pandas as pd 
from scipy import optimize

def parse_bmg(path: str) -> pd.DataFrame:
    # find header
    with open(path, 'r') as f:
        for row_num, row in enumerate(f):
            if  len(row.split(',')) > 500 or 'Well Row' in row:
                break
    df = pd.read_csv(path, skiprows=row_num)
    # drop 'Unnamed' column 
    df = df.loc[:, df.columns.str.contains('Unnamed') == False]
    if 'Well Row' in df.columns:
        df.index = [f'{i}{j}'.replace('.0','') for i, j in zip(df['Well Row'], 
                                                               df['Well Col'])]
    else:
        import ipdb ; ipdb.set_trace()
    #df = df.dropna(axis=0) # drop empty rows
    df = df.iloc[1:, 3:]
    df.columns = df.columns.str.extract('([0-9]+)')[0].astype(int)
    return df



