import math
import json
import os
import re
from string import ascii_uppercase
import argparse
import logging

import click
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import utils

logging.basicConfig(level=logging.INFO)

def plot_group(raw_data=None,
               control_data=None,
               corrected_data=None,
               diff_data=None,
               concs=None,
               ligand=None,
               response=None,
               vmax=None,
               km=None,
               rsq=None,
               a420_max=None,
               suptitle=None,
               show=None,
               save_path=None,
               legend_text=None,
               table_data=None,
               ):
    fig, axs = plt.subplots(3, 2, figsize=(16,12))
    next_ax = iter(axs.flatten())

    if control_data is not None:
        utils.plot.plot_plate_data(control_data.sort_index(ascending=False),
                                   ax=next(next_ax),
                                   concs=concs[::-1] if concs is not None else None,
                                   ligand_name=ligand,
                                   title='Control Data',
                                   ylim=(-0.1, max(0.3, 1.2 * a420_max) if a420_max else None),
                                   )

    if raw_data is not None:
        utils.plot.plot_plate_data(raw_data.sort_index(ascending=False),
                                   ax=next(next_ax),
                                   concs=concs[::-1] if concs is not None else None,
                                   ligand_name=ligand,
                                   title='Raw Test Data',
                                   ylim=(-0.1, max(0.3, 1.2 * a420_max)) if a420_max else None,
                                   )

    if corrected_data is not None:
        utils.plot.plot_plate_data(corrected_data.sort_index(ascending=False),
                                   ax=next(next_ax),
                                   ligand_name=ligand,
                                   concs=concs[::-1] if concs is not None else None,
                                   title='Corrected Test Data',
                                   ylim=(-0.1, max(0.3, 1.2 * a420_max)) if a420_max else None,
                                   )

    if diff_data is not None:
        utils.plot.plot_plate_data(diff_data.sort_index(ascending=False),
                                   ax=next(next_ax),
                                   concs=concs[::-1] if concs is not None else None,
                                   ligand_name=ligand,
                                   title='$\Delta$ Absorbance',
                                   ylim=(-0.3, max(0.3, 1.2 * a420_max)) if a420_max else None,
                                   )

    if ligand and response is not None:
        utils.plot.plot_michaelis_menten(response=response,
                                         concs=concs,
                                         vmax=vmax,
                                         km=km,
                                         r_squared=rsq,
                                         ax=next(next_ax),
                                         ylim=(0, max((vmax * 1.2), max(response) * 1.2)),
                                         legend_text=legend_text,
                                         title='Response'
                                         )
    # else:
    #     if legend_text is not None:
    #         handles, labels = axs[2, 0].get_legend_handles_labels()
    #         handles.append(mpatches.Patch(color='none', label=legend_text))
    #         axs[2, 0].legend(handles=handles,
    #                          loc='right',
    #                          )

    if table_data is not None:
        assert isinstance(table_data, dict)
        ax = next(next_ax)
        fmt_labels = lambda s : ' '.join([i.capitalize() for i in s.split('_')])
        ax.table(cellText=[[i] for i in table_data.values()],
                 rowLabels=[fmt_labels(i) for i in table_data.keys()],
                 bbox=[0.4, 0.2, 0.4, 0.6],
                 # colWidths=[0.4],
                 cellLoc='left',
                 # loc='center',
                 edges='TBLR',
                 alpha=0.5,
                 fontsize=14,
                 )
        ax.axis('off')

    for ax in next_ax:
        ax.axis('off')

    if suptitle:
        plt.suptitle(suptitle)
    plt.tight_layout()

    if show:
        plt.show()
    else:
        assert save_path is not None
        assert os.path.exists(os.path.dirname(save_path))
        plt.savefig(save_path)
        plt.close()

@click.group()
def cli():
    pass


@click.command()
@click.argument('config_paths', nargs=-1)
@click.option('-p', '--plot', is_flag=True, type=bool, default=False)
@click.option('-s', '--show', is_flag=True, type=bool, default=False)
def echo(config_paths,
         plot,
         show,
         ):
    """ Analyse experiment directory from config json file
    """

    for config_path in config_paths:
        try:
            logging.info(config_path)

            working_directory = os.path.abspath(os.path.dirname(config_path))

            with open(config_path, 'r') as f:
                config_data = json.load(f)

            experiment_number = config_data["experiment_number"]

            working_directory = os.path.abspath(os.path.dirname(config_path))
            if plot:
                img_dir = os.path.join(working_directory, 'img')
                if not os.path.exists(img_dir):
                    os.mkdir(img_dir)

            constants = {i.lower(): j for i, j in zip(config_data.keys(),
                                              config_data.values(),
                                              ) if not isinstance(j, (list, dict))
                         }

            summary = []

            per_well_summary = []

            well_ids = {i:j for i, j in enumerate(
                [f'{k}{l}' for k in ascii_uppercase[:16] for l in range(1,25)],
                                        1)
                        }
            source_plate_contents = config_data.get('source_plate_contents')
            experiments = config_data.get('experiments')
            blocks = config_data.get('blocks')
            for experiment in experiments.keys():
                experiment_config = experiments[experiment]

                if blocks is None:
                    blocks = experiment_config.get('blocks')
                
                if (echo_log_path := experiment_config.get('echo_log')) is not None:
                    pass
                
                if (plate_data_path := experiment_config.get('file')) is not None:
                    plate_data_path = os.path.join(working_directory, plate_data_path)
                    logging.info(plate_data_path)
                    df = utils.bmg.parse_bmg(plate_data_path)
                    df = df.subtract(df[800], axis=0)
                    test_plate_contents = {i:{} for i in well_ids.values()}

                    for block_num, block in zip(blocks.keys(), blocks.values()):

                        independent_variables = constants | {i: block[i] for i in block if isinstance(block[i], (str, int, float))}

                        ligand = block.get('ligand') or experiment_config.get('ligand') or config_data.get('ligand')

                        logging.info(f'{experiment_number} {independent_variables.get("dispense_ligands")}  block {block_num} ligand {ligand}')

                        if (concs := block.get('concentrations')):
                            concs = np.array(concs)
                        else:
                            concs = experiment_config.get('concentrations') or config_data.get('concentrations')
                            if concs is not None: 
                                concs = np.array(concs)

                        test_data = df.loc[list(block['test_wells']), :]

                        control_wells = block.get('control_wells')
                        if control_wells:
                            control_data = df.loc[list(control_wells), :]
                            if control_data.isna().all().all():
                                controls_ok = False
                                control_data = control_data.fillna(0)
                            else:
                                controls_ok = True
                        else:
                            control_data = None
                            controls_ok = False

                        if control_wells:
                            corrected_data = test_data.reset_index(drop=True).subtract(control_data.reset_index(drop=True))
                        else:
                            corrected_data = test_data

                        if concs is not None:
                            corrected_data = corrected_data.sort_index()
                            diff_data = corrected_data.subtract(corrected_data.loc[0, :], axis=1)
                            response = utils.mm.calculate_response(diff_data)

                            try:
                                vmax, km = utils.mm.calculate_km(response, response.index)
                            except:
                                vmax, km = None, None

                            rsq = utils.mm.r_squared(response, utils.mm.curve(concs, vmax, km))
                        else:
                            rsq, vmax, km, diff_data, response = None, None, None, None, None

                        a420_max = corrected_data.loc[:, 420].max()
                        auc = utils.metrics.auc(corrected_data)
                        auc_mean = auc.mean()
                        auc_cv = auc.std() / auc_mean
                        std_405 = utils.metrics.std_405(corrected_data)

                        if diff_data is not None:
                            dd_soret = utils.metrics.dd_soret(diff_data)
                        else:
                            dd_soret = None


                        for idx, (test_i, conc) in enumerate(zip(test_data.index,
                                                                    concs,
                                                                    )
                                                                ):
                            test_row = test_data.loc[test_i, :].to_dict()
                            per_well_summary.append({**test_row,
                                                     **independent_variables,
                                                     'experiment_number': experiment_number,
                                                     'ligand': ligand,
                                                     'concentration': conc,
                                                     'experiment_number': experiment_number,
                                                     'control': False,
                                                     'address': test_i,
                                                     **{i:block[i] for i in block.keys() if 'wells' not in i},
                                                     }
                                                    )


                        if control_data is not None:
                            for idx, (control_i, conc) in enumerate(zip(control_data.index,
                                                                        concs,
                                                                        )
                                                                    ):

                                control_row = control_data.loc[control_i, :].to_dict()
                                per_well_summary.append({**control_row,
                                                         **independent_variables,
                                                         'experiment_number': experiment_number,
                                                         'ligand': ligand,
                                                         'concentration': conc,
                                                         'control': True,
                                                         'address': control_i,
                                                         'experiment_number': experiment_number,
                                                         **{i:block[i] for i in block.keys() if 'wells' not in i},
                                                         }
                                                        )

                        summary.append({
                            'experiment_number': experiment_number,
                            'ligand': ligand,
                            'km': km,
                            'vmax': vmax,
                            'rsq': rsq,
                            'protein_concentration': config_data.get('protein_concentration') or 
                                                     experiment_config.get('protein_concentration') or 
                                                     block.get('protein_concentration') ,
                            'a420_max':a420_max,
                            'auc_mean': auc_mean,
                            'auc_cv': auc_cv,
                            'std_405': std_405,
                            'dd_soret': dd_soret,
                            **{i:block[i] for i in block.keys() if 'wells' not in i},
                            'controls_ok': controls_ok,
                            **independent_variables,
                            }
                                 )

                        if plot:
                            suptitle = f"UV-Visible Absorbance Profile of {experiment_config.get('protein_concentration')} μM P450 BM3 in Response to {ligand}"
                            save_path = os.path.join(img_dir,
                                                   f'{experiment}-block-{block_num}-ligand-{ligand}.png',
                                                   ) if 'img_dir' in locals() else None
                            plot_group(control_data=control_data,
                                       raw_data=test_data,
                                       corrected_data=corrected_data,
                                       diff_data=diff_data,
                                       concs=concs,
                                       ligand=ligand,
                                       response=response,
                                       vmax=vmax,
                                       km=km,
                                       rsq=rsq,
                                       a420_max=a420_max,
                                       suptitle=suptitle,
                                       show=show,
                                       save_path=save_path,
                                       table_data=independent_variables,
                                       )

            summary = pd.DataFrame(summary)
            summary.to_csv(os.path.join(working_directory,
                                        f'experiment-{experiment_number}-summary.csv'
                                        ), 
                           index=False)

            per_well_summary = pd.DataFrame(per_well_summary)
            per_well_summary.to_csv(os.path.join(working_directory,
                                        f'experiment-{experiment_number}-per-well-summary.csv'
                                        ), 
                           index=False)
        except Exception as e:
            logging.warn(f'{config_path} {e}')


    
@click.command()
@click.argument('config_paths', nargs=-1)
@click.option('-p', '--plot', is_flag=True, type=bool, default=False)
@click.option('-s', '--show', is_flag=True, type=bool, default=False)
def serial(config_paths,
           plot,
           show,
           ):
    """ Analyse experiment directory from config json file
        Assumig the serial dilution-type experiment design 
        from iterations 2-10
    """

    for config_path in config_paths:
        per_well_summary = []
        try:
            logging.info(config_path)
            working_directory = os.path.abspath(os.path.dirname(config_path))

            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            experiment_number = config_data["experiment_number"]

            constants = {i.lower(): j for i, j in zip(config_data.keys(),
                                              config_data.values(),
                                              ) if not isinstance(j, (list, dict))
                         }

            if plot:
                img_dir = os.path.join(working_directory, 'img')
                if not os.path.exists(img_dir):
                    os.mkdir(img_dir)

            test_rows = config_data['test_rows']
            control_rows = config_data['control_rows']
            concs = np.array(config_data['concentrations'])

            summary = []
            # order of concs is reversed (high at top of column)
            # so there's some messing here
            experiments = config_data.get('experiments')
            for plate_name in experiments.keys():


                experiment = experiments[plate_name]
                file_path = os.path.join(working_directory, experiment['file'])
                logging.info(file_path)
                img_dir = os.path.join(working_directory, 'img')
                columns = experiment['columns']

                experiment_constants = {i.lower(): j for i, j in zip(experiment.keys(),
                                                  experiment.values(),
                                                  ) if not isinstance(j, (list, dict))
                             }

                protein_concentration =  config_data.get('protein_concentration') 

                df = utils.bmg.parse_bmg(file_path)
                df = df.subtract(df[800], axis=0) # 800 nm correction

                for column_num in columns:

                    column_data = columns[column_num]
                    independent_variables = constants | experiment_constants | {i: column_data[i] for i in column_data if isinstance(column_data, dict) and isinstance(column_data[i], (str, int, float))}

                    if isinstance(column_data, str):
                        ligand = column_data  if column_data not in [
                                                                     'Protein',
                                                                     'Protein and DMSO',
                                                                     'DMSO',
                                                                    ] else None
                    elif isinstance(column_data, dict):
                        ligand = column_data.get('ligand')
                    else:
                        raise Warning('Problem finding ligand')

                    logging.info(f'{experiment_number} {independent_variables.get("dispense_ligands")} {plate_name} column {column_num} ligand {ligand}')

                    column_df = df.loc[df.index.str.contains(f'[A-Z]{column_num}$'), : ]
                    if math.prod(column_df.dropna().shape) == 0:
                        raise Warning(f'No data for wells: {", ".join(column_df.index)}')

                    test_data = column_df.loc[column_df.index.str.contains('|'.join(test_rows)), :]
                    control_data = column_df.loc[column_df.index.str.contains('|'.join(control_rows)), :]

                    corrected_data = test_data.reset_index(drop=True).subtract(control_data.reset_index(drop=True))
                    # corrected_data.index = concs
                    # corrected_data = corrected_data.sort_index()

                    diff_data = corrected_data.subtract(corrected_data.loc[0, :], axis=1)
                    diff_data.index = concs[::-1]

                    response = utils.mm.calculate_response(diff_data)
                    vmax, km = utils.mm.calculate_km(response, response.index)
                    #rsq = utils.mm.r_squared(response[::-1], utils.mm.curve(concs, vmax, km))
                    rsq = utils.mm.r_squared(response, utils.mm.curve(concs, vmax, km))

                    a420_max = corrected_data.loc[:, 420].max()
                    auc = utils.metrics.auc(corrected_data)
                    auc_mean = auc.mean()
                    auc_cv = auc.std() / auc_mean
                    std_405 = utils.metrics.std_405(corrected_data)
                    dd_soret = utils.metrics.dd_soret(diff_data)

                    summary.append({
                        'ligand': ligand,
                        'km': km,
                        'vmax': vmax,
                        'rsq': rsq,
                        'column_num': column_num,
                        'protein_concentration': protein_concentration,
                        'a420_max': a420_max,
                        'auc_mean': auc_mean,
                        'auc_cv': auc_cv,
                        'std_405': std_405,
                        'dd_soret': dd_soret,
                        **independent_variables,
                        }
                             )

                    for idx, (test_i, conc) in enumerate(zip(test_data.index,
                                                                concs,
                                                                )
                                                            ):
                        test_row = test_data.loc[test_i, :].to_dict()
                        per_well_summary.append({**test_row,
                                                 **independent_variables,
                                                 'experiment_number': experiment_number,
                                                 'ligand': ligand,
                                                 'concentration': conc,
                                                 'control': False,
                                                 'address': test_i,
                                                 }
                                                )


                    if control_data is not None:
                        for idx, (control_i, conc) in enumerate(zip(control_data.index,
                                                                    concs,
                                                                    )
                                                                ):

                            control_row = control_data.loc[control_i, :].to_dict()
                            per_well_summary.append({**control_row,
                                                     **independent_variables,
                                                     'experiment_number': experiment_number,
                                                     'ligand': ligand,
                                                     'concentration': conc,
                                                     'control': True,
                                                     'address': control_i,
                                                     }
                                                    )

                    if plot:
                        plot_group(control_data=control_data,
                                   raw_data=test_data,
                                   corrected_data=corrected_data,
                                   diff_data=diff_data,
                                   concs=concs,
                                   ligand=ligand,
                                   response=response,
                                   vmax=vmax,
                                   km=km,
                                   rsq=rsq,
                                   a420_max=a420_max,
                                   table_data=independent_variables,
                                   suptitle = f"UV-Visible Absorbance Profile of BM3 in Response to {ligand}",
                                   show=show,
                                   save_path=os.path.join(img_dir,
                                                          f'{experiment_number}-{independent_variables.get("ligand_dispensing")}-{plate_name}-column-{column_num}-ligand-{ligand}.png',
                                                          ),
                                   )


            summary = pd.DataFrame(summary)
            summary.to_csv(os.path.join(working_directory,
                                        f'experiment-{experiment_number}-summary.csv'
                                        ), 
                           index=False)

            per_well_summary = pd.DataFrame(per_well_summary)
            per_well_summary.to_csv(os.path.join(working_directory,
                                        f'experiment-{experiment_number}-per-well-summary.csv'
                                        ), 
                           index=False)

        except Exception as e:
            logging.warn(f'{config_path} {e}')

cli.add_command(serial)
cli.add_command(echo)

if __name__ == "__main__":
    cli()
