import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse
import torch
import torch.nn as nn
import tabulatehelper as th
from tqdm import tqdm

def argParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', nargs=1, help='trace')
    parser.add_argument('-s', help='save?',action="store_true")
    parser.add_argument('-m', help='manual input?',action="store_true")
    args=parser.parse_args()
    return args

class dataset:
    def __init__(self, path, m):
        self.path=path
        self.data = pd.read_csv(path)
        self.headers = self.data.columns
        self.wavelengths = self.Get_Wavelengths()
        self.data = self.Get_numericalData() # throws away the metadata
        self.data = self.Zero_at_800()
        if m:
            self.concs=self.Get_concs_manually()
        else:
            self.concs=self.Get_concs_automatically()
        self.diff = self.Get_Diff()
        self.diffdiff = self.Get_DiffDiff()
        self.vmax, self.km = self.Calculate_KM()


    def Get_Wavelengths(self):
        wavelengths = self.data.iloc[:,0] # first column
        wavelengths = wavelengths[wavelengths.str.contains(r'\d\d\d.\d\d\d\d')].astype(float)
        # there's an integer in there somewhere!
        wavelengths = wavelengths.reset_index(drop=True).iloc[1:]
        # cba to sort this out now, I'm just going to plot it out of shift by one cell shit
        return wavelengths.reset_index(drop=True)

    def Get_concs_manually(self):
        labels=self.headers[0::2][:-1]
        print('Manual concentration input')
        vols=[]
        for i in labels:
            print(i,'\t')
            x=input('Input:     ')
            vols.append(x)
        vols=pd.Series(concs).astype(float)

        # Now calculate the concentrations
        # c2 = (v1*c1)/v2
        # v2 = 1ml = 1000 ul
        # c1 = 10 mM = 10000 uM
        concs = (vols*1e4)/1e3
        return concs

    def Get_concs_automatically(self):
        labels=self.headers[0::2][:-1]
        labels=labels.str.findall(r"\d+\.\d+")

        vols=[]
        for i in labels:
            if len(i)!=0:
                vols.append(float(i[0]))
            else:
                vols.append(0)
        vols=pd.Series(vols)
        # Now calculate the concentrations
        # c2 = (v1*c1)/v2
        # v2 = 1ml = 1000 ul
        # c1 = 10 mM = 10000 uM
        concs = (vols*1e4)/1e3
        return concs

    def Get_numericalData(self):
        data = self.data
        data.columns = data.iloc[0,:]
        data = data.iloc[self.wavelengths.index,:].dropna(axis = 1)
        data = data.drop('Wavelength (nm)', axis = 1)
        data = data.iloc[1:,:] #drops strinds
        data.reset_index(inplace=True,drop=True)
        return data

    def Zero_at_800(self):
        data = self.data.astype(float)
        data = data.transpose()
        data.columns = self.wavelengths[:-1]
        zero_vals = data.iloc[:,0] # starts with 800
        data = data.subtract(zero_vals,axis=0)
        return data

    def Get_Diff(self):
        data=self.data
        data.index=self.headers[0::2][:-1]# last value is a dud
        diff=data.subtract(data.iloc[1,:])
        return diff

    def Get_DiffDiff(self):
        data=self.data
        data.columns=np.around(data.columns,0).astype(int)
        DiffA420=data.loc[:,420]
        DiffA390=data.loc[:,390]
        DiffDiff = DiffA390-DiffA420
        #Normalize too
        DiffDiff -= DiffDiff.min()
        DiffDiff /= DiffDiff.max()
        return DiffDiff

    def curve(self, x, vmax, km):
        y = (vmax*x)/(km + x)
        return y

    def Calculate_KM(self):
        params = torch.randn((2,1),dtype=torch.float, requires_grad=True)
        x=torch.tensor(self.concs.values,dtype=torch.float).unsqueeze(1)
        y=torch.tensor(self.diffdiff.values,dtype=torch.float).unsqueeze(1)

        loss_function  = nn.MSELoss()
        optimizer = torch.optim.Adam({params}, lr = 1e-1)

        lossrecord=[]
        for i in tqdm(range(1000)):
            yhat = self.curve(x,params[0],params[1])
            loss = loss_function(yhat, y)
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
            lossrecord.append(loss.data.numpy())

        print('MSE Loss  = ',loss.item())
        vmax = params[0]
        km = params[1]
        return vmax, km

    def r_squared(self):
        diffdiff = torch.tensor(self.diffdiff.values, dtype=torch.float)
        concs=torch.tensor(self.concs.values, dtype=torch.float)
        residuals = diffdiff -  self.curve(concs, self.vmax, self.km)
        ss_res = torch.sum(residuals**2)
        ss_tot = torch.sum(diffdiff-(diffdiff.mean()**2))
        r_squared = 1 - (ss_res / ss_tot)
        return r_squared


    def plot_traces(self,save):
        data = self.data
        fig, ax = plt.subplots(figsize=(15,5))
        ax.set_prop_cycle('color',plt.cm.inferno(np.linspace(0,0.9,len(data))))
        for i in range(len(data)):
            y = data.iloc[i,:]
            plt.plot(y, lw = 1)
        plt.xlim((250,800))
        plt.ylim((-0.1,0.5))
        plt.xticks(np.linspace(250,800,11))
        plt.xlabel('Wavlength nm')
        plt.ylabel('Absorbance')
        plt.legend(self.concs, title='Substrate conc/uM')
        plt.title(self.path+'Plot.png')
        if save:
            plt.savefig(self.path+'Plot.png')
        else:
            plt.show()

    def plot_difference(self,save):
        data = self.diff
        fig, ax = plt.subplots(figsize=(15,5))
        ax.set_prop_cycle('color',plt.cm.inferno(np.linspace(0,0.9,len(data))))
        for i in range(len(data)):
            y = data.iloc[i,:]
            plt.plot(y, lw = 1)

        plt.xlim((250,800))
        plt.ylim((-0.1,0.1))
        plt.xticks(np.linspace(250,800,11))
        plt.xlabel('Wavlength nm')
        plt.ylabel('Absorbance')
        plt.legend(self.concs, title='Substrate conc/uM')
        plt.title(self.path+'Difference_Plot.png')
        if save:
            plt.savefig(self.path+'Difference_Plot.png')
        else:
            plt.show()

    def Plot_MichaelisMenten(self,save):
        x2=np.linspace(0,self.concs.max(), 500)
        x2 = torch.tensor(x2,dtype=torch.float)
        y2 = self.curve(x2, self.vmax, self.km)
        r_sq = self.r_squared()

        pos1 = y2.max()
        pos2 = pos1 - 7*(y2.max()-y2.min())/8

        fig, ax = plt.subplots(figsize=(7.5,5))
        plt.set_cmap('inferno')
        plt.plot(x2.detach().numpy(), y2.detach().numpy(),color = '0.1')

        plt.scatter(self.concs, self.diffdiff,  color = 'orange', s = 30)
        plt.title(self.path + 'Michaelis Menten Plot')
        plt.ylabel('Difference in Abs')
        plt.xlabel('[Substrate] uM')
        plt.text(800,y2.max()/2,'Km = '+str(np.around(self.km.detach().numpy(),2))+'\n'\
        +'Vmax = '+str(np.around(self.vmax.detach().numpy(),2))+'\n'\
        +'R squared = '+str(np.around(r_sq.detach().numpy(),2)))
        if save:
            plt.savefig(self.path+'MichaelisMenten_Plot.png')
            plt.close()
        else:
            plt.show()

    def modify_filenames(self,filename):
        return '![](titrations/'+filename+')'

    def save_and_make_markdown(self):
        self.plot_traces(True)
        self.plot_difference(True)
        self.Plot_MichaelisMenten(True)
        df=pd.DataFrame([[self.modify_filenames(self.path+'Plot.png'),
        self.modify_filenames(self.path+'Difference_Plot.png'),
        self.modify_filenames(self.path+'MichaelisMenten_Plot.png')]],
        columns=['Raw Spec','Difference Spec', 'Michaelis Menten'])
        df.index=[self.path]
        metrix_table = th.md_table(df,showindex=True)
        print(metrix_table)

def main():
    args=argParser()
    Dataset = dataset(args.i[0],args.m)
    if args.s:
        Dataset.save_and_make_markdown()
    else:
        Dataset.plot_traces(False)
        Dataset.plot_difference(False)
        Dataset.Plot_MichaelisMenten(False)
main()
