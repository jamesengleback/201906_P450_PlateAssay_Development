import pandas as pd


def parse_bmg(path: str) -> pd.DataFrame:
    # find header
    with open(path, 'r') as f:
        for row_num, row in enumerate(f):
            if len(row.split(',')) > 500 or 'Well Row' in row:
                break
    df = pd.read_csv(path, skiprows=row_num)
    # drop 'Unnamed' column
    df = df.loc[:, df.columns.str.contains('Unnamed') == False]
    if 'Well Row' in df.columns:
        df.index = [f'{i}{j}'.replace('.0', '') for i, j in zip(df['Well Row'],
                                                                df['Well Col'])
                    ]
        df.columns = df.columns.str.extract('([0-9]+)')[0]
        df = df.dropna()
        df = df.loc[:, df.columns.dropna()]

    elif "Well" in df.columns:
        wells = [f'{i}{int(j) if j.isnumeric() else None}' for i, j in zip(
                                df['Well'].str.extract('([A-Z])')[0],
                                df['Well'].str.extract('([0-9]+)').astype(str)[0]
                                          )
                    ]
        wavelengths = df.iloc[0, :].astype(str).str.extract('([0-9]+)')[0]

        df.index = wells
        df.columns = wavelengths
        df = df.iloc[1:, 2:]
    else:
        import ipdb ; ipdb.set_trace()
    df.columns = df.columns.astype(int)
    # df = df.dropna(axis=0) # drop empty rows
    return df
