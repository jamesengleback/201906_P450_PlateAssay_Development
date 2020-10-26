import pandas as pd
from tqdm import tqdm

assayplate=pd.read_csv('PlateLayout1.csv')
letters=['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P']
oddletters=letters[0::2]
evenletters=letters[1::2]


def protein_transfer(assayPlate):
    bufferConditions=assayplate.loc[:,['Kpi /MM','Kcl/mM']].drop_duplicates()
    bufferConditions.index+=1

    Output = pd.DataFrame(columns=['Volume','SourcePlateBarcode','SourcePlateWell',
    'DestinationPlateBarcode','DestinationPlateWell','ComponentName'])

    for i in tqdm(assayPlate.index):
        for j in range(8):
            row=assayPlate.loc[i,:]
            Volume=25
            SourcePlateBarcode='MasterTrof'
            SourcePlateWell=letters[j]+str(match_buffers_2_trof(row, bufferConditions))
            DestinationPlateBarcode='assayplate'
            DestinationPlateWell=oddletters[j]+str(i+1)
            ComponentName='Protein'
            temp=pd.DataFrame([[Volume,SourcePlateBarcode,SourcePlateWell,DestinationPlateBarcode,DestinationPlateWell,ComponentName]],\
            columns=['Volume','SourcePlateBarcode','SourcePlateWell','DestinationPlateBarcode','DestinationPlateWell','ComponentName'])
            Output=Output.append(temp)
    Output.reset_index(drop=True,inplace=True)
    return Output

def match_buffers_2_trof(row,mastertrof):
    #buffer = row.loc[['Kpi /MM','Kcl/mM']]
    mtrof=mastertrof.loc[mastertrof['Kpi /MM']==row['Kpi /MM']]
    mtrof=mtrof.loc[mtrof['Kcl/mM']==row['Kcl/mM']]
    return mtrof.index.values[0]

def distrubute_buffer():
    output=pd.DataFrame(columns=['Volume', 'SourcePlateBarcode',
    'SourcePlateWell', 'DestinationPlateBarcode' ,'DestinationPlateWell', 'ComponentName'])
    for j in tqdm(evenletters):
        for i in range(1,25):
            row=pd.DataFrame(columns=['Volume', 'SourcePlateBarcode',
            'SourcePlateWell', 'DestinationPlateBarcode' ,'DestinationPlateWell', 'ComponentName'])

            row.loc[0,'Volume']=25
            row.loc[0,'SourcePlateBarcode']='MasterTrof'
            row.loc[0,'DestinationPlateBarcode']='assayplate'
            row.loc[0,'ComponentName']='Buffer'
            row.loc[0,'SourcePlateWell']='A8'
            row.loc[0,'DestinationPlateWell']=j+str(i)
            output=output.append(row)
    output=output.reset_index(drop=True)
    return output

def distribute_compounds():
    source_columns={'DMSO':6,'Arachadionic Acid':7, 'Lauric Acid':8,'Palmitic Acid':9,'4-Phenylimidazole':10}
    output=pd.DataFrame(columns=['Volume', 'SourcePlateBarcode',
    'SourcePlateWell', 'DestinationPlateBarcode' ,'DestinationPlateWell', 'ComponentName'])
    for i in tqdm(assayplate.index):
        substrate=assayplate.loc[i,'Substrate']
        sourcecol=source_columns[substrate]
        for j in range(8):
            row=pd.DataFrame(columns=['Volume', 'SourcePlateBarcode',
            'SourcePlateWell', 'DestinationPlateBarcode' ,'DestinationPlateWell', 'ComponentName'])

            row.loc[0,'Volume']=25
            row.loc[0,'SourcePlateBarcode']='CompoundPlate'
            row.loc[0,'DestinationPlateBarcode']='assayplate'
            row.loc[0,'ComponentName']='compound'
            row.loc[0,'SourcePlateWell']=letters[j]+str(sourcecol)
            row.loc[0,'DestinationPlateWell']=oddletters[j]+str(i+1)
            output=output.append(row)

            row=pd.DataFrame(columns=['Volume', 'SourcePlateBarcode',
            'SourcePlateWell', 'DestinationPlateBarcode' ,'DestinationPlateWell', 'ComponentName'])

            row.loc[0,'Volume']=25
            row.loc[0,'SourcePlateBarcode']='CompoundPlate'
            row.loc[0,'DestinationPlateBarcode']='assayplate'
            row.loc[0,'ComponentName']='compound'
            row.loc[0,'SourcePlateWell']=letters[j]+str(sourcecol)
            row.loc[0,'DestinationPlateWell']=evenletters[j]+str(i+1)
            output=output.append(row)
    return output.reset_index(drop=True)

def main():
    output=protein_transfer(assayplate)
    output=output.append(distrubute_buffer())
    output=output.append(distribute_compounds())
    output.reset_index(drop=True,inplace=True)
    output.to_csv('20190722_DraftTransferWithBufferandCompounds_sheet2.csv')
main()
