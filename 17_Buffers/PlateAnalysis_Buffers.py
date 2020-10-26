import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm


import string

from scipy import ndimage


class PlateDataset():
    def __init__(self,plate_data):
        self.plate_data = plate_data
        self.data, self.metadata = self.GetPlateData()
        self.smoothingParam = 2
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

    def GaussianSmoothBlock(self,block):
        output = pd.DataFrame([],columns=block.columns)
        for i in block.index:
            # Locates column, smooths it and returns it to the dataframe
            i = block.loc[i,:]
            i=ndimage.gaussian_filter(i,self.smoothingParam)
            temp = pd.DataFrame([i],columns=block.columns)
            output = output.append(temp)
        return output


    def PlotTrace(self,cols,colors=False):
        # Cols has to be an iterable
        # Checking the column headers are integers
        rows = list(string.ascii_uppercase[0:16])
		
        traceIDs = []
        for i in cols:
            for j in rows:
                traceIDs.append(j+str(i))
        traces = self.data.loc[traceIDs,:]
		
		
        if type(traces.columns) != 'pandas.core.indexes.numeric.Int64Index':
            traces.columns=traces.columns.astype(int)
            
        traces = self.GaussianSmoothBlock(traces)
        #Set axis limits
        axmax = traces.loc[:,390:].max().max()*1.5
        axmin = traces.loc[:,390:].min().min()*1.5

        # Define figure + set the colorcyle to a continuous color map
        fig, ax = plt.subplots(figsize=(20,10))
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
        plt.xticks(traces.columns[::50])
        plt.xlim((350,800))
        plt.ylim((axmin,axmax))
        plt.xlabel('Wavlength nm')
        plt.ylabel('Change in Absorbance')
        plt.show()
    
    def GetCols(self,col):
        selection = (pd.Series(self.data.index).str.extract(r'(\d+)')[0].astype(int) ==col)
        selection.index = self.data.index
        return self.data.loc[selection]
        
    def SignalToNoise(self):
        S2N = self.data.loc[:,420] - self.data.loc[:,390]
        S2N -= S2N.min()
        S2N /= np.ptp(S2N)
        return S2N



def main():

	pass
if __name__ =='__main__':
    main()
