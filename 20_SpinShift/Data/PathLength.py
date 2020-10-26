import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import string

class PlatePathlength():
    def __init__(self,path,K):
        self.K = K
        self.plate_path = path
        self.data, self.metadata = self.GetPlateData()
    
    def GetPlateData(self):
        '''
        This reads full range UV-Vis trace from a BMG PheraStar Platereader
        as a csv and does a bit or data munging and returns a pandas dataframe
        and the details of the experiment that the machine records, which I'm
        calling 'metadata'
        '''
        metadata = pd.read_csv(self.plate_path, nrows = 3)
        data = pd.read_csv(self.plate_path, skiprows = 5).dropna(axis=1)
        # Rename columns to something more sensible
        data.rename(columns = {'Raw Data (900 1)':900,'Raw Data (975 2)':975}, inplace = True)
        
        # Cleaning
        # Get rid of unused wells

        # The well letters and well numbers are seperate, so I'm combining them
        WellIndex = data.loc[:,'Well Row'].str.cat(data.loc[:,'Well Col'].astype(str))
        data.index = WellIndex
        data.drop(['Well Row','Well Col','Content'],inplace=True,axis =1) # Don't need these anymore
        data.index = WellIndex
        return data,metadata
        
    def Pathlength(self):
        k = self.K # need to check this in cuvettes
        pathlength = ((self.data[975] - self.data[900])/k) * 10 #mm
        return pathlength
        
    def PlotPlatePathlenghs(self):
        pathlengths = self.Pathlength() # returns pd.Series with well letter/number as index
        # arrange into a 2d plate/dataframe
        plateLayout = pd.DataFrame([])
        index = pd.Series(pathlengths.index)
        rows = index.str.extract(r'(\w)')[0] # not sure if I'll need this later?
        columns = index.str.extract(r'\w(\d+)')[0] # unique only works in pd.Series
        
        for i in columns.unique():
            col = pathlengths.iloc[columns.loc[columns==i].index]
            col.index = list(string.ascii_uppercase[0:16])
            col.name = i
            plateLayout = plateLayout.append(col)
       
        plateLayout = plateLayout.T
        plt.figure(figsize = (10,15))
        plt.set_cmap('inferno')
        plt.imshow(plateLayout)
        plt.xticks(ticks = range(len(plateLayout.columns)), labels = list(plateLayout.columns))
        plt.yticks(ticks = range(len(plateLayout.index)), labels = list(plateLayout.index))
        plt.colorbar(orientation = 'horizontal',shrink = 0.8,label = 'Pathlength (mm)')
        plt.show()        
        
