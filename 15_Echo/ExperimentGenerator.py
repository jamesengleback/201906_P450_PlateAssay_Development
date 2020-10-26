import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import string

from EchoXMLGenerator import Generate, WellIDtoNumber

def MakeConcentrations(k):
    # k is between 1 and 4, returns uM
    x=(np.linspace(0,1,8)**k)*200
    return x

def VolToAdd(c1,c2,v2):
    return (c2*v2)/c1

def Dispense(Column,concs,sourceWell):
    '''
    This one dispenses so that 1 column is one compound

    '''
    # columns are numbers, rows are letters
    df = pd.DataFrame([],columns=['SrcID','DestID', 'Volume'])
    rows = dict((number,letter) for letter,number in zip(string.ascii_uppercase,range(1,17)))
    sourceWell=WellIDtoNumber(sourceWell)

    for i,j,k in zip(concs,np.arange(1,17,2),np.arange(2,17,2)):
        dest_1 = WellIDtoNumber(rows[j] + str(Column))
        dest_2 = WellIDtoNumber(rows[k] + str(Column))



        vol=VolToAdd(10_000,i,20_000) #c1 is 10mM, v2 is 20_000 nl
        vol = 2.5*round(vol/2.5) # rounds to nearest 2.5

        temp=pd.DataFrame([[sourceWell,dest_1,vol],[sourceWell,dest_2,vol]],columns=['SrcID','DestID', 'Volume'])
        df=df.append(temp)
    return df.reset_index(drop=True)

def Dispense_2(Block,concs,sourceWell):
    ### well allocation from block
    rows = dict((number,letter) for letter,number in zip(string.ascii_uppercase,range(1,17)))
    # if block number is odd
    if Block%2!=0:
        blockRows = [rows.get(i) for i in range(1,9)]
        blockCols = (Block,Block+1)
    else:
        blockRows = [rows.get(i) for i in range(9,17)]
        blockCols = (Block-1,Block)

    df = pd.DataFrame([],columns=['SrcID','DestID', 'Volume'])
    sourceWell=WellIDtoNumber(sourceWell)

    for i,j in zip(concs,blockRows):
        dest_1 = WellIDtoNumber(j + str(blockCols[0]))
        dest_2 = WellIDtoNumber(j + str(blockCols[1]))

        vol=VolToAdd(10_000,i,50_000) #c1 is 10mM, v2 is 50_000 nl
        vol = 2.5*round(vol/2.5) # rounds to nearest 2.5

        temp=pd.DataFrame([[sourceWell,dest_1,vol],[sourceWell,dest_2,vol]],columns=['SrcID','DestID', 'Volume'])
        df=df.append(temp)
    return df.reset_index(drop=True)


def PP384_Dispense():
    sourcewells = ['A3']*4 + ['B3']*4 + ['C3']*4 + ['D3']*4 + ['E3']*4 + ['F3']*4

    blocks = np.arange(1,25)
    k_values = np.linspace(1,2,4).tolist()*6

    for i,j,k in zip(blocks,k_values,sourcewells):
        df=df.append(Dispense_2(i,MakeConcentrations(j),k))

    df.reset_index(inplace=True,drop=True)
    print(df)
    print(df.loc[df['SrcID']==3]['Volume'].sum())
    df.to_csv('Echoxml_dataframe.csv')
    Generate(df,'echo_r3.xml')

def main():
    df = pd.DataFrame([],columns=['SrcID','DestID', 'Volume'])
    info = pd.DataFrame([],columns=['blocks','k_values','sourcewells'])
    blocks = np.arange(1,25)
    k_values = np.linspace(1,2,4).tolist()*6

    #make source wells
    sourcewells = []
    compounds = {'A1':'DMSO','A2':'DMSO','A3':'DMSO','A4':'DMSO',
    'B1':'Arachadionic acid','B2':'Arachadionic acid','B3':'Arachadionic acid','B4':'Arachadionic acid',
    'C1':'Lauric acid','C2':'Lauric acid','C3':'Lauric acid','C4':'Lauric acid',
    'D1':'Palmitic acid','D2':'Palmitic acid','D3':'Palmitic acid','D4':'Palmitic acid',
    'E1':'SDS','E2':'SDS','E3':'SDS','E4':'SDS',
    'F1':'4-Phenylimidazole','F2':'4-Phenylimidazole','F3':'4-Phenylimidazole','F4':'4-Phenylimidazole',}

    for i in ['A','B','C','D','E','F']:
         for j in range(1,5):
             sourcewells.append(i+str(j))

    for i,j,k in zip(blocks,k_values,sourcewells):
        df=df.append(Dispense_2(i,MakeConcentrations(j),k))
        # repeat block, kvalue and sourcewell 16 times (for the whole block)
        # for concatenation later
        info=info.append(pd.DataFrame([[i,j,k]]*16,columns=['blocks','k_values','sourcewells']))
    df.reset_index(inplace=True,drop=True)
    info.reset_index(inplace=True,drop=True)
    info['Compound'] = pd.Series([compounds[i] for i in info['sourcewells']])

    # Checks that no source well has more than 8ul taken
    '''
    for i in df['SrcID'].unique():
        temp = df.loc[df['SrcID']==i]
        v = temp['Volume'].sum()
        print(v)'''
    df=pd.concat([df,info],axis=1)
    df['Concentration'] = (df['Volume']*10_000)/20_000 # (v1*c1)/v2
    print(df)
    df.to_csv('echo_lowDV.csv')
    Generate(df[['SrcID','DestID', 'Volume']],'echo_lowDV.xml')



if __name__ == '__main__':
    main()
