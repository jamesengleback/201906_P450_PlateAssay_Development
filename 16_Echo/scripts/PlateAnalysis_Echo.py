import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import argparse
from scipy import ndimage
import string
from tqdm import tqdm

import torch
import torch.nn as nn

def argParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', nargs=1, help='trace')
    parser.add_argument('-p', nargs=1, help='plan')
    parser.add_argument('-s', help='save?',action="store_true")
    parser.add_argument('-g', nargs=1,default=[0], help='guassian smoothing')
    args=parser.parse_args()
    return args

class PlateDataset():
    def __init__(self,plate_data,experiment_plan):
        self.plate_data = plate_data
        self.plan = self.GetExperimentPlan(experiment_plan)
        self.data, self.metadata = self.GetPlateData()
        self.smoothingParam = 1
        self.figures = pd.DataFrame([],columns=['Normalized Traces','Difference Spectra','Michaelis Menten'])

    def CalculateMetrics(self,Block):
        plan = self.plan.loc[Block,:]
        testWells, BlankWells = self.GetBlock(Block)
        NormalizedWells =self.NormalizeBlock(testWells, BlankWells)
        Diff = self.DifferenceBlock(NormalizedWells)
        DiffDiff = self.DiffDiffBlock(Diff)

        K,percentDMSO, Vol = plan['K-Value'], plan['% DMSO'], plan['Working Vol']
        concs = self.CalculateCompoundConcs(K,Vol,percentDMSO)
        km, vmax, loss = self.FitMichaelisMenten(concs,DiffDiff)
        km, vmax, loss  = km.item(), vmax.item(), loss.item()
        r_squared = self.r_squared(DiffDiff, concs, vmax,km)
        output = pd.DataFrame([[ K,percentDMSO, Vol,km, vmax, loss, r_squared]],
        columns = [ 'K','percentDMSO', 'Vol','km', 'vmax', 'loss', 'r_squared'])
        return output

    def PlotFigure(self,Block):
        plan = self.plan.loc[Block,:]
        title = 'K-Value = {}   DMSO = {}%  Working Vol = {} ul'.format(round(plan['K-Value'],2),
        round(plan['% DMSO'],2),
        round(plan['Working Vol'],2))
        testWells, BlankWells = self.GetBlock(Block)
        NormalizedWells =self.NormalizeBlock(testWells, BlankWells)
        Diff = self.DifferenceBlock(NormalizedWells)
        DiffDiff = self.DiffDiffBlock(Diff)
        self.PlotTrace(NormalizedWells,'Normalized Traces ' + title ,plan,save=False)
        self.PlotTrace(Diff,'Difference Spectra ' + title ,plan,save=False)
        self.PlotMichaelesMenten(DiffDiff,plan, 'Michaelis Menten '+ title,save=False)

    def BlockPipeline(self,Block):
        testWells, BlankWells = self.GetBlock(Block)
        BlockPlan = self.plan.loc[self.plan['Unnamed: 0']==Block]
        NormalizedWells =self.NormalizeBlock(testWells, BlankWells)
        Diff = self.DifferenceBlock(NormalizedWells)
        DiffDiff = self.DiffDiffBlock(Diff)
        title1 =self.PlotTrace(NormalizedWells,BlockPlan,'Normalized Traces'+str(Block),save=True)
        title2 = self.PlotTrace(Diff,BlockPlan,'Difference Spectra'+str(Block),save=True)
        title3 = self.PlotMichaelesMenten(DiffDiff,BlockPlan,save=True)

        self.figures = self.figures.append(pd.DataFrame([['![]({})'.format(title1),
        '![]({})'.format(title2),
        '![]({})'.format(title3)]],
        columns=['Normalized Traces','Difference Spectra','Michaelis Menten']))

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

    def GetExperimentPlan(self,experiment_plan):
        return pd.read_csv(experiment_plan)

    def GetBlock(self, Block):
        ### well allocation from block
        rows = dict((number,letter) for letter,number in zip(string.ascii_uppercase,range(1,17)))
        # if block number is odd
        if Block%2!=0:
            blockRows = [rows.get(i) for i in range(1,9)]
            blockCols = (Block,Block+1)
        else:
            blockRows = [rows.get(i) for i in range(9,17)]
            blockCols = (Block-1,Block)
        # Assuming that test column is the leftmost
        testWells = [i+str(blockCols[0]) for i in blockRows]
        BlankWells = [i+str(blockCols[1]) for i in blockRows]
        return testWells, BlankWells

    def GaussianSmoothBlock(self,block):
        output = pd.DataFrame([],columns=block.columns)
        for i in block.index:
            # Locates column, smooths it and returns it to the dataframe
            i = block.loc[i,:]
            i=ndimage.gaussian_filter(i,self.smoothingParam)
            temp = pd.DataFrame([i],columns=block.columns)
            output = output.append(temp)
        return output

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

    def PlotTrace(self,trace,TraceType,plan, save=False):
        # Checking the column headers are integers
        if type(trace.columns) != 'pandas.core.indexes.numeric.Int64Index':
            trace.columns=trace.columns.astype(int)

        K,percentDMSO, Vol = plan['K-Value'], plan['% DMSO'], plan['Working Vol']
        concs = self.CalculateCompoundConcs(K,Vol,percentDMSO)

        # Strip the duplicated rows from the blockplan
        #BlockPlan=BlockPlan[['Volume' ,'Unnamed: 0' ,'k_values', 'sourcewells', 'Compound', 'Concentration']].drop_duplicates()

        #Set axis limits
        axmax = trace.loc[:,390:].max().max()*1.5
        axmin = trace.loc[:,390:].min().min()*1.5

        # Define figure + set the colorcyle to a continuous color map
        fig, ax = plt.subplots(figsize=(20,10))
        ax.set_prop_cycle('color',plt.cm.magma(np.linspace(0,0.9,len(trace))))

        #Plot each trace idividually
        for i in range(len(trace)):
            y = trace.iloc[i,:]
            plt.plot(trace.columns,y, lw = 2, alpha = 0.8)

        title = '{}'.format(TraceType)
        plt.title(title,fontsize = 15)
        plt.xticks(range(300,800,10))#trace.columns[::50])
        plt.xlim((350,800))
        plt.ylim((axmin,axmax))
        plt.xlabel('Wavlength nm')
        plt.ylabel('Change in Absorbance')
        plt.legend(concs, title = 'Substrate concentration in uM',loc='right')
        plt.grid(True)
        if save:
            plt.savefig(title.replace(' ','_')+'.png')
            plt.close()
            return title.replace(' ','_')+'.png'
        else:
            plt.show()

    def PlotMichaelesMenten(self,DiffDiff,plan,title,save=False):
        K,percentDMSO, Vol = plan['K-Value'], plan['% DMSO'], plan['Working Vol']
        concs = self.CalculateCompoundConcs(K,Vol,percentDMSO)
        km, vmax, loss = self.FitMichaelisMenten(concs,DiffDiff)
        km, vmax, loss  = km.item(), vmax.item(), loss.item()
        x = np.linspace(concs.min(),concs.max(),100)

        plt.figure(figsize=(10,10))
        plt.scatter(concs,DiffDiff)

        plt.plot(x, (vmax*x)/(km + x))
        plt.title(title)
        plt.xlabel('Concentration uM')
        plt.ylabel('Change in Absorbance')

        plt.text(concs.max()*0.7,vmax*0.2,'Km = '+str(np.around(km,2))+'\n'\
        +'Vmax = '+str(np.around(vmax,2))+'\n'\
        +'Mean Squared Error = '+str(np.around(loss,5))+'\n'\
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

    def FitMichaelisMenten(self,x,y):
        x = torch.tensor(x,dtype=torch.float) # concs are numpy array
        y = torch.tensor(y.values,dtype=torch.float) # Diffdiff is pd.series
        km = torch.tensor([1.],requires_grad=True,dtype=torch.float)
        vmax = torch.tensor([1.],requires_grad=True,dtype=torch.float)
        optimizer = torch.optim.Adam({km,vmax},lr = 1e-2)
        loss_fn =  nn.L1Loss()
        for i in range(1000):
            y_pred = (vmax*x)/(km + x)
            loss = loss_fn(y,y_pred)
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
        return km, vmax, loss

    def r_squared(self, DiffDiff, concs, vmax,km):
        residuals = DiffDiff - (vmax*concs)/(km + concs) #curve(concs, vmax, km)
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((DiffDiff-np.mean(DiffDiff))**2)
        r_squared = 1 - (ss_res / ss_tot)
        return r_squared



def main():
    args=argParser()
    plate_data = args.i[0]
    plan = args.p[0]
    import ipdb ; ipdb.set_trace()
    dataset = PlateDataset(plate_data,plan)
    for i in tqdm(range(1,25)):
        dataset.BlockPipeline(i)

if __name__ =='__main__':
    main()
