
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

class dataset:
    def __init__(self, path):
        self.data = pd.read_csv(path)
        self.wavelengths = self.Get_Wavelengths()
        self.Clean_Data = self.StripColumns()[:,self.wavelengths]
    def Get_Wavelengths(self):
        wavelengths = self.data.iloc[:,0] # first column
        wavelengths = wavelengths[wavelengths.str.contains(r'\d\d\d.\d\d\d\d')].astype(float)
        return wavelengths.reset_index(drop=True)
    def StripColumns(self):
        match = 'Abs'
        temp = []
        count = 0
        for i in self.data.loc[0].astype(str):### the astype thing was just a sneaky fix dw about it
            if match in i:
                temp.append(count)
            count +=1
        cleanData = self.data.iloc[:,temp]
        cleanData.columns = cleanData.iloc[0]
        cleanData = cleanData.iloc[1:,:].dropna().reset_index(drop=True)

        return cleanData


path = '~/Desktop/Work/201906_PlateAssayDevelopment/1_PlateSelection/'+'20190603_BM3StckConcCheck.csv'

Dataet = dataset(path)
print(Dataet.Clean_Data)
