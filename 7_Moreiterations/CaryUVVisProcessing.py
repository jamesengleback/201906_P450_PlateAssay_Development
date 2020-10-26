import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


class dataset:
    def __init__(self, path):
        self.data = pd.read_csv(path)
        self.filename = path.rsplit('/',1)[-1]
        self.headers = pd.Series(self.data.columns)
        self.headers = self.headers.loc[self.headers.str.contains('Unnamed')==False]
        self.wavelengths = self.Get_Wavelengths()
        self.data = self.Get_numericalData() # throws away the metadata
        self.data = self.Zero_at_800()
        self.conc_labels = self.calc_conc()

    def Get_Wavelengths(self):
        wavelengths = self.data.iloc[:,0] # first column
        wavelengths = wavelengths[wavelengths.str.contains(r'\d\d\d.\d\d\d\d')].astype(float)
        # there's an integer in there somewhere!
        wavelengths = wavelengths.reset_index(drop=True).iloc[1:]
        # cba to sort this out now, I'm just going to plot it out of shift by one cell shit
        return wavelengths.reset_index(drop=True)

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

    def calc_conc(self):
        data = self.data
        data = data.loc[:,data.columns < 421]
        data = data.loc[:,data.columns > 419]
        A420 = data.iloc[:,0]
        ext = 95
        conc_mM = A420/ext
        conc_uM = conc_mM*1000
        conc_uM.reset_index(drop=True,inplace=True)
        conc_uM.name = 'P450 conc/uM'
        return conc_uM

    def plot_traces(self):
        data = self.data
        fig, ax = plt.subplots(figsize=(7,4))
        ax.set_prop_cycle('color',plt.cm.magma(np.linspace(0,0.9,len(data))))
        for i in range(len(data)):
            y = data.iloc[i,:]
            plt.plot(y, lw = 1)
        plt.xlim((250,800))
        plt.ylim((-0.1,1))
        plt.xticks(np.linspace(250,800,11))
        plt.xlabel('Wavlength nm')
        plt.ylabel('Absorbance')
        plt.legend(self.headers, title='P450 BM3 conc/uM')
        plt.title(self.filename)
        plt.savefig(self.filename+'RawSpec.png')
        #plt.show()


files = ['20190625_BM3conccheck.csv','20190625_BM3Lauric1.csv','20190625_BM3Lauric2.csv',
'20190625_BM3Lauric3centrifugepot.csv','20190625_BM3Palmiticcentrifugepot.csv','20190625_BM3Palmiticprecentrifugepot.csv']

for i in files:
    path = '~/Documents/Work/201906_PlateAssayDevelopment/7_Moreiterations/'+i

    Dataset = dataset(path)
    Dataset.plot_traces()
#print(Dataset.headers)
