import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
import random
import os
import itertools
from scipy import optimize
from tqdm import tqdm


def getPlateData(path):
    '''
    This reads full range UV-Vis trace from a BMG PheraStar Platereader
    as a csv and does a bit or data munging and returns a pandas dataframe
    and the details of the experiment that the machine records, which I'm
    calling 'metadata'
    '''
    data = pd.read_csv(path, skiprows = 6)
    metadata = pd.read_csv(path, nrows = 3)
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

def select_traces(data, selection):
    # assumes that the data has a well number index
    data.reset_index(inplace=True)
    well_index = data['WellLetter']
    data = data.loc[well_index.str.contains(str(selection)),:]
    data.drop(['WellLetter'],inplace=True, axis=1)
    return data

def plotPlateData(data, title, concs,save=False):
    '''
    Little bit at the beginning to scale the axes
    by the max in the area I'm interested in (390:420),
    I'm calling it axmax
    '''
    axmax = data.loc[:,380:].max().max()*1.1 # breathing room
    x = data.columns.astype(int)
    fig, ax = plt.subplots(figsize=(10,5))
    ax.set_prop_cycle('color',plt.cm.magma(np.linspace(0,0.9,len(data))))
    for i in range(len(data)):
        y = data.iloc[i,:]
        plt.plot(x,y, lw = 2, alpha = 0.8)
    plt.title(title + ' Corrected Spectra',fontsize=10)
    plt.xticks(x[::50])
    plt.xlim((310,800))
    plt.ylim((-0.05,axmax))
    plt.xlabel('Wavlength nm')
    plt.ylabel('Absorbance')
    plt.legend(np.around(concs,2) , title = 'Substrate concentration in uM')
    if save:
        title=(title + ' Corrected Spectra PM.png').replace(' ','_')
        title=title.replace('\n','_')
        plt.savefig(title)
        plt.close()
    else:
        plt.show()

def plotPlateDifferenceSpectra(data,pureprotein,title,concs,save=False):

    data.reset_index(drop=True,inplace=True)
    pureprotein.reset_index(drop=True,inplace=True)
    data = data.subtract(pureprotein,axis=1)
    axmax = data.loc[:,380:].max().max()*1.5 # breathing room
    axmin = data.loc[:,380:].min().min()*1.5 # breathing room
    x = data.columns.astype(int)
    fig, ax = plt.subplots(figsize=(10,2.5))
    ax.set_prop_cycle('color',plt.cm.magma(np.linspace(0,0.9,len(data))))
    concs = np.around(concs,2)
    for i in range(len(data)):
        y = data.iloc[i,:]
        plt.plot(x,y, lw = 2, alpha = 0.8)
    plt.title(title + ' Difference Spectra',fontsize=10)
    plt.xticks(x[::50])
    plt.xlim((310,800))
    plt.ylim((axmax,axmin))
    plt.xlabel('Wavlength nm')
    plt.ylabel('Change in Absorbance')
    plt.legend(concs, title = 'Substrate concentration in uM',loc='right')
    if save:
        title=(title + ' Difference Spectra PM.png').replace(' ','_')
        title=title.replace('\n','_')
        plt.savefig(title)
        plt.close()
    else:
        plt.show()

def calculateDiffDiff(data,pureprotein):
    '''
    Looks like I should Normalize these between 0 and 1 or something
    '''
    data=data.subtract(pureprotein,axis=1)
    DiffA420=data.loc[:,420]
    DiffA390=data.loc[:,390]
    DiffDiff = DiffA390-DiffA420
    DiffDiff -= DiffDiff.min()
    DiffDiff /= DiffDiff.max()
    DiffDiff.fillna(0, inplace=True)
    return DiffDiff

def curve(x, vmax, km):
    y = (vmax*x)/(km + x)
    return y

def calculate_Km(DiffDiff,concs):
    '''
    The idea of the bounds here is to make the lower limit
    of vmax 1, since the vamx shouldn't be reached.
    Arguments against: I'm scaling by the min and max values
    which could be anomalies, in which case I should make the
    lower limit 0 to avoid negative vmaxs because that seems weird.

    How does this handle non-substrates?
    '''
    params, cov = optimize.curve_fit(curve, concs, DiffDiff,\
        bounds=((0,0),(np.inf,np.inf)))
    vmax = params[0]
    km = params[1]
    return vmax, km

def r_squared(DiffDiff, concs, vmax,km):
    residuals = DiffDiff - curve(concs, vmax, km)
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((DiffDiff-np.mean(DiffDiff))**2)
    r_squared = 1 - (ss_res / ss_tot)
    return r_squared

def Plot_MichaelisMenten(DiffDiff,concs, title,save=False):
    vmax, km = calculate_Km(DiffDiff,concs)
    x2 = np.linspace(0,concs.max(), 500)
    y2 = curve(x2, vmax, km)
    r_sq = r_squared(DiffDiff, concs, vmax,km)

    pos1 = y2.max()
    pos2 = pos1 - 7*(y2.max()-y2.min())/8
    fig, ax = plt.subplots(figsize=(10,5))
    plt.set_cmap('inferno')
    plt.plot(x2, y2,color = '0.1')
    plt.scatter(concs, DiffDiff,  color = 'orange', s = 30)
    plt.title(title + 'Michaelis Menten Plot',fontsize=10)
    plt.ylabel('Difference in Abs')
    plt.xlabel('[Substrate] uM')
    plt.text(800,y2.max()/2,'Km = '+str(np.around(km,2))+'\n'\
    +'Vmax = '+str(np.around(vmax,2))+'\n'\
    +'R squared = '+str(np.around(r_sq,2)))
    if save:
        title=(title + ' Michaelis Menten PM.png').replace(' ','_')
        title=title.replace('\n','_')
        plt.savefig(title)
        plt.close()
    else:
        plt.show()

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


def return_metrics(DiffDiff,concs,plate):
    vmax, km = calculate_Km(DiffDiff,concs)
    r_sq = r_squared(DiffDiff, concs, vmax,km)
    df = pd.DataFrame([[vmax,km,r_sq,plate]],columns = ['vmax','Km','R^2','Plate'])
    return df

def generate_markdown_Table(titles):
    for i in titles:
        print('|![]('+(i + ' Corrected Spectra PM.png').replace(' ','_')+')|![]('\
        +(i + ' Difference Spectra PM.png').replace(' ','_')\
        +')|![]('+(i + ' Michaelis Menten PM.png').replace(' ','_')+')|')


def Data_Munjing_pipeline(path, selection):
    '''selection should match the well column number
    then Little bit of selecting the right columns
    Every other row is subtracted because that's how I lay out my
    plates for in case the compound itself absorbs light and interferes with
    the measurements. Then the protein and DMSO are used as a reference point
    to see how much of an effect each compound has. '''
    data = getPlateData(path)
    well_index = data.index
    data.index = well_index
    data=subtract_evryOtherRow(data)
    well_columns = pd.Series(data.index).str.extract(r'(\d+)').astype(int)
    pureprotein_andDMSO = data.iloc[well_columns[well_columns==1].dropna().index] #### important one!
    well_columns=well_columns[well_columns==selection].dropna().index
    data=data.iloc[well_columns]
    diffdiff=calculateDiffDiff(data.reset_index(drop=True),pureprotein_andDMSO.reset_index(drop=True))
    return data, pureprotein_andDMSO, diffdiff

def getTitleFromPlateConditions(rowFromDf):
    return 'Plate: '+rowFromDf.loc[1]+'  [Kpi]: '+str(rowFromDf.loc[2])+'  [Kcl]: '+str(rowFromDf.loc[3])+'  Substrate: '+rowFromDf.loc[4]

concs = np.array([1,
0.5,
0.25,
0.125,
0.0625,
0.03125,
0.015625,
0.0078125])*1000


files = ['20190806.CSV','20190807_BrandPSStandard.CSV','20190807_BrandLipograde.CSV','20190807_ThermoDelta.CSV']
conditions=['TheBlackPlateConditions.csv','BrandPSStandard_conditions.csv','BrandLipoGrade_conditions.csv','ThermoDelta_conditions.csv']
plates=['that black one','Brand PS Standard','Brand Lipograde','Thermo Delta']
output_metrix=pd.DataFrame([],columns = ['vmax','Km','R^2','Plate'])


for condition,file in zip(conditions,files):
    conds=pd.read_csv(condition,header=None)
    for i in tqdm(range(1,len(conds))):
        title=getTitleFromPlateConditions(conds.loc[i-1,:])

        plate=plates[files.index(file)]
        data, pureprotein_andDMSO, diffdiff = Data_Munjing_pipeline(file,i)
        #metrix=return_metrics(diffdiff,concs,plate)
        #output_metrix=output_metrix.append(metrix)
        plotPlateData(data,'BM3 WT Spectra \n '+title,concs,save=True)
        plotPlateDifferenceSpectra(data,pureprotein_andDMSO,'BM3 WT Difference Spectra \n '+title,concs,save=True)
        Plot_MichaelisMenten(diffdiff, concs,'BM3 WT Michaelis Menten \n'+title,save=True)

#output_metrix.reset_index(drop=True,inplace=True)
#output_metrix.to_csv('PlateValidationMetrix.csv')
