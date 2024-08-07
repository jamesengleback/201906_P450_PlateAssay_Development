import math
import json
import os
import re
from string import ascii_uppercase
import argparse
import logging
import itertools
from io import BytesIO
import colorama
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import click
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import utils
from utils.plot import plot_group

logging.basicConfig(level=logging.INFO)

class TextStyle:
    def bgreen(s):
        return f'{colorama.Style.BRIGHT + colorama.Fore.GREEN}{s}{colorama.Style.RESET_ALL}'
    def green(s):
        return f'{colorama.Fore.GREEN}{s}{colorama.Style.RESET_ALL}'
    def bred(s):
        return f'{colorama.Style.BRIGHT + colorama.Fore.RED}{s}{colorama.Style.RESET_ALL}'
    def red(s):
        return f'{colorama.Fore.RED}{s}{colorama.Style.RESET_ALL}'

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
                    # df = df.subtract(df[800], axis=0)
                    test_plate_contents = {i:{} for i in well_ids.values()}

                    for block_num, block in zip(blocks.keys(), blocks.values()):

                        independent_variables = constants | {i: block[i] for i in block if isinstance(block[i], (str, int, float))}

                        ligand = block.get('ligand') or experiment_config.get('ligand') or config_data.get('ligand')

                        logging.info(f'{experiment_number} {independent_variables.get("dispense_ligands")}  block {block_num} ligand {ligand}')

                        concs = block.get('concentrations') or experiment_config.get('concentrations') or config_data.get('concentrations')

                        if concs is not None: 
                            concs = np.array(concs)
                        else:
                            concs = np.array([0] * len(block['test_wells'])) # all zero

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

                        corrected_data = corrected_data.subtract(corrected_data[800], axis=0)

                        if concs is not None:
                            corrected_data = corrected_data.sort_index()
                            diff_data = corrected_data.subtract(corrected_data.iloc[concs.argmin(), :], axis=1)
                            response = utils.mm.calculate_response(diff_data)

                            try:
                                vmax, km = utils.mm.calculate_km(response, response.index)
                                rsq = utils.mm.r_squared(response, utils.mm.curve(concs, vmax, km))
                            except:
                                vmax, km, rsq = None, None, None
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
                                                     'block': block_num,
                                                     'ligand': ligand,
                                                     'concentration': conc,
                                                     'experiment': experiment_number,
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
                                                         'experiment': experiment_number,
                                                         'ligand': ligand,
                                                         'block': block_num,
                                                         'concentration': conc,
                                                         'control': True,
                                                         'address': control_i,
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
                # df = df.subtract(df[800], axis=0) # 800 nm correction

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
                    corrected_data = corrected_data.subtract(corrected_data[800], axis=0)
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

                    for idx, (test_i, control_i, conc) in enumerate(zip(test_data.index,
                                                                        control_data.index,
                                                                        concs,
                                                                        )
                                                                    ):
                        test_row = test_data.loc[test_i, :].to_dict()
                        per_well_summary.append({**test_row,
                                                 **independent_variables,
                                                 'ligand': ligand,
                                                 'concentration': conc,
                                                 'control': False,
                                                 'address': test_i,
                                                 'experiment': experiment_number,
                                                 'block': column_num,
                                                 }
                                                )


                        control_row = control_data.loc[control_i, :].to_dict()
                        per_well_summary.append({**control_row,
                                                 **independent_variables,
                                                 'ligand': ligand,
                                                 'concentration': conc,
                                                 'control': True,
                                                 'address': control_i,
                                                 'experiment': experiment_number,
                                                 'block': column_num,
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

@click.command()
@click.argument('config_paths', nargs=-1)
@click.option('-p', '--plot', is_flag=True, type=bool, default=False)
@click.option('-s', '--show', is_flag=True, type=bool, default=False)
@click.option('-t', '--experiment_type', type=str, default='serial')
@click.option('-d', '--db_uri', type=str)
def process(config_paths,
            experiment_type,
            plot,
            show,
            db_uri,
            ):

    dict_to_str = lambda d : ' '.join([f'{i} = {round(d[i], 2) if isinstance(d[i], (float, int)) else d[i]}' for i in d.keys()])

    if db_uri is None:
        SQLITE_URI = f'sqlite:///'
        db_uri = SQLITE_URI + os.path.abspath(os.path.join(os.curdir, 'db.sqlite3'))

    engine = create_engine(db_uri, echo=True)
    utils.model.Base.metadata.create_all(engine)
    logging.info(TextStyle.bred(f"Connected to: {db_uri}"))
    #con = sqlite3.connect(db_uri)

    #import ipdb ; ipdb.set_trace()
    with Session(engine) as session:
        for config_path in config_paths:
            per_well_summary = []
            logging.info(config_path)
            working_directory = os.path.abspath(os.path.dirname(config_path))

            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            experiment_number = config_data["experiment_number"]

            constants = {i.lower(): j for i, j in zip(config_data.keys(),
                                              config_data.values(),
                                              ) if not isinstance(j, (list, dict))
                         }

            logging.info(TextStyle.bgreen(f'Experiment: {experiment_number}: ' + dict_to_str(constants)))
            # if plot:
            #     img_dir = os.path.join(working_directory, 'img')
            #     if not os.path.exists(img_dir):
            #         os.mkdir(img_dir)
            summary = []

            match experiment_type:
                case 'serial':
                    test_rows = config_data['test_rows']
                    control_rows = config_data['control_rows']
                    concs = np.array(config_data['concentrations'])

                    # order of concs is reversed (high at top of column)
                    # so there's some messing here
                    experiments = config_data.get('experiments')
                    # logging.info(f'Experiments: {dict_to_str(experiments)}')
                    for plate_name in experiments.keys():


                        experiment = experiments[plate_name]
                        file_path = os.path.join(working_directory, experiment['file'])
                        logging.info(file_path)
                        # img_dir = os.path.join(working_directory, 'img')
                        columns = experiment['columns']

                        experiment_constants = {i.lower(): j for i, j in zip(experiment.keys(),
                                                          experiment.values(),
                                                          ) if not isinstance(j, (list, dict))
                                     }

                        experiment_constants['protein_concentration'] =  config_data.get('protein_concentration') 

                        logging.info(TextStyle.red(dict_to_str(experiment_constants)))

                        df = utils.bmg.parse_bmg(file_path)
                        # df = df.subtract(df[800], axis=0) # 800 nm correction

                        for column_num in columns:
                            column_data = columns[column_num]
                            variables = constants | experiment_constants | {i: column_data[i] for i in column_data if isinstance(column_data, dict) and isinstance(column_data[i], (str, int, float))}

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

                            variables['ligand'] = ligand

                            # logging.debug(TextStyle.bgreen('Variables: ') + TextStyle.green(dict_to_str(variables)))
                            logging.info(TextStyle.bgreen('Variables: ') + TextStyle.green(dict_to_str(variables)))

                            column_df = df.loc[df.index.str.contains(f'[A-Z]{column_num}$'), : ]
                            if math.prod(column_df.dropna().shape) == 0:
                                logging.warning(TextStyle.bred(f'No data for wells: {", ".join(column_df.index)}'))
                                continue

                            test_data = column_df.loc[column_df.index.str.contains('|'.join(test_rows)), :]
                            control_data = column_df.loc[column_df.index.str.contains('|'.join(control_rows)), :]

                            results = utils.processing.process_block(test_data,
                                                                      control_data,
                                                                      concs,
                                                                      plot,
                                                                     )

                            summary.append(variables | results)

                            logging.info(TextStyle.bred('Results: ') + TextStyle.red(dict_to_str(results)))

                                

                            wells = []  

                            for i, conc in zip(test_data.index,
                                              concs,
                                              ):

                                test_row = test_data.loc[i, :]
                                well = utils.model.Well(
                                                        address=test_row.name,
                                                        plate_type=variables.get('plate_type'),
                                                        file=variables.get('file'),
                                                        ligand=variables.get('ligand'),
                                                        control=False,
                                                        )
                                wells.append(well)

                            if control_data is not None:
                                for i, conc in zip(control_data.index,
                                                   concs,
                                                   ):
                                    control_row = control_data.loc[i, :]
                                    well = utils.model.Well(address=test_row.name,
                                                            plate_type=variables.get('plate_type'),
                                                            file=variables.get('file'),
                                                            ligand=variables.get('ligand'),
                                                            control=True,
                                                            )
                                    wells.append(well)

                            results = utils.processing.process_block(test_data,
                                                                     control_data,
                                                                     concs,
                                                                     **variables,
                                                                     )
                            if (fig := results.get('fig')):
                                fig_buf = BytesIO()
                                fig.savefig(fig_buf, format='png')
                                fig_buf.seek(0)

                            res = utils.model.Result(experiment_number=variables.get('experiment_number'),
                                                     centrifuge_minutes=variables.get('centrifuge_minutes'),
                                                     centrifuge_rpm=variables.get('centrifuge_rpm'),
                                                     dispense_bulk=variables.get('dispense_bulk'),
                                                     dispense_ligands=variables.get('dispense_ligands'),
                                                     protein_days_thawed=variables.get('protein_days_thawed'),
                                                     protein_concentration=variables.get('protein_concentration'),
                                                     protein_name=variables.get('protein_name'),
                                                     plate_type=variables.get('plate_type'),
                                                     well_volume=variables.get('well_volume'),
                                                     volume=variables.get('well_volume'),
                                                     ligand=variables.get('ligand'),
                                                     k=variables.get('k'),
                                                     km=results.get('km'),
                                                     vmax=results.get('vmax'),
                                                     rsq=results.get('rsq'),
                                                     a420_max=results.get('a420_max'),
                                                     auc_mean=results.get('auc_mean'),
                                                     auc_cv=results.get('auc_cv'),
                                                     std_405=results.get('std_405'),
                                                     dd_soret=results.get('dd_soret'),
                                                     fig=fig_buf.read() if fig is not None,
                                                     )

                            session.add(res)
                            session.commit()

                            for well in wells:
                                well.result_id = res.id
                                session.add(well)

                            session.commit()

                case 'echo':
                    source_plate_contents = config_data.get('source_plate_contents')
                    experiments = config_data.get('experiments')
                    blocks = config_data.get('blocks')
                    well_ids = {i:j for i, j in enumerate(
                        [f'{k}{l}' for k in ascii_uppercase[:16] for l in range(1,25)],
                                                1)
                                }

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
                            # df = df.subtract(df[800], axis=0)
                            test_plate_contents = {i:{} for i in well_ids.values()}

                            for block_num, block in zip(blocks.keys(), blocks.values()):

                                variables = constants | experiment_config | {i: block[i] for i in block if isinstance(block[i], (str, int, float))}
                                variables['ligand'] = block.get('ligand') or experiment_config.get('ligand') or config_data.get('ligand') 

                                logging.info(TextStyle.bgreen('Variables: ') + TextStyle.green(dict_to_str(variables)))

                                concs = block.get('concentrations') or experiment_config.get('concentrations') or config_data.get('concentrations')
                                if concs is not None: 
                                    concs = np.array(concs)
                                else:
                                    concs = np.zeros_like(block['test_wells'], dtype=float)

                                test_data = df.loc[list(block['test_wells']), :]
                                if (control_wells := block.get('control_wells')):
                                    control_data = df.loc[list(control_wells), :]
                                else:
                                    control_data = None
                                

                                wells = []  

                                for i, conc in zip(test_data.index,
                                                  concs,
                                                  ):

                                    test_row = test_data.loc[i, :]
                                    well = utils.model.Well(
                                                            address=test_row.name,
                                                            plate_type=variables.get('plate_type'),
                                                            file=variables.get('file'),
                                                            ligand=variables.get('ligand'),
                                                            control=False,
                                                            )
                                    wells.append(well)

                                if control_data is not None:
                                    for i, conc in zip(control_data.index,
                                                       concs,
                                                       ):
                                        control_row = control_data.loc[i, :]
                                        well = utils.model.Well(address=test_row.name,
                                                                plate_type=variables.get('plate_type'),
                                                                file=variables.get('file'),
                                                                ligand=variables.get('ligand'),
                                                                control=True,
                                                                )
                                        wells.append(well)

                                results = utils.processing.process_block(test_data,
                                                                         control_data,
                                                                         concs,
                                                                         )
                                if (fig := results.get('fig')):
                                    fig_buf = BytesIO()
                                    fig.savefig(fig_buf, format='png')
                                    fig_buf.seek(0)

                                res = utils.model.Result(experiment_number=variables.get('experiment_number'),
                                                         centrifuge_minutes=variables.get('centrifuge_minutes'),
                                                         centrifuge_rpm=variables.get('centrifuge_rpm'),
                                                         dispense_bulk=variables.get('dispense_bulk'),
                                                         dispense_ligands=variables.get('dispense_ligands'),
                                                         protein_days_thawed=variables.get('protein_days_thawed'),
                                                         protein_concentration=variables.get('protein_concentration'),
                                                         protein_name=variables.get('protein_name'),
                                                         plate_type=variables.get('plate_type'),
                                                         well_volume=variables.get('well_volume'),
                                                         volume=variables.get('well_volume'),
                                                         ligand=variables.get('ligand'),
                                                         k=variables.get('k'),
                                                         km=results.get('km'),
                                                         vmax=results.get('vmax'),
                                                         rsq=results.get('rsq'),
                                                         a420_max=results.get('a420_max'),
                                                         auc_mean=results.get('auc_mean'),
                                                         auc_cv=results.get('auc_cv'),
                                                         std_405=results.get('std_405'),
                                                         dd_soret=results.get('dd_soret'),
                                                         fig=fig_buf.read() if fig is not None,
                                                         )

                                session.add(res)
                                session.commit()

                                for well in wells:
                                    well.result_id = res.id
                                    session.add(well)

                                session.commit()


@click.command()
@click.argument('db', nargs=1)
def serve(db):
    from .app import app
    app.db = db
    app.run(debug=True)

cli.add_command(serial)
cli.add_command(echo)
cli.add_command(process)
cli.add_command(serve)

if __name__ == "__main__":
    cli()
