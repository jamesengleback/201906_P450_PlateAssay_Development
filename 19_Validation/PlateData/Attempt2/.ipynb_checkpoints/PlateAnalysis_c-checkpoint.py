import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm

import string
from scipy import ndimage

import torch
import torch.nn as nn


class PlateDataset():
    def __init__(self,plate_data, pathlength_data):
        self.plate_data = plate_data
        self.pathlength_data_path = pathlength_data
        self.data, self.metadata = self.GetPlateData()
        self.smoothingParam = 2
        
        # Pathlength Stuff
        self.pathlengthdata, self.pathlengthmetadata = self.GetPlatePathlengthData(self.pathlength_data_path)
        self.K = 0.158 # buffer absorbance constant
        self.Compound_K = 3
        self.vol = 20 #ul
        self.PercentDMSO = 5
        self.concs = self.CalculateCompoundConcs(self.Compound_K,self.vol,self.PercentDMSO)
        
        self.PathlengthsByWell = self.Pathlength()
        
    def GetPlateData(self):
        '''
        This reads full range UV-Vis trace from a BMG PheraStar Platereader
        as a csv and does a bit or data munging and returns a pandas dataframe
        and the details of the experiment that the machine records, which I'm
        calling 'metadata'
        '''
        metadata = pd.read_csv(self.plate_data, nrows = 3)
        data = pd.read_csv(self.plate_data, skiprows = 6)
        # Rename columns to something more sensible
        data.rename(columns = {'Unnamed: 0':'WellLetter','Unnamed: 1':'WellNumber','Unnamed: 2':'SampleID',}, inplace = True)
        # Cleaning
        data.dropna(inplace = True, how = 'all')
        # Get rid of unused wells
        unused_wells = data['SampleID'].str.contains('unused')
        data = data.loc[unused_wells == False]
        # The well letters and well numbers are seperate, so I'm combining them
        WellIndex = data.loc[:,'WellLetter'].str.cat(data.loc[:,'WellNumber'].astype(str))
        data.index = WellIndex
        data.drop(['WellLetter','WellNumber'],inplace=True,axis =1) # Don't need these anymore
        data = data.loc[:,'220':].dropna(axis = 1) # Numerical data only!
        data.columns = data.columns.astype(int) # useful for indexing and plotting
        # zero at 800 nm
        data.reset_index(drop=True,inplace=True) # otherwise SUBTRACT can't match up cells
        data = data.subtract(data.loc[:,800],axis=0)
        data.index = WellIndex
        return data,metadata

    
    def GetPlatePathlengthData(self,plate_path):
        '''
        PATHLENGTH STUFF
        
        Reads data from a csv of a 900 and 975 nm plate read, used to 
        calculate path length
        '''
        metadata = pd.read_csv(plate_path, nrows = 3)
        data = pd.read_csv(plate_path, skiprows = 5).dropna(axis=1)
        # Rename columns to something more sensible
        data.rename(columns = {'Raw Data (900 1)':900,'Raw Data (975 2)':975}, inplace = True)
        
        # The well letters and well numbers are seperate, so I'm combining them
        WellIndex = data.loc[:,'Well Row'].str.cat(data.loc[:,'Well Col'].astype(str))
        data.index = WellIndex
        data.drop(['Well Row','Well Col','Content'],inplace=True,axis =1) # Don't need these anymore
        data.index = WellIndex
        return data,metadata
        
    def Pathlength(self):
        '''
        K value in this case is a constant assigned to a buffer based on its absorbance at 975 abd 900 nm
        different from the K in the __init__ function, which relates to compound concentrations.
        I'll sort out my naming system at some point.
        '''
        k_value = 0.158 # need to check this in cuvettes
        pathlength = ((self.pathlengthdata[975] - self.pathlengthdata[900])/k_value) * 10 #mm
        return pathlength
        
    def AnalysisPipeline_1(self,Block):
        '''
        Returns tuple of races, difference spec and diff diff
        as pd.Dataframes, given a block
        '''
        testWells, BlankWells = self.GetBlocksWells(Block)
        NormalizedTraces = self.NormalizeBlock(testWells, BlankWells)
        DifferenceSpec = self.DifferenceBlock(NormalizedTraces)
        DiffDiff = self.DiffDiffBlock(DifferenceSpec)
        return  NormalizedTraces, DifferenceSpec, DiffDiff
        
    def AnalysisPipeline_2(self,Block):
        '''
        returns %spin shift instead of diffdiff
        '''
        # requires pathlengths
        testWells, BlankWells = self.GetBlocksWells(Block)
        NormalizedTraces = self.NormalizeBlock(testWells, BlankWells)
        testPathlengths, blankPathLenths = self.PathlengthsByWell.loc[testWells], self.PathlengthsByWell.loc[BlankWells]
        
    def SpinShift(self,NormalizedTraces):
        '''
        Equation and constants taken from "Temperature jump relaxation kinetics of the P-450cam spin equilibrium."
        - I'll have to sort out the constants for BM3 later.
        '''
        E_hs_417 = 60.1
        E_ls_417 = 119.0
        E_hs_391 = 105.3
        E_ls_391 = 47.9
        
        spinShift = (
        
    def GetBlocksWells(self, Block):
        '''
        Returns the test well IDs and blank well IDs. I got some columns the wrong 
        way around so I've got a paramater to switch them around
        '''
        # I got some of the blocks the wrong way around
        ### well allocation from block
        rows = dict((number,letter) for letter,number in zip(string.ascii_uppercase,range(1,17)))
        # if block number is odd
        
        if Block%2!=0:
            blockRows = [rows.get(i) for i in range(1,9)]
            blockCols = (Block,Block+1)
        else:
            blockRows = [rows.get(i) for i in range(9,17)]
            blockCols = (Block-1,Block)
        
        testWells = [i+str(blockCols[0]) for i in blockRows]
        BlankWells = [i+str(blockCols[1]) for i in blockRows]
        return testWells, BlankWells
        
    def NormalizeBlock(self,testWells, BlankWells):
        '''
        Subtracts baseline well trace from each testwell
        and gaussian smooths according to the
        self.smoothing param (kernel size)
        
        Takes into account path length
        '''
        # testWells, BlankWells are well ID number/letters
        testWells=self.GaussianSmoothBlock(self.data.loc[testWells])
        BlankWells=self.GaussianSmoothBlock(self.data.loc[BlankWells])
        
        # to subtract, the well ID index has to be ignored
        return testWells.reset_index(drop=True)-BlankWells.reset_index(drop=True)

    def DifferenceBlock(self,NormalizedBlock):
        NormalizedBlock=NormalizedBlock-NormalizedBlock.iloc[0,:]
        return NormalizedBlock

    def DiffDiffBlock(self,Differenceblock):
        # Checking the column headers are integers
        if type(Differenceblock.columns) != 'pandas.core.indexes.numeric.Int64Index':
            Differenceblock.columns=Differenceblock.columns.astype(int)
        # subtract the peak and trough from one another
        DiffDiff = abs(Differenceblock.loc[:,420] - Differenceblock.loc[:,390])
        return DiffDiff
        
    def GaussianSmoothBlock(self,block):
        output = ndimage.gaussian_filter(block,self.smoothingParam)
        output = pd.DataFrame(output,columns=block.columns,index=block.index)
        return output

    def PlotTrace(self,traces):
        if type(traces.columns) != 'pandas.core.indexes.numeric.Int64Index':
            traces.columns=traces.columns.astype(int)
        fig, ax = plt.subplots(figsize=(10,3))
        ax.set_prop_cycle('color',plt.cm.magma(np.linspace(0,0.9,len(traces))))

        for i in traces.index:
            y = traces.iloc[i,:]
            plt.plot(traces.columns,y, lw = 2, alpha = 0.8)

        #plt.title(title,fontsize = 15)
        
        concs = np.round(self.concs,2)
        plt.legend(concs,loc = 'center right')
        
        plt.xticks(traces.columns[::50])
        plt.xlim((250,800))
        
        #Set axis limits
        axmax = traces.loc[:,390:].max().max()*1.5
        axmin = traces.loc[:,390:].min().min()*1.5
        plt.ylim((axmin,axmax))
        plt.xlabel('Wavlength nm')
        plt.ylabel('Change in Absorbance')
        plt.show()
    
    def PlotMichaelesMenten(self,DiffDiff,concs, km, vmax, loss,title,save=False):
        #K,percentDMSO, Vol = 3, 5, 20
        #concs = self.CalculateCompoundConcs(K,Vol,percentDMSO)
        #km, vmax, loss = self.FitMichaelisMenten(concs,DiffDiff)
        x = np.linspace(concs.min(),concs.max(),100)

        plt.figure(figsize=(5,5))
        plt.scatter(concs,DiffDiff)

        plt.plot(x, (vmax*x)/(km + x))
        plt.title(title)
        plt.xlabel('Concentration uM')
        plt.ylabel('Change in Absorbance')
        plt.text(concs.max()*0.7,vmax*0.2,'Km = '+str(np.around(km,2))+'\n'\
        +'Vmax = '+str(np.around(vmax,2))+'\n'\
        +'Loss = '+str(np.around(loss,5))+'\n'\
        'R squared = ' + str(round(self.r_squared(DiffDiff, concs, vmax,km),2)))

        if save:
            plt.savefig(title.replace(' ','_')+'.png')
            plt.close()
            return title.replace(' ','_')+'.png'
        else:
            plt.show()
    
    def CalculateCompoundConcs(self,K,Vol,percentDMSO):
        # recreates the experimental plan concentrations
        compound_vol = np.linspace(0,1,8)**K
        compound_vol *= Vol # ul
        compound_vol *= percentDMSO/100 # scaled to DMSO percentage
        #compound_vol = 2.5* np.round(compound_vol/2.5) # vol in nl
        compoundConcs = (10_000 * compound_vol)/Vol
        return compoundConcs
            
    def GetCols(self,col):
        selection = (pd.Series(self.data.index).str.extract(r'(\d+)')[0].astype(int) ==col)
        selection.index = self.data.index
        return self.data.loc[selection]
        
    def Noise(self,data):
        S2N = data.loc[:,405].std()
        return S2N

    def FitMichaelisMenten(self,x,y):
        x = torch.tensor(x,dtype=torch.float) # concs are numpy array, 500 is max conc
        y = torch.tensor(y.values,dtype=torch.float) # Diffdiff is pd.series, 500 is max conc
        km = torch.tensor([0.5],requires_grad=True,dtype=torch.float)
        vmax = torch.tensor([0.5],requires_grad=True,dtype=torch.float)
        optimizer = torch.optim.Adam({km,vmax},lr = 1e-2)
        loss_fn =  self.r_squared_torch
        for i in range(5_000):
            y_pred = (vmax*0.05*x)/(km*500 + x) # scaling
            loss = 1 - loss_fn(y,y_pred) # 1 - r squared
            if km <0:
                # making sure that Km isn't negative
                loss -= km.item()
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
        return (km*500).item(), (vmax*0.05).item(), loss.item()

    def r_squared(self, DiffDiff, concs, vmax,km):
        residuals = DiffDiff - (vmax*concs)/(km + concs) #curve(concs, vmax, km)
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((DiffDiff-np.mean(DiffDiff))**2)
        r_squared = 1 - (ss_res / ss_tot)
        return r_squared
        
    def r_squared_torch(self,y,yh):
        residuals = y-yh
        ss_res = (residuals**2).sum()
        ss_tot = ((y-y.mean())**2).sum()
        r_squared = 1 - (ss_res / ss_tot)
        return r_squared
    

def main():

	pass
if __name__ =='__main__':
    main()
