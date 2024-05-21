import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import string

from tqdm import tqdm

from EchoXMLGenerator import Generate, WellIDtoNumber

class Compound():
    def __init__(self,coumpound_name,wells):
        self.compound = coumpound_name
        self.MaxWellVol = 12 * 1000 #nl
        self.MinWellVol = 2.5 * 1000 #nl + safety

        self.wells = self.FillWells(wells)

    def FillWells(self,wells):
        output = {}
        for i in wells:
            output[i] = self.MaxWellVol #ul
        return output

    def AvailableVolume(self):
        return sum(self.wells.values())

    def Sample(self,vol):
        if vol %2.5 !=0:
            'Transfer vol not a multiple of 2.5'
        sample = {}
        for well in self.wells:
            if self.wells[well] > self.MinWellVol:
                if vol < self.wells[well]:
                    self.wells[well] -= vol
                    sample[well] = vol
                    vol -=vol
                    break
                else:
                    sampleVol = self.wells[well]-self.MinWellVol
                    sample[well] = sampleVol
                    self.wells[well] -= sampleVol
                    vol -= sampleVol
        if vol !=0:
            print('Vol not reached')
        return sample

class Block():
    def __init__(self, WorkingVol, Compound):
        '''
        This class is a bit tangled, next steps to improve
        would be to make it less complicated
        '''
        self.WorkingVol = WorkingVol *1000 # convert to nl
        self.K = 4
        self.Percent_DMSO = 5/100 # as a fraction of 1
        self.Compound = Compound
        self.Transfer = self.MakeTransfer()

    def MakeTransfer(self):
        '''
        Calls self.MakeCompound_Vols()
        
        Makes a temporary output with destination wells,
        volumes but not source wells. The source wells are allocated later 
        in self.Dispense()
        '''
        compound_vol, DMSO = self.MakeCompound_Vols()
        output = pd.DataFrame([], columns = ['SrcID','DestID','Volume'])

        for i,(j, k) in enumerate(zip(compound_vol, DMSO)):
            temp = pd.DataFrame([[self.Compound, 'X'+str(i), j], #Compound to target well
                                ['DMSO','X'+str(i), k], # DMSO to target well
                                [self.Compound, 'Y'+str(i), j], # Compound to blank well
                                ['DMSO','Y'+str(i), k]] , # DMSO to blank Well
                                columns = ['SrcID','DestID','Volume'])
            output=output.append(temp)
        output.reset_index(inplace=True,drop=True)

        return output

    def MakeCompound_Vols(self):
        compound_vol = np.linspace(0,1,8)**self.K
        compound_vol *= self.Percent_DMSO
        compound_vol *= self.WorkingVol
        compound_vol = 2.5* np.round(compound_vol/2.5)
        TotalDMSOVol = np.round((self.Percent_DMSO * self.WorkingVol)/2.5) *2.5
        DMSO = TotalDMSOVol - compound_vol
        return compound_vol, DMSO

    def MapWells(self,TestWellsx8, BlankWellsx8):
        TestWells = {'X' + str(i):j for i,j in zip(range(9),TestWellsx8)}
        BlankWells = {'Y' + str(i):j for i,j in zip(range(9),BlankWellsx8)}
        self.Transfer['DestID'] = self.Transfer['DestID'].replace(TestWells)
        self.Transfer['DestID'] = self.Transfer['DestID'].replace(BlankWells)
        return self.Transfer

    def Dispense(self, compound, dmso):
        '''
        Takes the partially completed transfer list
        and external source compound objects. Sometimes
        transfers take multiple wells so they're looped through.
        '''
        output = pd.DataFrame([], columns = ['SrcID','DestID','Volume'])
        for i in self.Transfer.index:
            row = self.Transfer.loc[i,:]
            source = row['SrcID']

            if source == compound.compound:
                # returns dictionary of transfers
                transfers = compound.Sample(row['Volume'])
                for j in transfers:
                    temp = pd.DataFrame([[j,row['DestID'],transfers[j]]], columns = ['SrcID','DestID','Volume'])
                    output = output.append(temp)

            if source == dmso.compound:
                # returns dictionary of transfers
                transfers = dmso.Sample(row['Volume'])
                for j in transfers:
                    temp = pd.DataFrame([[j,row['DestID'],transfers[j]]], columns = ['SrcID','DestID','Volume'])
                    output = output.append(temp)
        return output.reset_index(drop=True)



def main(arg):

    DMSO = Compound('DMSO',['J'+str(i) for i in range(1,25)]+['K'+str(i) for i in range(1,25)])
    ArachadionicAcid = Compound('Arachadionic acid',['L'+str(i) for i in range(1,25)])
    
    blocks = {}
    
    plan = pd.read_csv(arg, index_col=0)
    # duplicate plan blocks
    plan=plan.append(plan).loc[range(10)]
    plan.reset_index(drop=True, inplace=True)

    for i in range(1,21):
        if i%2==1:
            testwells = [j+str(i) for j in list(string.ascii_uppercase)[0:8]]
            blankwells = [j+str(i+1) for j in list(string.ascii_uppercase)[0:8]]
        else:
            testwells = [j+str(i-1) for j in list(string.ascii_uppercase)[8:16]]
            blankwells = [j+str(i) for j in list(string.ascii_uppercase)[8:16]]
        blocks[i] = {'test_wells': testwells, 
                     'blank_wells':blankwells,
                     **plan.iloc[i - 1, :].to_dict()
                     }
    
    json.dump(blocks, sys.stdout)
    # transferMap = pd.DataFrame([], columns = ['SrcID','DestID','Volume'])
    # 
    # 
    # for i,j in tqdm(zip(blocks,plan['Protein Vol'])):
    #     Current_block = Block(j,'Arachadionic acid' )
    #     Current_block.MapWells(blocks[i][0],blocks[i][1])
    #     DispensingPattern = Current_block.Dispense(ArachadionicAcid,DMSO)
    #     transferMap = transferMap.append(DispensingPattern)
    # 

    # transferMap.reset_index(inplace=True, drop=True)
    # transferMap = transferMap.loc[transferMap['Volume'] != 0]
    # #transferMap.to_csv('Echo16Transfermap_BSA_2.csv')
    # transferMap['SrcID'] = transferMap['SrcID'].apply(WellIDtoNumber)
    # transferMap['DestID'] = transferMap['DestID'].apply(WellIDtoNumber)
    # #Generate(transferMap, 'Echo18TransferMap_BSA_rep2.xml')
    # print(transferMap)
    
    
if __name__ == '__main__':
	main(sys.argv[1])
