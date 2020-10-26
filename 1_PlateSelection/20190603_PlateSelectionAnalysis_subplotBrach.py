import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
import random
import os
import itertools


def getPlateData(path):
    '''
    This reads full range UV-Vis trace from a BMG PheraStar Platereader
    as a csv and does a bit or data munging and returns a pandas dataframe
    and the details of the experiment that the machine records, which I'm
    calling 'metadata'
    '''
    data = pd.read_csv(path, skiprows = 6)
    metadata = pd.read_csv(path, nrows = 3)

    # rename some columns for readability
    #.columns[0:3] = ['WellLetter','WellNumber', 'SampleID']
    data.rename(columns = {'Unnamed: 0':'WellLetter','Unnamed: 1':'WellNumber','Unnamed: 2':'SampleID',}, inplace = True)
    data.dropna(inplace = True, how = 'all')
    unused_wells = data['SampleID'].str.contains('unused')
    data = data.loc[unused_wells == False] ### The bool statement flips and strips unused wells
    WellIndex = data.loc[:,'WellLetter'].str.cat(data.loc[:,'WellNumber'].astype(str))
    data.index = WellIndex
    data = data.loc[:,'220':].dropna(axis = 1) # Numerical data only!
    data.columns = data.columns.astype(int)
    # zero at 800 nm
    data.reset_index(drop=True,inplace=True) # otherwise SUBTRACT can't match up cells
    data = data.subtract(data.loc[:,800],axis=0)
    data.index = WellIndex
    return data, metadata

def plotPlateData(data, title):
    WellNumbers = pd.Series([list(i)[1] for i in Data_Frames[0].reset_index()['WellLetter']]).astype(int)
    x = data.columns.astype(int)
    #fig, ax = plt.subplots(figsize=(15,5))
    plt.figure(figsize=(15,5))
    colors = {1:'#304360',
    2:'#3f6c77',
    3:'#41a48c'}
    #ax.set_prop_cycle('color',plt.cm.inferno(np.linspace(0,0.9,len(data))))

    plt.set_cmap('magma')
    for i in range(len(data)):
        y = data.iloc[i,:]
        well = WellNumbers[i]
        plt.plot(x,y, lw = 0.5, alpha = 0.7, color = colors[well])
    plt.title(title)
    plt.xticks(x[::50])
    plt.xlim((220,800))
    plt.ylim((0,1))
    plt.xlabel('Wavlength nm')
    plt.ylabel('Absorbance')
    plt.show()


def getFiles(csvs):
    path_list = []
    for i in csvs:
        path = '~/Desktop/Work/201906_PlateAssayDevelopment/1_PlateSelection/'+i
        path_list.append(path)


    '''
    Files are in, now I'm putting everything into one dataframe and
    also getting the Experiment ID number in a pandas Series to match
    up later.
    '''
    data_frames = []
    Experiment_IDs = []

    for experiment in path_list:
        data, metadata = getPlateData(experiment)
        ID = metadata.iloc[1,0]
        Experiment_IDs.append([ID]*len(data))
        data_frames.append(data)

    uniqueIDs =np.unique(np.array(Experiment_IDs))
    return data_frames, Experiment_IDs,uniqueIDs

def subplotPlateData(list_of_DataFrames,Experiment_IDs):
    '''for i in list_of_DataFrames:
        print(i)

        '''
    colors = {1:'#304360',2:'#3f6c77',3:'#41a48c'}
    count = 0 ## this is to adress the subplots
    fig, ax = plt.subplots(nrows=6, ncols=2, figsize = (7,14), sharex=True, sharey=False,squeeze=False)
    #fig.add_gridspec(6,2)
    for row in ax:
        for col in row:

            data = list_of_DataFrames[count]
            WellNumbers = pd.Series([list(i)[1] for i in data.reset_index()['WellLetter']]).astype(int)
            x = data.columns.astype(int)

            for i in range(len(data)):
                y = data.iloc[i,:]
                well = WellNumbers[i]

                col.plot(x,y, lw = 0.5, alpha = 0.7, color = colors[well])
            title = Experiment_IDs[count]
            col.set_xticks(x[::100])
            col.set_yticks(np.linspace(0,1,3))
            col.set_xlim((220,800))
            col.set_ylim((-0.1,1))
            col.set_title('Test ID: '+title, fontsize=10)
            col.set_ylabel('Abs', fontsize = 8)
            col.set_xlabel('Wavelength', fontsize = 8)
            count+=1

    fig.tight_layout()
    plt.subplots_adjust(hspace=1)
    lgnd = plt.legend(['2 uM','5 uM','10 uM'], loc='best',markerfirst=True)
    count =1
    for i in lgnd.legendHandles:
        i.set_linewidth(6.0)
        i.set_color(colors[count])
        count+=1
    plt.savefig('20190603_PlateselectionTests_ALL.png')




# getting the files
csvs = ['36640_2.CSV',
  '3770bc_2.CSV',
   '464718_2.CSV'  ,
   '761860_2.CSV',
   '781620_2.CSV',
   'DELTA_2.CSV',
   '36640.CSV',
   '3770bc.CSV',
   '464718.CSV',
   '761860.CSV',
   '781620.CSV',
   'DELTA.CSV']

Data_Frames, Experiment_IDs, uniqueIDs = getFiles(csvs)
subplotPlateData(Data_Frames,uniqueIDs)
