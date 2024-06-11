import os
from textwrap import dedent
import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt
from .mm import curve
import matplotlib.patches as mpatches


def plot_plate_data(data,
                    title=None,
                    ligand_name=None,
                    save_path=None,
                    concs=None,
                    ax=None,
                    ylim=None,
                    legend_text=None,
                    ):
    x = data.columns.astype(int)

    if ax is None:
        fig, ax = plt.subplots(figsize=(15,5))

    if concs is not None:
        # colors = plt.cm.inferno((concs - min(concs))/max(concs))
        if concs.argmax() == 0:
            colors = plt.cm.inferno(np.linspace(1, 0, len(data)))
        else:
            colors = plt.cm.inferno(np.linspace(0, 1, len(data)))
    else:
        colors = plt.cm.inferno(np.linspace(0, 1, len(data)))

    for i, j in enumerate(data.index):
        y = data.loc[j,:]
        ax.plot(x,
                y, 
                lw=2, 
                color=colors[i],
                label=round(concs[i], 2) if concs is not None else y.index,
                )
    if title is not None:
        ax.set_title(title)

    if ylim is None:
        ax.set_ylim((-0.05,1))
    else:
        ax.set_ylim(ylim)


    ax.set_xticks(x[::50])
    ax.set_xlim((280,800))
    ax.set_xlabel('Wavlength nm')
    ax.set_ylabel('Absorbance')

    if concs is not None:
        if ligand_name is not None:
            if legend_text is not None:
                handles, labels = ax.get_legend_handles_labels()
                handles.append(mpatches.Patch(color='none', label=legend_text))
            else:
                handles = None
            ax.legend([round(i, 2) for i in concs], 
                      title = f'{ligand_name} concentration μM',
                      loc='right',
                      handles=handles,
                      )
        else:
            ax.legend([round(i, 2) for i in concs], 
                      title = 'Concentration μM',
                      loc='right',
                      )
    if ax is None and save_path is not None:
        assert 'fig' in locals()
        fig.savefig(save_path)

def plot_michaelis_menten(response,
                          concs,
                          ax=None,
                          vmax=None,
                          km=None,
                          r_squared=None,
                          title=None,
                          ylim=None,
                          legend_text=None,
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

    if title is not None:
        ax.set_title(title)

    if ylim is None:
        ylim = (-0.1, 1)

    ax.set_ylim(ylim)

    label = dedent(f'''
           Km = {round(km, 2)}
           Vmax = {round(vmax, 2)}
           R squared = {round(r_squared, 2)}
           ''')
    handles, labels = ax.get_legend_handles_labels()
    handles.append(mpatches.Patch(color='none', label=label))
    if legend_text:
        handles.append(mpatches.Patch(color='none', label=legend_text))
    ax.legend(handles=handles,
              loc='right',
              )

    if title is not None:
        ax.set_title(title)

