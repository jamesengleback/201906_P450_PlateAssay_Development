import json
import logging
import os
import pandas as pd

from . import metrics, mm
from .plot import plot_group


def process_block(test_wells,
                  control_wells=None,
                  concs=None,
                  plot=False,
                  **variables,
                  ):

    test_wells.index = concs
    test_wells = test_wells.sort_index()

    if control_wells is not None:
        control_wells.index = concs
        control_wells = control_wells.sort_index()
        # subtract controls
        corrected_wells = test_wells.subtract(control_wells)
    else:
        corrected_wells = test_wells

    # 0 at A800
    corrected_wells = corrected_wells.subtract(corrected_wells[800], axis=0)
    corrected_wells = corrected_wells.sort_index()

    # subtract zero conc trace
    diff_wells = corrected_wells.subtract(corrected_wells.loc[0, :], axis=1)
    response = mm.calculate_response(diff_wells)
    vmax, km = mm.calculate_km(response, response.index)
    #rsq = mm.r_squared(response[::-1], mm.curve(concs, vmax, km))
    rsq = mm.r_squared(response, mm.curve(response.index, vmax, km))
    a420_max = corrected_wells.loc[:, 420].max()
    auc = metrics.auc(corrected_wells)
    auc_mean = auc.mean()
    auc_cv = auc.std() / auc_mean
    std_405 = metrics.std_405(corrected_wells)
    dd_soret = metrics.dd_soret(diff_wells)

    block_summary = {
             'km': km,
             'vmax': vmax,
             'rsq': rsq,
             'a420_max': a420_max,
             'auc_mean': auc_mean,
             'auc_cv': auc_cv,
             'std_405': std_405,
             'dd_soret': dd_soret,
             }

    if plot:
        fig = plot_group(control_data=control_wells,
                         raw_data=test_wells,
                         corrected_data=corrected_wells,
                         diff_data=diff_wells,
                         #concs=concs,
                         ligand=variables.get('ligand'),
                         response=response,
                         suptitle = f"UV-Visible Absorbance Profile of BM3 in Response to {variables.get('ligand')}",
                         vmax=vmax,
                         km=km,
                         rsq=rsq,
                         a420_max=a420_max,
                         table_data=variables,
                         )

        block_summary['fig'] = fig
    # logging.info(' '.join([f'{i} = {j:.2f}' for i, j in zip(block_summary.keys(), block_summary.values())]))

    return block_summary
