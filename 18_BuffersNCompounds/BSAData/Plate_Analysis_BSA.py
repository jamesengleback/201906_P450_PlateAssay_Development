import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm

import string
from scipy import ndimage

import torch
import torch.nn as nn

from sklearn.metrics import r2_score

class PlateDataset():
    def __init__(self,plate_data):
        self.plate_data = plate_data
        self.data, self.metadata = self.GetPlateData()
        self.smoothingParam = 0.5
        self.SignaltoNoiseData = self.SignalToNoise()
    
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

    def AnalysisPipeline_1(self,Block,WrongWay=False):
        testWells, BlankWells = self.GetBlocksWells(Block,WrongWay)
        NormalizedTraces = self.NormalizeBlock(testWells, BlankWells)
        DifferenceSpec = self.DifferenceBlock(NormalizedTraces)
        DiffDiff = self.DiffDiffBlock(DifferenceSpec)
        return  NormalizedTraces, DifferenceSpec, DiffDiff
        
    def GetBlocksWells(self, Block,WrongWay = False):
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
        
        if WrongWay:
            testWells = [i+str(blockCols[1]) for i in blockRows]
            BlankWells = [i+str(blockCols[0]) for i in blockRows]
        else:
            # Assuming that test column is the leftmost
            testWells = [i+str(blockCols[0]) for i in blockRows]
            BlankWells = [i+str(blockCols[1]) for i in blockRows]
        return testWells, BlankWells
        
    def NormalizeBlock(self,testWells, BlankWells):
        # testWells, BlankWells are well ID number/letters
        testWells=self.GaussianSmoothBlock(self.data.loc[testWells].reset_index(drop=True))
        BlankWells=self.GaussianSmoothBlock(self.data.loc[BlankWells].reset_index(drop=True))
        return testWells-BlankWells

    def DifferenceBlock(self,NormalizedBlock):
        NormalizedBlock.columns=NormalizedBlock.columns.astype(int)
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
        '''
        output = pd.DataFrame([],columns=block.columns)
        for i in block.index:
            # Locates column, smooths it and returns it to the dataframe
            i = block.loc[i,:]
            i=ndimage.gaussian_filter(i,self.smoothingParam)
            temp = pd.DataFrame([i],columns=block.columns)
            output = output.append(temp)'''
        output = ndimage.gaussian_filter(block,self.smoothingParam)
        output = pd.DataFrame(output,columns=block.columns,index=block.index)
        return output


    def PlotTrace(self,traces,vol = None,colors=False):
        '''
        # Cols has to be an iterable
        # Checking the column headers are integers
        rows = list(string.ascii_uppercase[0:16])
		
        traceIDs = []
        for i in cols:
            for j in rows:
                traceIDs.append(j+str(i))
        traces = self.data.loc[traceIDs,:]
		'''
            
        if type(traces.columns) != 'pandas.core.indexes.numeric.Int64Index':
            traces.columns=traces.columns.astype(int)
            
        traces = self.GaussianSmoothBlock(traces)
        #Set axis limits
        axmax = traces.loc[:,390:].max().max()*1.5
        axmin = traces.loc[:,390:].min().min()*1.5

        # Define figure + set the colorcyle to a continuous color map
        fig, ax = plt.subplots(figsize=(10,3))
        ax.set_prop_cycle('color',plt.cm.magma(np.linspace(0,0.9,len(traces))))

        #Plot each trace idividually
        
        if colors:

            for i,j in zip(range(len(traces)),traceIDs):
                y = traces.iloc[i,:]
                S2N = self.SignaltoNoiseData[j]
                plt.plot(traces.columns,y, lw = 2, alpha = 0.8,c = cm.magma(S2N))

        else:
            for i in range(len(traces)):
                y = traces.iloc[i,:]
                plt.plot(traces.columns,y, lw = 2, alpha = 0.8)

        #plt.title(title,fontsize = 15)
        
        if vol != None:
            K,percentDMSO = 4, 5
            concs = self.CalculateCompoundConcs(K,vol,percentDMSO)
            concs = np.round(concs,2)
            plt.legend(concs,loc = 'center right')
            
        plt.xticks(traces.columns[::50])
        plt.xlim((350,800))
        plt.ylim((axmin,axmax))
        plt.xlabel('Wavlength nm')
        plt.ylabel('Change in Absorbance')
        plt.show()
    
    def PlotMichaelesMenten(self,DiffDiff,Vol,title,save=False):
        K,percentDMSO = 4, 5
        concs = self.CalculateCompoundConcs(K,Vol,percentDMSO)
        km, vmax, loss = self.FitMichaelisMenten(concs,DiffDiff)
        km, vmax, loss  = km.item(), vmax.item(), loss.item()
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
        return  km, vmax, loss
    
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
        
    def SignalToNoise(self):
        S2N = self.data.loc[:,420] - self.data.loc[:,390]
        S2N -= S2N.min()
        S2N /= np.ptp(S2N)
        return S2N

    def FitMichaelisMenten(self,x,y):
        x = torch.tensor(x,dtype=torch.float) # concs are numpy array, 500 is max conc
        y = torch.tensor(y.values,dtype=torch.float) # Diffdiff is pd.series, 500 is max conc
        km = torch.tensor([0.5],requires_grad=True,dtype=torch.float)
        vmax = torch.tensor([0.5],requires_grad=True,dtype=torch.float)
        optimizer = torch.optim.Adam({km,vmax},lr = 1e-2)
        loss_fn =  self.r_squared_torch
        for i in range(1_000):
            y_pred = (vmax*x)/(km*500 + x)
            loss = loss_fn(y,y_pred) # true r squared
            loss = 1- loss # so that 
            
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
        return km*500, vmax, loss

    def r_squared(self, DiffDiff, concs, vmax,km):
        residuals = DiffDiff - (vmax*concs)/(km + concs) #curve(concs, vmax, km)
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((DiffDiff-np.mean(DiffDiff))**2)
        r_squared = 1 - (ss_res / ss_tot)
        return r_squared
        
    def r_squared_torch(self,y,yh):
        residuals = y-yh
        ss_res = (residuals**2).sum()
        ss_tot = (y-y.mean()**2).sum()
        r_squared = 1 - (ss_res / ss_tot)
        return r_squared
    

def main():

	pass
if __name__ =='__main__':
    main()