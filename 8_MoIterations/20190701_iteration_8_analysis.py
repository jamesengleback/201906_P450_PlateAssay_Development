import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
#import torch

data = pd.read_csv('201990626_BM3Concs_MetricsAndStuff.csv')
data.drop(data.loc[data['R^2']==-np.inf].index,inplace=True)
data.drop(data.loc[data['vmax']>1e4].index,inplace=True)

x = data['vmax']
y=data['R^2']
km = data['Km']
protconcs=data['Unnamed: 0'].str.split('µ',expand=True).loc[:,0].astype(float)

plt.set_cmap('cool')
plt.scatter(x,y,c=protconcs)
plt.xlabel('Vmax (sort of normalised)')
plt.ylabel('R^2')
plt.colorbar(label='Protein conc /µM')
plt.title('Does my assay have a Sensitivity \
issue?')
plt.show()
#plt.savefig('plateassaymetricsplot_2.png')
