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
    fig, ax = plt.subplots(figsize=(5,5))
    ax.set_prop_cycle('color',plt.cm.magma(np.linspace(0,0.9,len(data))))
    for i in range(len(data)):
        y = data.iloc[i,:]
        plt.plot(x,y, lw = 2, alpha = 0.8)
    plt.title(title + ' Corrected Spectra')
    plt.xticks(x[::50])
    plt.xlim((220,800))
    plt.ylim((-0.05,axmax))
    plt.xlabel('Wavlength nm')
    plt.ylabel('Absorbance')
    plt.legend(np.around(concs,2) , title = 'Substrate concentration in µM')
    if save:
        plt.savefig((title + ' Corrected Spectra PM.png').replace(' ','_'))
    else:
        plt.show()

def plotPlateDifferenceSpectra(data,pureprotein,title,concs,save=False):
    data.reset_index(drop=True,inplace=True)
    pureprotein.reset_index(drop=True,inplace=True)
    data = data.subtract(pureprotein,axis=1)
    x = data.columns.astype(int)
    fig, ax = plt.subplots(figsize=(7,2.5))
    ax.set_prop_cycle('color',plt.cm.magma(np.linspace(0,0.9,len(data))))
    concs = np.around(concs,2)
    for i in range(len(data)):
        y = data.iloc[i,:]
        plt.plot(x,y, lw = 2, alpha = 0.8)
    plt.title(title + ' Difference Spectra')
    plt.xticks(x[::50])
    plt.xlim((350,800))
    plt.ylim((-0.3,0.4))
    plt.xlabel('Wavlength nm')
    plt.ylabel('Change in Absorbance')
    plt.legend(concs, title = 'Substrate concentration in µM',loc='right')
    if save:
        plt.savefig((title + ' Difference Spectra PM.png').replace(' ','_'))
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
    fig, ax = plt.subplots(figsize=(7.5,5))
    plt.set_cmap('inferno')
    plt.plot(x2, y2,color = '0.1')
    plt.scatter(concs, DiffDiff,  color = 'orange', s = 30)
    plt.title(title + 'Michaelis Menten Plot')
    plt.ylabel('Difference in Abs')
    plt.xlabel('[Substrate] µM')
    plt.text(800,y2.max()/2,'Km = '+str(np.around(km,2))+'\n'\
    +'Vmax = '+str(np.around(vmax,2))+'\n'\
    +'R squared = '+str(np.around(r_sq,2)))
    if save:
        plt.savefig((title + ' Michaelis Menten PM.png').replace(' ','_'))
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


def return_metrics(DiffDiff,concs,title):
    vmax, km = calculate_Km(DiffDiff,concs)
    r_sq = r_squared(DiffDiff, concs, vmax,km)
    df = pd.DataFrame([[vmax,km,r_sq]],columns = ['vmax','Km','R^2'])
    df.index = [title]
    return df


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


concs = np.array([1,
0.5,
0.25,
0.125,
0.0625,
0.03125,
0.015625,
0.0078125])*1000

titles = ['protein and dmso',
'arachadnic acid 1','arachadnic acid 2',
'arachadnic acid 3','arachadnic acid 4',
'Lauric Acid 1','Lauric Acid 2',
'Lauric Acid 3','Lauric Acid 4',
'Palmitic acid 1','Palmitic acid 2',
'Lauric acid 3','Palmitic acid 4',
'4-Phenylimidazole 1','4-Phenylimidazole 2',
'4-Phenylimidazole 3','4-Phenylimidazole 4'
]


df = pd.DataFrame([],columns = ['vmax','Km','R^2'])
files = ['20190626_plate1.CSV','20190626_plate2.CSV','20190626_plate3.CSV']
BM3_stock_conc_titles = ['7.09 µM BM3 ','14.09 µM BM3 ','27.56 µM BM3 ']
metacount=0
for file in files:
    count=0
    titles = [BM3_stock_conc_titles[metacount]+i for i in titles]

    for i in range(1,len(titles)+1):

        data, pureprotein_andDMSO, diffdiff = Data_Munjing_pipeline(file,i)
        df =df.append(return_metrics(diffdiff,concs,titles[count]))
        #plotPlateData(data,titles[count],concs)
        #plotPlateDifferenceSpectra(data,pureprotein_andDMSO,titles[count],concs)
        #Plot_MichaelisMenten(diffdiff, concs,titles[count])
        count+=1
    metacount+=1
df.to_csv('201990626_BM3Concs_MetricsAndStuff.csv')
