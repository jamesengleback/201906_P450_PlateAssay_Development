import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import string



class SourcePlateCompound():
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
    def __init__(self, WorkingVol, ProteinConc, Compound,Additive):
        self.WorkingVol = WorkingVol *1000 # convert to nl
        self.ProteinConc = ProteinConc
        self.K = 3 # prevents duplicates of zero values
        self.Percent_DMSO = 0.05 # as a fraction of 1
        self.Compound = Compound
        self.Additive = Additive
        self.Transfers = self.MakeCompound_Vols()

    def MakeCompound_Vols(self):
        compound_vol = np.linspace(0,1,8)**self.K
        compound_vol *= self.Percent_DMSO
        compound_vol *= self.WorkingVol
        compound_vol = 2.5* np.round(compound_vol/2.5)
        TotalDMSOVol = np.round((self.Percent_DMSO * self.WorkingVol)/2.5) *2.5
        DMSO = TotalDMSOVol - compound_vol
        
        return {self.Compound:[i for i in compound_vol], 'DMSO':[i for i in DMSO]} # return dict
        
    '''
    def MakeTransfer(self):
        compound_vol, DMSO = self.MakeCompound_Vols()
        output = pd.DataFrame([], columns = ['SrcID','DestID','Volume'])

        for i,(j, k) in enumerate(zip(compound_vol, DMSO)):
            temp = pd.DataFrame([[self.Compound, 'X'+str(i+1), j], #Compound to target well
                                ['DMSO','X'+str(i+1), k], # DMSO to target well
                                [self.Compound, 'Y'+str(i+1), j], # Compound to blank well
                                ['DMSO','Y'+str(i+1), k]] , # DMSO to blank Well
                                columns = ['SrcID','DestID','Volume'])
            output=output.append(temp)
        output.reset_index(inplace=True,drop=True)

        return output

    

    def MapWells(self,TestWellsx8, BlankWellsx8):
        TestWells = {'A' + str(i):j for i,j in zip(range(1,9),TestWellsx8)}
        BlankWells = {'B' + str(i):j for i,j in zip(range(1,9),BlankWellsx8)}
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
        return output.reset_index(drop=True)'''


class AssayPlate():
    def __init__(self):
        self.blocks = {}
        self.Allocations = {} # IDs map to blocks
        self.TransferPlan = pd.DataFrame([],columns = ['SrcID','DestID','Volume'])
        
    def AddBlocks(self,block):
        count = len(self.blocks)+1
        self.blocks[count] = block
    
    def BlockProperties(self):
        # Returns dataframe of formulation properties
        # of each block
        
        df = pd.DataFrame([],columns = ['ID','Additive','Vol','Conc'])

        for i in self.blocks:
            BlockVol = self.blocks[i].WorkingVol
            BlockConc = self.blocks[i].ProteinConc
            BlockAdditive = self.blocks[i].Additive
            df = df.append(pd.DataFrame([[i,BlockAdditive,BlockVol,BlockConc]],columns = ['ID','Additive','Vol','Conc']))
        df =  df.reset_index(drop=True)
        df = df.sort_values(['Additive','Vol','Conc'])
        return df

    def AllocateBlocks(self):
        blockProperties = self.BlockProperties()
        
        count = 1
        for i in blockProperties.index:
            row = blockProperties.loc[i,:].to_dict()
            if not bool(self.Allocations): # if allocation dictionary is empty
                row['Block Allocation'] = count

                self.Allocations[count] = row
                count +=1
                # end of that
            
            else: # for everything else
                if count %2 ==1: # if odd
                    # then add the block
                    row['Block Allocation'] = count
                    self.Allocations[count] = row
                    count += 1
                else: # if even
                    previousAllocation = self.Allocations[count-1]

                    if row['Additive'] == previousAllocation['Additive']\
                    and row['Vol'] == previousAllocation['Vol']\
                    and row['Conc'] == previousAllocation['Conc']:
                    ### ^ checks if this block matches the previous one
                        row['Block Allocation'] = count
                        self.Allocations[count] = row # then add
                        count +=1
                    else:
                        count +=1 # or count up
                    row['Block Allocation'] = count
                    self.Allocations[count] = row # then add
                    count +=1
            
    def MakeTransfer(self):
        
        for i in self.blocks:
          
            block = self.blocks[i]
            compound_vols, DMSO_vols = block.Transfers[block.Compound], block.Transfers['DMSO']
            TestWells,BlankWells = self.BlockNumberToWells(i)
            
      
            
            for cpd_vol, dmso_vol, testwell,blankwell in zip(compound_vols, DMSO_vols, TestWells,BlankWells):
                temp = pd.DataFrame([[block.Compound, testwell, cpd_vol], #Compound to target well
                                ['DMSO',testwell, dmso_vol], # DMSO to target well
                                [block.Compound, blankwell, cpd_vol], # Compound to blank well
                                ['DMSO',blankwell, dmso_vol]] , # DMSO to blank Well
                                columns = ['SrcID','DestID','Volume'])
                                
                self.TransferPlan=self.TransferPlan.append(temp)
        self.TransferPlan.reset_index(inplace=True,drop=True)
        
        '''
        self.AllocateBlocks() # give blocks the right ID numbers      
       
        for i in self.Allocations:
            originalID = self.Allocations[i]['ID']
            blockAllocation = self.Allocations[i]['Block Allocation']
            block = self.blocks[originalID]
            compound_vols, DMSO_vols = block.Transfers[block.Compound], block.Transfers['DMSO']
            TestWells,BlankWells = self.BlockNumberToWells(blockAllocation)
            
      
            
            for cpd_vol, dmso_vol, testwell,blankwell in zip(compound_vols, DMSO_vols, TestWells,BlankWells):
                temp = pd.DataFrame([[block.Compound, testwell, cpd_vol], #Compound to target well
                                ['DMSO',blankwell, dmso_vol], # DMSO to target well
                                [block.Compound, testwell, cpd_vol], # Compound to blank well
                                ['DMSO',blankwell, dmso_vol]] , # DMSO to blank Well
                                columns = ['SrcID','DestID','Volume'])
                                
                self.TransferPlan=self.TransferPlan.append(temp)
            self.TransferPlan.reset_index(inplace=True,drop=True)'''

    def BlockNumberToWells(self, BlockNumber):
        alphabet = string.ascii_uppercase
        # if odd
        if BlockNumber%2 == 1: 
            TestWells = [i+str(BlockNumber) for i in list(alphabet)[0:8]]
            BlankWells = [i+str(BlockNumber+1) for i in list(alphabet)[0:8]]
        else:
            TestWells = [i+str(BlockNumber-1) for i in list(alphabet)[8:16]]
            BlankWells = [i+str(BlockNumber) for i in list(alphabet)[8:16]]
        return TestWells,BlankWells
            
