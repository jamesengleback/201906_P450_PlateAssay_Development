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

def plotPlateData(data,
				  title=None,
				  ligand_name=None,
				  save_path=None,
				  concs=None,
				  ax=None,
                  ylim=None,
                  ):
    x = data.columns.astype(int)

    if ax is None:
        fig, ax = plt.subplots(figsize=(15,5))

    if concs is not None:
        colors = plt.cm.inferno((concs - min(concs))/max(concs))
    else:
        colors = plt.cm.inferno(np.linspace(0, 1, len(data)))

    for i, j in enumerate(data.index):
        y = data.loc[j,:]
        ax.plot(x,
                y, 
                lw=2, 
                color=colors[i],
                label=concs[i] if concs is not None else None,
                )
    if title is not None:
        ax.set_title(title)
    ax.set_xticks(x[::50])
    ax.set_xlim((220,800))
    if ylim is None:
        ax.set_ylim((-0.05,1))
    else:
        ax.set_ylim(ylim)
    ax.set_xlabel('Wavlength nm')
    ax.set_ylabel('Absorbance')
    if concs is not None:
        if ligand_name is not None:
            ax.legend(concs, 
                      title = f'{ligand_name} concentration μM',
                      loc='right',
                      )
        else:
            ax.legend(concs, 
                      title = 'Concentration μM',
                      loc='right',
                      )


def calculate_response(data):
    return data.loc[:, 390].abs() + data.loc[:, 420].abs() 

def curve(x, vmax, km):
    y = (vmax*x)/(km + x)
    return y

def calculate_km(DiffDiff,concs):
    params, cov = optimize.curve_fit(curve, concs, DiffDiff,
                                                   p0=[2, 2])
    vmax = params[0]
    km = params[1]
    return vmax, km

def r_squared(y, y_hat):
    residuals = y - y_hat
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((y-np.mean(y))**2)
    r_squared = 1 - (ss_res / ss_tot)
    return r_squared

def Plot_MichaelisMenten(response,
                         concs,
                         ax=None,
                         vmax=None,
                         km=None,
                         r_squared=None,
                         title=None,
                         ):
    x_2 = np.linspace(0,concs.max(), 500)
    y_hat = curve(x_2,
                  vmax, 
                  km,
                  )

    plt.set_cmap('inferno')
    if ax is None:
        fig, ax = plt.subplots(figsize=(7.5,5))
    ax.plot(x_2, y_hat, color = '0.1')
    ax.scatter(concs, response,  color = 'orange', s = 30)
    ax.set_ylabel('Difference in Abs')
    ax.set_xlabel('[Substrate] µM')
    ax.set_ylim((-0.1, 1))
    if km is not None:
        ax.text(400, 0.2,  f'Km = {round(km, 2)}')
    if vmax is not None:
        ax.text(400, 0.15,  f'Vmax = {round(vmax, 2)}')
    if r_squared is not None:
        ax.text(400, 0.1,  f'R squared = {round(r_squared, 2)}')

    if title is not None:
        ax.set_title(title)


def main():
    data = getPlateData('SerialDilSchem1.CSV')

    # looks lig I got the concs backwards
    concs = np.array([round(500 / i, 2) for i in range(1,8)] + [0])
    concs_rep = []
    for i in concs:
        concs_rep.append(i)
        concs_rep.append(i)

    experiments = {
            "buffer_col": {
                'data': data.loc[data.index.str.contains('[A-Z]4$'),:],
                'title':'Buffer Only',
                'save_path':'BufferOnly.png',
                },
            "protein_col": {
                'data': data.loc[data.index.str.contains('[A-Z]5$'),:],
                'title':'Protein Only',
                'save_path':'ProteinOnly.png',
                },
            "npg_2p5_col": {
                'data': data.loc[data.index.str.contains('[A-Z]6$'),:],
                'title': 'N-Palmitoglycine, [DMSO] 2.5% v/v',
                'ligand': 'N-Palmitoglycine',
                'save_path':'NPG-2p5pct.png',
                },
            "lauric_5_col": {
                'data': data.loc[data.index.str.contains('[A-Z]7$'),:],
                'title':'Lauric Acid, [DMSO] 5% v/v',
                'ligand': 'Lauric Acid',
                'save_path':'LauricAcid5pct.png',
                },
            "npg_50_col": {
                'data': data.loc[data.index.str.contains('[A-Z]8$'),:],
                'title':'N-Palmitoglycine, [DMSO] 5% v/v',
                'ligand':'N-Palmitoglycine',
                'save_path':'NPG-5pct.png',
                },
            "lauric_25_col": {
                'data': data.loc[data.index.str.contains('[A-Z]9$'),:],
                'title':'Lauric Acid, [DMSO] 2.5% v/v',
                'ligand': 'Lauric Acid',
                'save_path':'LauricAcid-2p5pct.png',
                },
    }

    if not os.path.exists('img'):
        os.mkdir('img')

    buffer_col = experiments['buffer_col']['data']
    buffer_avg = buffer_col.mean(axis=0)

    protein_col = experiments['protein_col']['data']
    protein_avg = protein_col.mean(axis=0)

    for key in experiments:
        experiment_data = experiments[key]
        fig, axs = plt.subplots(2,2, figsize=(16,8))
        df = experiment_data.get('data')
        title = experiment_data.get('title')
        ligand = experiment_data.get('ligand')

        df_r1 = df.iloc[1::2, :]

        df_r1_corrected = df_r1 - buffer_avg
        # df_r1_corrected_diff = df_r1_corrected - df_r1_corrected.iloc[0,:]
        df_r1_corrected_diff = df_r1_corrected - protein_avg
        response = calculate_response(df_r1_corrected_diff)
        response.index = concs 
        vmax, km = calculate_km(response, response.index)
        rsq = r_squared(response, curve(concs, vmax, km))

        plotPlateData(data=df_r1,
                      title=title,
                      ligand_name=ligand,
                      concs=concs if key not in ['buffer_col', 'protein_col'] else None,
                      ax=axs[0,0],
                      )

        plotPlateData(data=df_r1_corrected,
                      title=f'{title} Buffer-Corrected Absorbance',
                      ligand_name=ligand,
                      concs=concs if key not in ['buffer_col', 'protein_col'] else None,
                      ax=axs[0,1],
                      )

        plotPlateData(data=df_r1_corrected_diff,
                      title=f'{title} $\Delta$ Absorbance',
                      ligand_name=ligand,
                      concs=concs if key not in ['buffer_col', 'protein_col'] else None,
                      ax=axs[1,0],
                      ylim=(-0.3, 0.3),
                      )

        if key not in ['buffer_col', 'protein_col']:
            Plot_MichaelisMenten(response=response, 
                                 concs=concs,
                                 km=km,
                                 vmax=vmax,
                                 r_squared=rsq,
                                 ax=axs[1, 1],
                                 title=f'{title} Michaelis Menten Model'
                                 )
        else:
            axs[1, 1].axis('off')

        if ligand is not None:
            fig.suptitle(f'Photspectroscopic Measurement of P450 BM3 with Additions of {ligand}')
        else:
            fig.suptitle(f'Photspectroscopic Measurement of $P450_BM3$')

        plt.tight_layout()
        #plt.show()
        plt.savefig(os.path.join('img', 
                                 f"2_{experiment_data['save_path']}",
                                 ),
                    )

    # Plot_MichaelisMenten(DiffDiff,concs)

if __name__ == "__main__":
    main()
