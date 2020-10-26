import pandas as pd
import numpy as np
from tqdm import tqdm

assayPlate = pd.read_csv('PlateLayout1.csv')
ExampleSheet = pd.read_csv('Example_Transfer_form.csv')
MasterPlate = pd.read_csv('masterplate_df.csv')
TransferSheet = pd.DataFrame(columns = ExampleSheet.columns)
Letters = ['A','B','C','D','E','F','G','H']
Leters384=['A','B','C','D','E','F','G','H','I','J','K','M','N','O','P']
columns=['Row','Column','Content','Vol','Kpi /MM','Kcl/mM']

'''
The plan:
1. Re-format the MasterPlate and assayPlate to have well indices
and Stuff
2. Make master trough plate
3. Put together a new transfer sheet for one plate with easy options
to change source wells as I run out of mix

'''
def make_mastertrof():
    MasterTrof = pd.DataFrame(columns=['Row','Column','Content','Vol','Kpi /MM','Kcl/mM'])
    bufferConditions=assayPlate.loc[:,['Kpi /MM','Kcl/mM']].drop_duplicates()
    count=0
    for i in tqdm(bufferConditions.index):
        temp=pd.DataFrame(columns=['Row','Column','Content','Vol','Kpi /MM','Kcl/mM'])
        temp=temp.append(bufferConditions.loc[i])
        temp['Row']=1 # Maybe this is what you do with trofs?
        temp['Column']=Letters[count]
        temp['Content']='BM3 in Buffer '+Letters[count]
        temp['Vol']=11000
        count+=1
        MasterTrof=MasterTrof.append(temp)
    return MasterTrof

def make_CompoundSourcePlate():
    Output = pd.DataFrame(columns=['Row','Column','Content','Vol','Kpi /MM','Kcl/mM','Ligand','LigandConc'])
    col_IDs = MasterPlate.columns.drop('Unnamed: 0')
    count=0
    for i in tqdm(col_IDs):

        temp=pd.DataFrame(columns=['Row','Column','Content','Vol','Kpi /MM','Kcl/mM','Ligand','LigandConc'])
        Ligand=pd.Series([i]*8,name='Ligand')
        LigandConc=pd.Series(([100.]*8)/np.array([1,2,4,8,16,32,64,128]),name='LigandConc')
        Column=pd.Series([count+1]*8)
        Row=pd.Series([j for j in Letters])
        Vol = MasterPlate.loc[:,i]

        temp['Row']=Row
        temp['Column']=Column
        temp['Ligand']=Ligand
        temp['LigandConc']=LigandConc
        temp['Vol']=Vol
        count+=1
        Output=Output.append(temp)
    Output.reset_index(inplace=True,drop=True)
    return Output

def protein_transfer(assayPlate):
    '''First loop makes the transfers from the
    protein source trof'''
    Output = pd.DataFrame(columns=ExampleSheet.columns)
    for i in tqdm(assayPlate.index):

        row=assayPlate.loc[i,:]
        Volume=25
        SourcePlateBarcode='MasterTrof'
        SourcePlateWell=match_buffers_2_trof(row)
        DestinationPlateBarcode='AssayPlate'
        DestinationPlateWell='A'+str(i+1)
        ComponentName='-'

        #another time I should calculate how much is left in the source plate

        temp=pd.DataFrame([[Volume,SourcePlateBarcode,SourcePlateWell,DestinationPlateBarcode,DestinationPlateWell,ComponentName]],\
        columns=['Volume','SourcePlateBarcode','SourcePlateWell','DestinationPlateBarcode','DestinationPlateWell','ComponentName'])
        Output=Output.append(temp)
    Output.reset_index(drop=True,inplace=True)
    return Output

def match_buffers_2_trof(row):
    #buffer = row.loc[['Kpi /MM','Kcl/mM']]
    mtrof=mastertrof.loc[mastertrof['Kpi /MM']==row['Kpi /MM']]
    mtrof=mtrof.loc[mtrof['Kcl/mM']==row['Kcl/mM']]
    row = mtrof.loc[:,'Row'].item()
    col = mtrof.loc[:,'Column'].item()
    return str(col)+str(row)

def compound_transfer(compound_source):
    '''Assumes multichannel'''
    Output = pd.DataFrame(columns=ExampleSheet.columns)
    for i in tqdm(assayPlate['Substrate']):
        '''source is a dataframe with the plate column we're after'''
        source=compound_source.loc[compound_source.loc[:,'Ligand']==i]
        count=0
        #print(i)
        '''
        for letter in Leters384:
            Volume=25
            SourcePlateBarcode='compound_source'
            SourcePlateWell=str(source.loc[count,'Row']) + str(source.loc[count,'Column'])
            DestinationPlateBarcode='AssayPlate'
            DestinationPlateWell=letter+str(count)
            ComponentName='-'
            count+=1
            temp=pd.DataFrame([[Volume,SourcePlateBarcode,SourcePlateWell,DestinationPlateBarcode,DestinationPlateWell,ComponentName]],\
            columns=['Volume','SourcePlateBarcode','SourcePlateWell','DestinationPlateBarcode','DestinationPlateWell','ComponentName'])
            Output=Output.append(temp)'''
    Output.reset_index(drop=True,inplace=True)
    return Output


mastertrof=make_mastertrof()
compound_source = make_CompoundSourcePlate()
Output_Protein=protein_transfer(assayPlate)
Output_compound=compound_transfer(compound_source)

Output=Output_Protein.append(Output_compound)
print(assayPlate)
