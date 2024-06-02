import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
import random
import os
import itertools
from scipy import optimize



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
    return data

def baseline_correction(data):
    data.reset_index(inplace=True)
    baseline = data[data['WellLetter'].str.contains('4')]
    baseline = baseline.mean(axis=0)
    # takes mean
    data = data.drop('WellLetter',axis=1)
    data = data.subtract(baseline, axis=1)

    return data

def WhosTheWorstOffender(data):
    data = pd.DataFrame(data.loc[:,320])
    data.reset_index(inplace=True)
    data.sort_values([320],inplace=True,ascending=False)
    return data

def select_traces(data, selection):
    # assumes that the data has a well number index
    data.reset_index(inplace=True)
    well_index = data['WellLetter']
    data = data.loc[well_index.str.contains(str(selection)),:]
    data.drop(['WellLetter'],inplace=True, axis=1)
    return data

def plotPlateData(data):
    ## = pd.Series([list(i)[1] for i in Data_Frames[0].reset_index()['WellLetter']]).astype(int)
    x = data.columns.astype(int)
    fig, ax = plt.subplots(figsize=(15,5))
    #plt.figure(figsize=(15,5))
    colors = {1:'#304360',
    2:'#3f6c77',
    3:'#41a48c'}
    ax.set_prop_cycle('color',plt.cm.inferno(np.linspace(0,0.9,len(data))))
    plt.set_cmap('viridis')

    concs = np.array([1,1,
    0.5,0.5,
    0.25,0.25,
    0.125,0.125,
    0.0625,0.0625,
    0.03125,0.03125,
    0.015625,0.015625,
    0.0078125,0.0078125])*1000

    concs = np.around(concs,2)
    for i in range(len(data)):
        y = data.iloc[i,:]
        plt.plot(x,y, lw = 2, alpha = 0.7)
    plt.title('Serial Dilution Scheme Experiment Dump, Baseline corrected - Protein + NPG, 2.5% DMSO')
    plt.xticks(x[::50])
    plt.xlim((220,800))
    plt.ylim((-0.05,1))
    plt.xlabel('Wavlength nm')
    plt.ylabel('Absorbance')
    plt.legend(concs, title = 'Lauric Acid concentration in uM')
    plt.show()

def plotPlateDifferenceSpectra(data,pureprotein):
    data = data.subtract(pureprotein,axis=1)
    x = data.columns.astype(int)
    fig, ax = plt.subplots(figsize=(15,5))
    ax.set_prop_cycle('color',plt.cm.inferno(np.linspace(0,0.9,len(data))))
    plt.set_cmap('viridis')
    concs = np.array([1,1,
    0.5,0.5,
    0.25,0.25,
    0.125,0.125,
    0.0625,0.0625,
    0.03125,0.03125,
    0.015625,0.015625,
    0.0078125,0.0078125])*1000

    concs = np.around(concs,2)
    for i in range(len(data)):
        y = data.iloc[i,:]
        plt.plot(x,y, lw = 2, alpha = 0.7)
    plt.title('Serial Dilution Scheme Experiment Dump, Baseline corrected - Protein + Lauric Acid, 5% DMSO')
    plt.xticks(x[::50])
    plt.xlim((220,800))
    plt.ylim((-0.5,0.5))
    plt.xlabel('Wavlength nm')
    plt.ylabel('Change in Absorbance')
    plt.legend(concs, title = 'Substrate concentration in uM',loc='right')
    plt.show()

def calculateDiffDiff(data,pureprotein):
    data=data.subtract(pureprotein,axis=1).drop('index',axis=1)
    DiffA420=data.loc[:,420]
    DiffA390=data.loc[:,390]
    DiffDiff = DiffA390-DiffA420
    return DiffDiff

def curve(x, vmax, km):
    y = (vmax*x)/(km + x)
    return y

def calculate_Km(DiffDiff,concs):
    params, cov = optimize.curve_fit(curve, concs, DiffDiff,
                                                   p0=[2, 2])
    vmax = params[0]
    km = params[1]
    return vmax, km

def Plot_MichaelisMenten(DiffDiff,concs):
    vmax, km = calculate_Km(DiffDiff,concs)
    x2 = np.linspace(0,concs.max(), 500)
    y2 = curve(x2, vmax, km)
    # R^2
    residuals = DiffDiff - curve(concs, vmax, km)
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((DiffDiff-np.mean(DiffDiff))**2)
    r_squared = 1 - (ss_res / ss_tot)

    fig, ax = plt.subplots(figsize=(7.5,5))
    plt.set_cmap('inferno')
    plt.plot(x2, y2,color = '0.1')
    plt.scatter(concs, DiffDiff,  color = 'orange', s = 30)
    plt.title('Serial Dilution Scheme Experiment Dump, Baseline corrected -\n Protein + Lauric Acid, 2.5% DMSO')
    plt.ylabel('Difference in Abs')
    plt.xlabel('[Substrate] µM')
    plt.text(400,0.2,'Km = '+str(np.around(km,2)))
    plt.text(400,0.15,'Vmax = '+str(np.around(vmax,2)))
    plt.text(400,0.1,'R squared = '+str(np.around(r_squared,2)))

    plt.show()

data = getPlateData('SerialDilSchem1.CSV')
well_index = data.index
data = baseline_correction(data)
data.index = well_index
pureprotein = select_traces(data,5).mean(axis=0)

j = select_traces(data,7)
DiffDiff=calculateDiffDiff(j,pureprotein)
concs = np.array([0.5,0.5,
0.25,0.25,
0.125,0.125,
0.0625,0.0625,
0.03125,0.03125,
0.015625,0.015625,
0.0078125,0.0078125,
0.00390625,0.00390625])*1000

Plot_MichaelisMenten(DiffDiff,concs)
