import pandas as pd
from tqdm import tqdm


data = pd.read_csv('DraftTransferFormsheet2.csv')
letters=['A','B','C','D','E','F','G','H']

output=pd.DataFrame(columns=data.columns)
for i in tqdm(data.index[:49]):
    row=data.loc[i,:]
    for j in range(0,8):
        newrow=row
        newrow['SourcePlateWell']=letters[j]+newrow['SourcePlateWell'][1]
        newrow['DestinationPlateWell']=letters[j]+newrow['DestinationPlateWell'][1]
        output=output.append(newrow)
output=output.reset_index(drop=True)

print(output)
#output.to_csv('DraftTransferForm2_sheet2.csv')
