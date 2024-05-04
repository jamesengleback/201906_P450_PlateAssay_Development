import pandas as pd 

def parse_spec(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    initial_columns = df.columns 
    wavelength_col_num = df.iloc[0,:].to_list().index('Wavelength (nm)')
    wavelengths_ = df.iloc[:, wavelength_col_num]
    wavelengths = wavelengths_.loc[wavelengths_.str.match('[0-9\.]+')]
    df = df.loc[wavelengths.index, :]
    df = df.iloc[:, 1::2]
    df.columns = initial_columns[:-1:2]
    return df
