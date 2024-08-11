import json
import logging
import os
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import curve_fit

from . import metrics, mm
from .plot import plot_group


def process_block(test_wells,
                  control_wells=None,
                  concs=None,
                  plot=False,
                  **variables,
                  ):

    # test_wells.reset_index(names='well', inplace=True)
    test_wells = test_wells.copy()
    test_well_addresses = test_wells.index
    test_wells.index = concs
    test_wells = test_wells.sort_index()

    # 0 at A800
    test_wells_norm = test_wells.subtract(test_wells[800], axis=0)

    # smooth traces
    test_wells_norm_smooth = pd.DataFrame(gaussian_filter1d(test_wells_norm.loc[:, 280:],
                                                            sigma=5,
                                                            axis=1,
                                                            ),
                                          columns=test_wells_norm.loc[:, 280:].columns,
                                          index=test_wells_norm.index,
                                          )

    if control_wells is not None:
        # control_wells.reset_index(names='well', inplace=True)
        control_wells = control_wells.copy()
        control_well_addresses = control_wells.index
        control_wells.index = concs
        control_wells = control_wells.sort_index()
        # 0 at A800
        control_wells_norm = control_wells.subtract(control_wells[800], axis=0)
        # smooth traces
        control_wells_norm_smooth = pd.DataFrame(gaussian_filter1d(control_wells_norm.loc[:, 280:],
                                                                sigma=5,
                                                                axis=1,
                                                                ),
                                                  columns=control_wells_norm.loc[:, 280:].columns,
                                                  index=control_wells_norm.index,
                                                  )

        # subtract controls
        corrected_wells = test_wells_norm_smooth.subtract(control_wells_norm_smooth)
    else:
        control_wells_norm = None
        corrected_wells = test_wells

    control_well_summary = well_summary(data_raw=control_wells,
                                        data_norm=control_wells_norm,
                                        data_norm_smooth=control_wells_norm_smooth,
                                        data_corrected=corrected_wells,
                                        )

    if control_wells is not None and 'control_well_addresses' in locals():
        control_well_summary.index = control_well_addresses


    test_well_summary = well_summary(data_raw=test_wells,
                                     data_norm=test_wells_norm,
                                     data_norm_smooth=test_wells_norm_smooth,
                                     data_corrected=corrected_wells,
                                     )

    test_well_summary['address'] = test_well_addresses
    test_well_summary['concentration'] = concs


    # 0 at A800
    # corrected_wells = corrected_wells.subtract(corrected_wells[800], axis=0)
    # corrected_wells = corrected_wells.sort_index()


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
             'test_well_summary': test_well_summary.to_dict() if 'test_well_summary' in locals() else None,
             'control_well_summary': control_well_summary.to_dict() if 'control_well_summary' in locals() else None,
             }

    if plot:
        fig = plot_group(test_data_raw=test_wells,
                         control_data_raw=control_wells,
                         control_data_norm=control_wells_norm,
                         test_data_norm=test_wells_norm,
                         test_data_smooth=test_wells_norm_smooth,
                         control_data_smooth=control_wells_norm_smooth,
                         corrected_data=corrected_wells,
                         diff_data=diff_wells,
                         test_well_addresses=test_well_addresses,
                         control_well_addresses=control_well_addresses,
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

    return block_summary


def well_summary(data_raw=None,
                 data_norm=None,
                 data_norm_smooth=None,
                 data_corrected=None,
                 ):


    columns = []

    if data_raw is not None:
        a_800 = data_raw.loc[:, 800].reset_index(drop=True)
        a_800.name = 'a_800'
        columns.append(a_800)

    if data_norm is not None:
        pass

    if data_norm_smooth is not None:
        auc = pd.Series(np.trapz(data_norm_smooth.loc[:, 300:], axis=1))
        auc.name = 'auc'
        columns.append(auc)

        rsqs = []
        ks = []

        for _, row in data_norm_smooth.iterrows():
            (k,), cov = curve_fit(metrics.scatter,
                                 xdata=row.index,
                                 ydata=row
                                 )
            y_pred = pd.Series(metrics.scatter(row.index, k), index=row.index)
            rsq = mm.r_squared(row, y_pred)
            rsqs.append(rsq)
            ks.append(k)

        ks = pd.Series(ks, name='k')
        rsqs = pd.Series(rsqs, name='r_squared')

        columns.append(ks)
        columns.append(rsqs)


    if data_corrected is not None:
        pass

    df = pd.concat(columns, axis=1)
    return df
