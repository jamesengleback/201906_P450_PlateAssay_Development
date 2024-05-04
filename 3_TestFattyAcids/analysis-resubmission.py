import os
from string import ascii_uppercase
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
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



def calculate_response(data):
    return data.loc[:, 390].abs() + data.loc[:, 420].abs() 

def curve(x, vmax, km):
    y = (vmax*x)/(km + x)
    return y

def calculate_km(response, concs):
    params, cov = optimize.curve_fit(curve, 
                                     concs, 
                                     response, 
                                     p0=[max(response), 250],
                                     )
    vmax = params[0]
    km = params[1]
    return vmax, km

def r_squared(y, y_hat):
    residuals = y - y_hat
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((y-np.mean(y))**2)
    r_squared = 1 - (ss_res / ss_tot)
    return r_squared


def plot_plate_data(data,
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
        colors = plt.cm.inferno(np.linspace(0, 1, len(data)))
    else:
        colors = plt.cm.inferno(np.linspace(0, 1, len(data)))

    for i, j in enumerate(data.index):
        y = data.loc[j,:]
        ax.plot(x,
                y, 
                lw=2, 
                color=colors[i],
                label=round(concs[i], 2) if concs is not None else None,
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
            ax.legend([round(i, 2) for i in concs], 
                      title = f'{ligand_name} concentration μM',
                      loc='right',
                      )
        else:
            ax.legend([round(i, 2) for i in concs], 
                      title = 'Concentration μM',
                      loc='right',
                      )

def plot_michaelis_menten(response,
                          concs,
                          ax=None,
                          vmax=None,
                          km=None,
                          r_squared=None,
                          title=None,
                          ylim=None,
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
    if ylim is None:
        ylim = (-0.1, 1)
    ax.set_ylim(ylim)
    if km is not None:
        ax.text(400, ylim[1] * 0.5,  f'Km = {round(km, 2)}')
    if vmax is not None:
        ax.text(400, ylim[1] * 0.4,  f'Vmax = {round(vmax, 2)}')
    if r_squared is not None:
        ax.text(400, ylim[1] * 0.3,  f'R squared = {round(r_squared, 2)}')

    if title is not None:
        ax.set_title(title)

def main():
    # 20190607_SubstrateWeighing.csv
    # 20190609BM3ConcCheck.csv
    # 20190607_BM3conccheck.csv

    # plates
    # SerialDilfattyacids.CSV
    # SerialDilSchem2.2.CSV
    # SerialDilSchem2.CSV

    experiments = {
            'plate_1':{
                'path': 'SerialDilfattyacids.CSV',
                'columns':{
                    1: 'Buffer',
                    2: 'Protein',
                    3: 'Lauric Acid',
                    4: 'Lauric Acid',
                    5: 'Lauric Acid',
                    6: 'Lauric Acid',
                    7: 'Lauric Acid',
                    8: 'Arachadionic Acid',
                    9: 'Arachadionic Acid',
                    10: 'Arachadionic Acid',
                    11: 'Arachadionic Acid',
                    12: 'Arachadionic Acid',
                    13: 'Arachadionic Acid',
                    14: '4-Phenylimidazole',
                    15: '4-Phenylimidazole',
                    16: '4-Phenylimidazole',
                    17: '4-Phenylimidazole',
                    }
                },
            'plate_2':{
                'path': 'SerialDilSchem2.CSV',
                'columns':{
                    10: 'Buffer',
                    11: 'Protein',
                    12: 'Protein and DMSO',
                    13: 'Lauric Acid',
                    14: 'Arachadionic Acid',
                    15: '4-Phenylimidazole',
                    16: 'Sodium Dodecyl Sulfate',
                    }
                }
            }
    if not os.path.exists('img'):
        os.mkdir('img')

    test_rows = ascii_uppercase[:16][::2]
    control_rows = ascii_uppercase[:16][1::2]
    concs_rev = np.array([500 / i**2 for i in range(1,8)] + [0])
    concs = concs_rev[::-1]

    o = []
    for key in experiments.keys():
        path = experiments[key]['path']
        columns = experiments[key]['columns']
        data = getPlateData(path)
        for col_num in columns.keys():
            treatment = columns[col_num]
            data_chunk_rev = data.loc[data.index.str.contains(f'[A-Z]{col_num}$'), :]
            data_chunk = data_chunk_rev.loc[data_chunk_rev.index[::-1], :]
            data_chunk_test = data_chunk.loc[data_chunk.index.str.contains(f'[{"".join(test_rows)}]'), :]
            data_chunk_control = data_chunk.loc[data_chunk.index.str.contains(f'[{"".join(control_rows)}]'), :]
            data_chunk_corrected = data_chunk_test.reset_index(drop=True).subtract(data_chunk_control.reset_index(drop=True),
                                                                                   axis=0)
            data_chunk_corrected_diff = data_chunk_corrected.subtract(data_chunk_corrected.iloc[0, :],
                                                                      axis=1)
            response = calculate_response(data_chunk_corrected_diff)
            vmax, km = calculate_km(response, concs)
            y_hat = curve(x=concs, km=km, vmax=vmax)
            rsq = r_squared(y_hat, response)

            o.append({'plate': key,
                      'column': col_num,
                      'ligand': treatment,
                      'km': km,
                      'vmax': vmax,
                      'rsq': rsq,
                      })

            fig, axs = plt.subplots(2, 2, figsize=(16,8))
            plot_plate_data(data_chunk_test,
                            ax=axs[0,0],
                            concs=concs if key not in ['Protein', 'Buffer'] else None,
                            title=f'Absorbance Traces for P450 BM3 with {treatment}',
                            )

            plot_plate_data(data_chunk_corrected,
                            ax=axs[0,1],
                            concs=concs if key not in ['Protein', 'Buffer'] else None,
                            title=f'Control-Corrected Absorbance Traces for P450 BM3 with {treatment}',
                            )

            plot_plate_data(data_chunk_corrected_diff,
                            ax=axs[1,0],
                            concs=concs if key not in ['Protein', 'Buffer'] else None,
                            title=f'Difference Traces for P450 BM3 with {treatment}',
                            ylim=(-0.2, 0.2),
                            )
            if treatment in ['Protein', 'Buffer']:
                axs[1, 1].axis('off')
            else:
                plot_michaelis_menten(response=response,
                                      concs=concs,
                                      ax=axs[1, 1],
                                      km=km,
                                      r_squared=rsq,
                                      vmax=vmax,
                                      ylim=(-0.01, vmax*1.2),
                                      title=f'Michaelis-Menten Model for P450 BM3 and {treatment}',
                                      )

            fig.suptitle(f'Experiment 3: P450 BM3 Wild Type and {treatment}')
            plt.tight_layout()
            plt.savefig(os.path.join('img', 
                                     f'3_{key}-{treatment}-column-{col_num}.png'
                                     ))
            plt.close()
    df = pd.DataFrame(o)
    df = df.loc[df['column'] != 8, :] # anomaly - mis-dispensed compoun

    df_mean = df.groupby(['ligand']).mean()[['km', 'vmax', 'rsq']]
    df_std = df.groupby(['ligand']).std()[['km', 'vmax', 'rsq']]
    x = pd.DataFrame([], index=df_mean.index)
    for i in df_mean.columns:
       x[f'{i} Mean'] = df_mean[i]
       x[f'{i} Std'] = df_std[i]
    x.drop(['Protein', 'Protein and DMSO', 'Buffer'], inplace=True)
    x = x.round(2)

    print(x.to_markdown())

if __name__ == "__main__":
    main()
