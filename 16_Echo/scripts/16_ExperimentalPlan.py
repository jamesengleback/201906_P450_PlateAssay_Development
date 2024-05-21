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
    def __init__(self, WorkingVol, K, Percent_DMSO, Compound):
        self.WorkingVol = WorkingVol *1000 # convert to nl
        self.K = K
        self.Percent_DMSO = Percent_DMSO/100 # as a fraction of 1
        self.Compound = Compound
        self.Transfer = self.MakeTransfer()

    def MakeTransfer(self):
        compound_vol, DMSO = self.MakeCompound_Vols()
        output = pd.DataFrame([], columns = ['SrcID','DestID','Volume'])

        for i,(j, k) in enumerate(zip(compound_vol, DMSO)):
            temp = pd.DataFrame([[self.Compound, 'A'+str(i), j], #Compound to target well
                                ['DMSO','A'+str(i), k], # DMSO to target well
                                [self.Compound, 'B'+str(i), j], # Compound to blank well
                                ['DMSO','B'+str(i), k]] , # DMSO to blank Well
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
        TestWells = {'A' + str(i):j for i,j in zip(range(9),TestWellsx8)}
        BlankWells = {'B' + str(i):j for i,j in zip(range(9),BlankWellsx8)}
        self.Transfer['DestID'] = self.Transfer['DestID'].replace(TestWells)
        self.Transfer['DestID'] = self.Transfer['DestID'].replace(BlankWells)
        return self.Transfer

    def Dispense(self, compound, dmso):
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


def main():
    plan = pd.read_csv('../data/D_Opt.csv')

    DMSO = Compound('DMSO',['E'+str(i) for i in range(1,19)])
    ArachadionicAcid = Compound('Arachadionic acid',['F'+str(i) for i in range(1,13)])

    blocks = {}

    for i in range(1,25):
        testwells = [j+str(i) for j in list(string.ascii_uppercase)[0:8]]
        blankwells = [j+str(i) for j in list(string.ascii_uppercase)[8:16]]
        blocks[i] = [testwells,blankwells]

    o = {i:{'test_wells':blocks[i][0], 'control_wells':blocks[i][1]} for i in blocks}
    with open('wells.json', 'w') as f:
        json.dump(o, f)

    import ipdb ; ipdb.set_trace()

    transferMap = pd.DataFrame([], columns = ['SrcID','DestID','Volume'])
    for i,j in zip(plan.index, blocks):
        Condition = plan.loc[i,:]
        block = Block(Condition['Working Vol'], Condition['K-Value'], Condition['% DMSO'], 'Arachadionic acid' )
        block.MapWells(blocks[j][0],blocks[j][1])
        DispensingPattern = block.Dispense(ArachadionicAcid,DMSO)
        transferMap = transferMap.append(DispensingPattern)


    transferMap.reset_index(inplace=True, drop=True)
    transferMap = transferMap.loc[transferMap['Volume'] != 0]
    transferMap.to_csv('Echo16Transfermap.csv')
    transferMap['SrcID'] = transferMap['SrcID'].apply(WellIDtoNumber)
    transferMap['DestID'] = transferMap['DestID'].apply(WellIDtoNumber)
    Generate(transferMap, 'Echo16TransferMap_rep3.xml')
    print(transferMap)

if __name__ == '__main__':
	main()
