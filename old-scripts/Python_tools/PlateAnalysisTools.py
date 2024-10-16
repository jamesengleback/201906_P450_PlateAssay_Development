import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
import random
import os

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
    # zero at 800 nm later
    return data, metadata

def plotPlateData(data):

    x = data.columns.astype(int)


    fig, ax = plt.subplots(figsize=(15,5))
    ax.set_prop_cycle('color',plt.cm.inferno(np.linspace(0,0.9,len(data))))
    plt.set_cmap('magma')
    for i in range(len(data)):
        y = data.iloc[i,:]
        plt.plot(x,y, lw = 0.5, alpha = 0.7)
    plt.xticks(x[::50])
    plt.xlim((250,800))
    plt.ylim((0,1))
    plt.xlabel('Wavlength nm')
    plt.ylabel('Absorbance')
    plt.show()

def fitscattercurve(PlateScan, plot_loss=False, plot_fit=False, return_n=False):
    '''
    y = (1/ x)**4 * n
    '''
    x,y = torch.tensor(PlateScan.values, dtype = torch.float, requires_grad=True), \
        torch.tensor(PlateScan.index.values,  dtype = torch.float)
    RayleyScattering = lambda y, n: (1/ x)**4 * n
    #n = torch.rand(size =(1,1), requires_grad=True)
    n = torch.tensor(random.uniform(0,1))
    n = torch.nn.Parameter(n)
    opt = torch.optim.Adam({n}, lr = 0.1)
    loss_fn = torch.nn.MSELoss()

    losslist = []
    for i in range(10**2):
        yhat = (1/ x)**4 * n
        loss = loss_fn(x,yhat)
        loss.backward()
        opt.step()
        opt.zero_grad()
        losslist.append(loss)
    losslist = np.array(losslist)

    if plot_loss ==True:
        plt.style.use('seaborn')
        plt.figure(figsize = (7.5,2.5))
        plt.plot(losslist, lw = 2, color = '#5E2750')
        plt.xlabel('Iteration')
        plt.ylabel('Mean Squared Error')
        plt.show()
    '''
    if plot_fit ==True:
        #### Still not working yet
        yhat = (1/ x)**4 * n
        yhat = yhat.detach()

        plt.style.use('seaborn')
        plt.figure(figsize = (7.5,2.5))
        plt.plot(yhat.view(-1), lw = 2, color = '#5E2750')
        plt.xlabel('Iteration')
        plt.ylabel('Mean Squared Error')
        plt.show()
        '''
    if return_n==True:
        return n.item()


csvs = ['180918_1753.csv',
'180918_1845.csv',
'180918_1818.csv',
'180918_1747.csv',
'180918_1913.csv',
'180918_1854.csv',
'180918_1800.csv',
'180918_1810.csv',
'180918_1826.csv',
'180918_1745.csv',
'180918_1839.csv',
'180918_1904.csv']
path_list = []

for i in csvs:
    path = '~/Desktop/Work/201906_PlateAssayDevelopment/2018_Stuff/'+i
    path_list.append(path)

data_frames = []
for experiment in path_list:
    data, metadata = getPlateData(experiment)
    data_frames.append(data)
data_frames = pd.concat(data_frames)

### all of the datafraes are in one!
def concatData(path_list):
    data_frames = []
    for experiment in path_list:
        data, metadata = getPlateData(experiment)
        data_frames.append(data)
    data_frames = pd.concat(data_frames)
    return data_frames

All_Traces = concatData(path_list)

plotPlateData(All_Traces)
