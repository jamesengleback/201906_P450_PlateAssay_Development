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

def plotPlateData(data, title):
    ## = pd.Series([list(i)[1] for i in Data_Frames[0].reset_index()['WellLetter']]).astype(int)
    x = data.columns.astype(int)
    fig, ax = plt.subplots(figsize=(7,3))
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
    plt.title(title + 'Corrected Spectra')
    plt.xticks(x[::50])
    plt.xlim((220,800))
    plt.ylim((-0.05,0.5))
    plt.xlabel('Wavlength nm')
    plt.ylabel('Absorbance')
    plt.legend(concs, title = 'Substrate concentration in uM')
    plt.savefig((title + 'Corrected Spectra').replace(' ','_')+'.png')
    #plt.show()

def plotPlateDifferenceSpectra(data,pureprotein,title):
    data.reset_index(drop=True,inplace=True)
    pureprotein.reset_index(drop=True,inplace=True)
    data = data.subtract(pureprotein,axis=1)
    x = data.columns.astype(int)
    fig, ax = plt.subplots(figsize=(7,3))
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
    plt.title(title + 'Difference Spectra')
    plt.xticks(x[::50])
    plt.xlim((220,800))
    plt.ylim((-0.5,0.5))
    plt.xlabel('Wavlength nm')
    plt.ylabel('Change in Absorbance')
    plt.legend(concs, title = 'Substrate concentration in uM',loc='right')
    plt.savefig((title + 'Difference Spectra').replace(' ','_')+'.png')
    #plt.show()

def calculateDiffDiff(data,pureprotein):
    data=data.subtract(pureprotein,axis=1)
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
    vmax, km = params
    residuals = DiffDiff - curve(concs, vmax, km)
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((DiffDiff-np.mean(DiffDiff))**2)
    r_squared = 1 - (ss_res / ss_tot)
    return vmax, km, r_squared

def Plot_MichaelisMenten(DiffDiff,concs, title):
    vmax, km = calculate_Km(DiffDiff,concs)
    x2 = np.linspace(0,concs.max(), 500)
    y2 = curve(x2, vmax, km)
    # R^2
    residuals = DiffDiff - curve(concs, vmax, km)
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((DiffDiff-np.mean(DiffDiff))**2)
    r_squared = 1 - (ss_res / ss_tot)

    fig, ax = plt.subplots(figsize=(5,3))
    plt.set_cmap('inferno')
    plt.plot(x2, y2,color = '0.1')
    plt.scatter(concs, DiffDiff,  color = 'orange', s = 30)
    plt.title(title + 'Michaelis Menten Plot')
    plt.ylabel('Difference in Abs')
    plt.xlabel('[Substrate] µM')
    yposition = np.linspace(0,vmax,5).tolist()
    plt.text(600,yposition[0],'Km = '+str(np.around(km,2)))
    plt.text(600,yposition[1],'Vmax = '+str(np.around(vmax,2)))
    plt.text(600, yposition[2],'R squared = '+str(np.around(r_squared,2)))
    plt.savefig((title + 'Michaelis Menten Plot').replace(' ','_')+'.png')
    #plt.show()

def subtract_evryOtherRow(data):
    rowswithprotein = ['A', 'C', 'E', 'G', 'I', 'K', 'M', 'O']
    well_index = pd.Series(data.index).str.extract(r'(\w)',expand=False)
    rowswithprotein = well_index.loc[well_index.isin(rowswithprotein)]

    dataWithProtein = data.iloc[rowswithprotein.index,:]
    datawithoutprotein = data.drop(dataWithProtein.index)
    indexExceptForRealThisTime = dataWithProtein.index
    dataWithProtein.reset_index(drop=True,inplace=True)
    datawithoutprotein.reset_index(drop=True,inplace=True)
    output = dataWithProtein - datawithoutprotein
    output.index=indexExceptForRealThisTime
    return output

def StickItAllTogether(path, selection,concs, title):
    '''selection should match the well column number'''
    data = getPlateData(path)
    well_index = data.index
    data = baseline_correction(data)
    data.index = well_index
    data=subtract_evryOtherRow(data)
    '''
    Little bit of selecting the right columns
    '''
    well_columns = pd.Series(data.index).str.extract(r'(\d+)').astype(int)
    pureprotein_andDMSO = data.iloc[well_columns[well_columns==2].dropna().index]
    well_columns=well_columns[well_columns==selection].dropna().index
    data=data.iloc[well_columns]
    diffdiff=calculateDiffDiff(data.reset_index(drop=True), pureprotein_andDMSO.reset_index(drop=True))

    #plotPlateData(data,title+' ')
    #plotPlateDifferenceSpectra(data,pureprotein_andDMSO,title)
    #Plot_MichaelisMenten(diffdiff, concs,title)
    return calculate_Km(diffdiff,concs)

concs = np.array([1,
0.5,
0.25,
0.125,
0.0625,
0.03125,
0.015625,
0.0078125])*1000


allthetitles = ['buffer','protein+DMSO','Lauric acid 1','Lauric acid 2', 'Lauric acid 3', 'Lauric acid 4', 'Lauric acid 5',
'Arachadonic acid 1', 'Arachadonic acid 2', 'Arachadonic acid 3', 'Arachadonic acid 4', 'Arachadonic acid 5',
'4-Phenylimidazole 1', '4-Phenylimidazole 2', '4-Phenylimidazole 3', '4-Phenylimidazole 4', '4-Phenylimidazole 5']
'''
for i in range(1,17):
    title=allthetitles[i-1]+' '
    StickItAllTogether('SerialDilfattyacids.CSV',i,concs,title)


'''


kds=[]
for i in range(1,17):
    vmax,kd,r_squared = StickItAllTogether('SerialDilfattyacids.CSV',i,concs, 'balls')
    kds.append([vmax,kd,r_squared])
kds=pd.DataFrame(kds)
kds.index=['protein+DMSO','Lauric acid 1','Lauric acid 2', 'Lauric acid 3', 'Lauric acid 4', 'Lauric acid 5',
'Arachadonic acid 1', 'Arachadonic acid 2', 'Arachadonic acid 3', 'Arachadonic acid 4', 'Arachadonic acid 5',
'4-Phenylimidazole 1', '4-Phenylimidazole 2', '4-Phenylimidazole 3', '4-Phenylimidazole 4', '4-Phenylimidazole 5']
kds.columns=['Vmax','Kd','R^2']
print(kds)
#kds.to_csv('20190609_')
