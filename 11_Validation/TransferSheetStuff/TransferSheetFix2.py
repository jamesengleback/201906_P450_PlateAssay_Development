import pandas as pd
from tqdm import tqdm


data = pd.read_csv('DraftTransferFormcpdplate.csv')
letters=['A','B','C','D','E','F','G','H','I','J','K','L','M','O','P']
output=pd.DataFrame(columns=data.columns)

for i in tqdm(data.index):
    row=data.loc[i,:]
    print(row)
    for j in range(0,8):
        newrow=row
        header_letter=newrow['DestinationPlateWell']


        newrow['SourcePlateWell']=letters[j]+newrow['SourcePlateWell'][1]
        newrow['DestinationPlateWell']=letters[j]+newrow['DestinationPlateWell'][1]
        output=output.append(newrow)
output=output.reset_index(drop=True)

print(output)
#output.to_csv('DraftTransferForm2_sheet2.csv')
