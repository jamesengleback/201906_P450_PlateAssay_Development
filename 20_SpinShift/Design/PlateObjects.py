import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import string



class SourcePlateCompound():
    def __init__(self,coumpound_name,wells,ldv = True):
        self.compound = coumpound_name
        self.ldv = ldv
        if self.ldv:
            self.MaxWellVol = 12 * 1000 #nl
            self.MinWellVol = 2.5 * 1000 #nl + safety
        else:
            self.MaxWellVol = 65 * 1000 #nl
            self.MinWellVol = 15 * 1000 #nl + safety
        self.wells = self.FillWells(wells)

    def FillWells(self,wells,):
        output = {}
        
        if self.ldv:
            for i in wells:
                output[i] = 11 * 1000 #self.MaxWellVol #ul
        else:
            for i in wells:
                output[i] = 60 * 1000
        return output

    def AvailableVolume(self):
        return sum(self.wells.values())

    def Sample(self,vol):
        if vol %2.5 !=0:
            print('Transfer vol not a multiple of 2.5')
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
            print('{}: \tVol not reached'.format(self.compound))
        return sample

class Block():
    def __init__(self, Compound,DMSO, WorkingVol):
        self.WorkingVol = WorkingVol *1000 # convert to nl
        self.ProteinConc = 10 #ish
        self.K = 3 # prevents duplicates of zero values
        self.Percent_DMSO = 0.05 # as a fraction of 1
        self.Compound = Compound
        self.DMSO = DMSO
        self.TestWells = ['X'+str(i) for i in range(1,9)]
        self.BlankWells = ['Y'+str(i) for i in range(1,9)]
        
        self.Transfers = self.MakeTransfer()
        
        
    def MakeTransfer(self):
        compound_vol = np.linspace(0,1,8)**self.K
        compound_vol *= self.Percent_DMSO
        compound_vol *= self.WorkingVol
        compound_vol = 2.5* np.round(compound_vol/2.5)
        TotalDMSOVol = np.round((self.Percent_DMSO * self.WorkingVol)/2.5) *2.5
        DMSO = TotalDMSOVol - compound_vol

        vols = {self.Compound:[i for i in compound_vol], self.DMSO:[i for i in DMSO]} # return dict
        
        output = pd.DataFrame([],columns = ['SrcWell','Destination Well','Volume'])
        for vol_cpd, vol_dmso ,testwell, blankwell in zip(vols[self.Compound], vols[self.DMSO],self.TestWells, self.BlankWells):
            cpd_transfer = self.Compound.Sample(vol_cpd)
            dmso_transfer = self.DMSO.Sample(vol_dmso)
            for i,j in zip(cpd_transfer, dmso_transfer):
                print(i,j)
                temp = pd.DataFrame(\
                [[i,testwell,cpd_transfer[i]],\
                [j,testwell,dmso_transfer[j]],\
                [i,blankwell,cpd_transfer[i]],\
                [j,blankwell,dmso_transfer[j]]]\
                ,columns = ['SrcWell','Destination Well','Volume'])
                output = output.append(temp)
        return output.reset_index(drop=True)
            
class AssayPlate():
    def __init__(self):
        self.blocks = {}
        self.Allocations = {} # IDs map to blocks
        self.TransferPlan = pd.DataFrame([],columns = ['SrcWell','Destination Well','Volume'])
        
    def AddBlocks(self,block):
        count = len(self.blocks)+1
        self.blocks[count] = block

    def MapWells(self):
        # Gets the block from the number and replaces the
        # place holder destingation well IDs with actual well numbers
        TransferPlan = pd.DataFrame([],columns = ['SrcWell','Destination Well','Volume'])
        alphabet = string.ascii_uppercase
        for BlockNumber in self.blocks:
            # if odd
            if BlockNumber%2 == 1: 
                TestWells = [i+str(BlockNumber) for i in list(alphabet)[0:8]]
                BlankWells = [i+str(BlockNumber+1) for i in list(alphabet)[0:8]]
            else:
                TestWells = [i+str(BlockNumber-1) for i in list(alphabet)[8:16]]
                BlankWells = [i+str(BlockNumber) for i in list(alphabet)[8:16]]
                

            mappings = dict(zip(['X'+str(i) for i in range(1,9)]+['Y'+str(i) for i in range(1,9)],\
            TestWells + BlankWells))
            transfers = self.blocks[BlockNumber].Transfers
            transfers['Destination Well'] = transfers['Destination Well'].replace(mappings)
            self.TransferPlan = self.TransferPlan.append(transfers)
            self.TransferPlan.reset_index(inplace=True,drop=True)
    
    
   
def test_1():
    aracadonic = SourcePlateCompound('Arachadonic acid',['A'+str(i) for i in range(1,8)],ldv=False)
    DMSO = SourcePlateCompound('DMSO',['B'+str(i) for i in range(1,15)],ldv=False)
    assayplate = AssayPlate()
    for vol in [20,30,40]:
        for repeat in range(8):
            block = Block(aracadonic,DMSO,vol)
            assayplate.AddBlocks(block)
    assayplate.MapWells()
    transferMap = assayplate.TransferPlan
    transferMap = transferMap.loc[transferMap['Volume']>0]
    
    for i in transferMap['Destination Well'].unique():
        print(i, len(transferMap.loc[transferMap['Destination Well'] == i]))

def test_2():
    aracadonic = SourcePlateCompound('Arachadonic acid',['A'+str(i) for i in range(1,8)],ldv=False)
    DMSO = SourcePlateCompound('DMSO',['B'+str(i) for i in range(1,15)],ldv=False)
    assayplate = AssayPlate()
    block = Block(aracadonic,DMSO, WorkingVol = 20)
    assayplate.AddBlocks(block)
    assayplate.MapWells()
    
if __name__ == '__main__':
    test_2()

