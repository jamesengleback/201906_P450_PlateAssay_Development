import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import string

from EchoXMLGenerator import Generate, WellIDtoNumber


def MakeCompound_Vols(fracDMSO):
    compound = np.linspace(0,1,8) * fracDMSO * 20_000 # 20ul
    compound = 2.5*np.round(compound/2.5)
    DMSO = (fracDMSO * 20_000) - compound
    return compound, DMSO

def CalcConc(c1,v1,v2):
    return (v1*c1)/v2

def Dispense(Block,cpd_vols, DMSO_vols,CPDsourceWell, DMSOsourceWell,frac_DMSO):
    rows = dict((number,letter) for letter,number in zip(string.ascii_uppercase,range(1,17)))
    if Block%2!=0:
        blockRows = [rows.get(i) for i in range(1,9)]
        blockCols = (Block,Block+1)
    else:
        blockRows = [rows.get(i) for i in range(9,17)]
        blockCols = (Block-1,Block)
    df = pd.DataFrame([],columns=['SrcID','DestID', 'Volume','Block','Source Well','Destination Well','Concentration','DMSO Fraction'])


    for i,j,k in zip(cpd_vols,DMSO_vols,blockRows):
        dest_1 = WellIDtoNumber(k + str(blockCols[0]))
        dest_2 = WellIDtoNumber(k + str(blockCols[1]))

        temp=pd.DataFrame([[WellIDtoNumber(CPDsourceWell),dest_1,i,Block,CPDsourceWell,k + str(blockCols[0]), CalcConc(10_000,i,20_000+i),frac_DMSO],
                            [WellIDtoNumber(CPDsourceWell),dest_2,i,Block,CPDsourceWell,k + str(blockCols[0]),CalcConc(10_000,i,20_000+i),frac_DMSO],
                            [WellIDtoNumber(DMSOsourceWell),dest_1,j,Block,DMSOsourceWell,k + str(blockCols[1]),0,frac_DMSO],
                            [WellIDtoNumber(DMSOsourceWell),dest_2,j,Block,DMSOsourceWell,k + str(blockCols[1]),0,frac_DMSO]],
                            columns=['SrcID','DestID', 'Volume','Block','Source Well','Destination Well','Concentration','DMSO Fraction'])
        df=df.append(temp)
    return df.reset_index(drop=True)

def calcConcsodDF(df):
    for i in df['DestID'].unique():
        well = df.loc[df['DestID'] ==i]

def main():
    Block_DMSO_Concs = {1:0.01,2:0.01,3:0.01,
                   4:0.02, 5:0.02,6:0.02,
                   7:0.03,8:0.03,9:0.03,
                   10:0.04,11:0.04,12:0.04}

    DMSO_Wells = ['A1']*3 + ['A2']*3 + ['A3']*3 + ['A4']*3
    ArachadionicAcid_Wells = ['B1']*3 + ['B2']*3 + ['B3']*3 + ['B4']*3

    output=pd.DataFrame([],columns=['SrcID','DestID','Volume','Block','Source Well','Destination Well','Concentration','DMSO Fraction'])

    for block, CPDsourceWell, DMSOsourceWell in zip(range(1,13),DMSO_Wells, ArachadionicAcid_Wells):
        CPD_vol, DMSO_Vol = MakeCompound_Vols(Block_DMSO_Concs[block])
        output=output.append(Dispense(block, CPD_vol, DMSO_Vol, CPDsourceWell,DMSOsourceWell,Block_DMSO_Concs[block]))

    output.reset_index(drop=True,inplace=True)
    output.to_csv('20191026_DMSO_Concs.csv')
    print('Max volumes per source:',[output.loc[output['SrcID']==i]['Volume'].sum() for i in output['SrcID'].unique()])
    print(output)
    #Generate(output[['SrcID','DestID','Volume']], '20191026_DMSO_Concs.xml')

if __name__ == '__main__':
    main()
