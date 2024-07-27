import json
import logging
import os
import pandas as pd

from . import metrics, mm


def process_block(test_wells,
                  control_wells=None,
                  concs=None,
                  ):

    # subtract controls
    if control_wells is not None:
        corrected_wells = test_wells.reset_index(drop=True).subtract(control_wells.reset_index(drop=True))
    else:
        corrected_wells = test_wells

    # 0 at A800
    corrected_wells = corrected_wells.subtract(corrected_wells[800], axis=0)

    # subtract zero conc trace
    diff_wells = corrected_wells.subtract(corrected_wells.loc[0, :], axis=1)
    response = mm.calculate_response(diff_wells)
    vmax, km = mm.calculate_km(response, response.index)
    #rsq = mm.r_squared(response[::-1], mm.curve(concs, vmax, km))
    rsq = mm.r_squared(response, mm.curve(concs, vmax, km))
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

    # logging.info(' '.join([f'{i} = {j:.2f}' for i, j in zip(block_summary.keys(), block_summary.values())]))

    return block_summary
