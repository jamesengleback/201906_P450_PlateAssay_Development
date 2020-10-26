import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import argparse
from scipy import ndimage
import tabulatehelper as th
from datetime import date
import string
from tqdm import tqdm

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
    def BlockPipeline(self,Block):
        testWells, BlankWells = self.GetBlock(Block)
        BlockPlan = self.plan.loc[self.plan['Block']==Block]
        NormalizedWells =self.NormalizeBlock(testWells, BlankWells)
        Diff = self.DifferenceBlock(NormalizedWells)
        DiffDiff = self.DiffDiffBlock(Diff)
        title1 =self.PlotTrace(NormalizedWells,BlockPlan,'Not Mixed - Normalized Traces'+str(Block),save=True)
        title2 = self.PlotTrace(Diff,BlockPlan,'Not Mixed - Difference Spectra'+str(Block),save=True)
        title3 = self.PlotMichaelesMenten(DiffDiff,BlockPlan,str(Block),save=True)
        self.figures = self.figures.append(pd.DataFrame([['![]({})'.format(title1),
        '![]({})'.format(title2),
        '![]({})'.format(title3)]],columns=['Normalized Traces','Difference Spectra','Michaelis Menten']))


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
        DiffDiff = Differenceblock.loc[:,420] - Differenceblock.loc[:,390]
        return DiffDiff

    def PlotTrace(self,trace,BlockPlan,TraceType,save=False):
        # Checking the column headers are integers
        if type(trace.columns) != 'pandas.core.indexes.numeric.Int64Index':
            trace.columns=trace.columns.astype(int)

        # Strip the duplicated rows from the blockplan
        BlockPlan=BlockPlan.drop_duplicates()
        #BlockPlan['Concentration'] = BlockPlan['Concentration']
        DMSO_Frac = BlockPlan['DMSO Fraction'].unique()[0]
        concentrations = BlockPlan['Concentration'].unique() # quick fix
        #Set axis limits
        axmax = trace.loc[:,390:].max().max()*1.5
        axmin = trace.loc[:,390:].min().min()*1.5

        # Define figure + set the colorcyle to a continuous color map
        fig, ax = plt.subplots(figsize=(15,10))
        ax.set_prop_cycle('color',plt.cm.magma(np.linspace(0,0.9,len(trace))))

        #Plot each trace idividually
        for i in range(len(trace)):
            y = trace.iloc[i,:]
            plt.plot(trace.columns,y, lw = 2, alpha = 0.8)

        plt.title('Arachadionic Acid {} [DMSO] = {}%'.format(TraceType,DMSO_Frac*100),fontsize=16)
        plt.xticks(trace.columns[::50])
        plt.xlim((350,800))
        plt.ylim((axmin,axmax))
        plt.xlabel('Wavlength nm',fontsize=14)
        plt.ylabel('Change in Absorbance',fontsize=14)
        plt.legend(np.round(concentrations,2), title = 'Substrate concentration in uM',loc='right')
        if save:
            plt.savefig(('Arachadionic Acid {} [DMSO] = {}% .png'.format(TraceType,DMSO_Frac*100).replace(' ','_')))
            plt.close()
            return 'Arachadionic Acid {} [DMSO] = {}% .png'.format(TraceType,DMSO_Frac*100).replace(' ','_')
        else:
            plt.show()

    def PlotMichaelesMenten(self,DiffDiff,BlockPlan,Block,save=False):
        concentrations = BlockPlan['Concentration'].unique()
        DMSO_Frac = BlockPlan['DMSO Fraction'].unique()[0]
        plt.figure(figsize=(10,10))
        plt.scatter(concentrations,DiffDiff)
        plt.title(('Arachadionic Acid, [DMSO] = {}% .png'.format(DMSO_Frac*100)),fontsize=16)
        plt.xlabel('Concentration uM',fontsize=14)
        plt.ylabel('Change in Absorbance',fontsize=14)
        if save:
            plt.savefig(('Not Mixed - Arachadionic Acid {}, [DMSO] = {}% .png'.format(Block,DMSO_Frac*100).replace(' ','_')))
            plt.close()
            return 'Not Mixed - Arachadionic Acid {}, [DMSO] = {}% .png'.format(Block,DMSO_Frac*100).replace(' ','_')
        else:
            plt.show()



def main():
    args=argParser()
    plate_data = args.i[0]
    plan = args.p[0]
    dataset = PlateDataset(plate_data,plan)
    for i in tqdm(range(1,25)):
        try:
            dataset.BlockPipeline(i)
        except:
            pass

    table = th.md_table(dataset.figures)
    print(table)

if __name__ =='__main__':
    main()
