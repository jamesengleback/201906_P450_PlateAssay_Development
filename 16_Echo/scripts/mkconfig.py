import re
import os
import json
import pandas as pd

def read_xml_picklist(path):
    assert os.path.exists(path)
    pats = {'Src': 'SrcID="([0-9\.]+)"',
            'Dest': 'DestID="([0-9\.])+"',
            'Volume': 'Volume="([0-9\.])+"',
            }
    data = {}
    with open(path, 'r') as f:
        for i, row in enumerate(f):
            row_data = {}
            for name, pat in zip(pats.keys(), pats.values()):
                srch = re.search(pat, row)
                if srch:
                    row_data[name] = srch.group(1)
            data[i] = row_data
    df = pd.DataFrame(data).T.dropna()
    return df


def main():
    cwd = os.path.dirname(os.path.expanduser(__file__))

    picklist_dir = os.path.join(cwd, 'picklists')
    log_dir = os.path.join(cwd, 'log')
    data_dir = os.path.join(cwd, 'data')

    import ipdb ; ipdb.set_trace()

if __name__ == "__main__":
    main()
