import pandas as pd


def parse(path):
    df = pd.read_csv(path)
    df = df.iloc[1:, :-1]
    df = df.dropna()
    cols = df.columns
    wavelengths = df.iloc[:, 0]
    df = df.iloc[:, 1::2]
    df.columns = cols[::2]
    df.index = wavelengths.astype(float).round(2)
    return df.astype(float)
