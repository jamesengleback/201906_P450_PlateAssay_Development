import os
import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt

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

