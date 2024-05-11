import click
import math
import json
import os
import re
from string import ascii_uppercase
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import utils

def plot_group(corrected_data,
               diff_data,
               concs,
               ligand=None,
               response=None,
               vmax=None,
               km=None, 
               rsq=None,
               a420_max=None,
               suptitle=None,
               show=None,
               save_path=None,
               ):
    fig, axs = plt.subplots(2, 2, figsize=(16,8))

    utils.plot.plot_plate_data(corrected_data,
                               ax=axs[0, 0],
                               concs=concs,
                               ligand_name=ligand,
                               ylim=(-0.1, max(0.3, 1.2 * a420_max)),
                               )

    utils.plot.plot_plate_data(corrected_data,
                               ax=axs[0, 1],
                               concs=concs,
                               ligand_name=ligand,
                               ylim=(-0.1, max(0.3, 1.2 * a420_max)),
                               )

    utils.plot.plot_plate_data(diff_data,
                               ax=axs[1, 0],
                               concs=concs,
                               ligand_name=ligand,
                               ylim=(-0.1, max(0.3, 1.2 * a420_max)),
                               )

    if ligand is not None:
        utils.plot.plot_michaelis_menten(response=response,
                                         concs=response.index,
                                         vmax=vmax,
                                         km=km,
                                         r_squared=rsq,
                                         ax=axs[1, 1],
                                         ylim=(0, max((vmax * 1.2), max(response) * 1.2)),
                                         )
    else:
        axs[1, 1].axis('off')

    plt.suptitle(suptitle)

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
@click.argument('config_path')
@click.option('-p', '--plot', is_flag=True, type=bool, default=False)
@click.option('-s', '--show', is_flag=True, type=bool, default=False)
def echo(config_path,
         plot,
         show,
         **kwargs,
         ):
    """ Analyse experiment directory from config json file
    """

    working_directory = os.path.abspath(os.path.dirname(config_path))

    with open(config_path, 'r') as f:
        config_data = json.load(f)

    experiment_number = config_data["experiment_number"]

    working_directory = os.path.abspath(os.path.dirname(config_path))
    img_dir = os.path.join(working_directory, 'img')
    if not os.path.exists(img_dir):
        os.mkdir(img_dir)

    constants = {i.lower(): j for i, j in zip(config_data.keys(),
                                      config_data.values(),
                                      ) if not isinstance(j, (list, dict))
                 }

    # test_rows = config_data['test_rows']
    # control_rows = config_data['control_rows']
    # concs = np.array(config_data['concentrations'])

    o = []
    # order of concs is reversed (high at top of column)
    # so there's some messing here
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

        # map well contents
        # picklist_path = experiment_config.get('echo_picklist')
        # if picklist_path is not None:
        #     picklist = pd.read_csv(picklist_path, index_col=0)

        #     if picklist['SrcID'].dtype == int:
        #         picklist['SrcID'] = picklist['SrcID'].replace(well_ids)

        #     if picklist['DestID'].dtype == int:
        #        picklist['DestID'] = picklist['DestID'].replace(well_ids)


        #     for i, j, k in zip(picklist['SrcID'], picklist['DestID'], picklist['Volume']):
        #         compound = source_plate_contents.get(i)
        #         if compound is None:
        #             raise Warning()
        #         test_plate_contents[j][compound] = k

        echo_log_path = experiment_config.get('echo_log')

        if echo_log_path is not None:
            pass
        plate_data_path = experiment_config.get('file')

        if plate_data_path is not None:
            df = utils.bmg.parse_bmg(plate_data_path)
            test_plate_contents = {i:{} for i in well_ids.values()}

            for block_num, block in zip(blocks.keys(), blocks.values()):

                ligand = block.get('ligand')
                concs = np.array(block['concentrations'])
                test_data = df.loc[list(block['test_wells']), :]
                control_data = df.loc[list(block['control_wells']), :]
                corrected_data = test_data.reset_index(drop=True).subtract(control_data.reset_index(drop=True))
                corrected_data.index = concs[::-1]
                corrected_data = corrected_data.sort_index()
                diff_data = corrected_data.subtract(corrected_data.loc[0, :], axis=1)
                response = utils.mm.calculate_response(diff_data)
                vmax, km = utils.mm.calculate_km(response, response.index)
                rsq = utils.mm.r_squared(response[::-1], utils.mm.curve(concs, vmax, km))

                a420_max = corrected_data.loc[:, 420].max()
                auc = utils.metrics.auc(corrected_data)
                auc_cv = auc.std() / auc.mean()
                std_405 = utils.metrics.std_405(corrected_data)
                dd_soret = utils.metrics.dd_soret(diff_data)

                o.append({
                    'ligand': ligand,
                    'km': km,
                    'vmax': vmax,
                    'rsq': rsq,
                    'protein_concentration': experiment_config.get('protein_concentration'),
                    'a420_max':a420_max,
                    'auc': auc,
                    'auc_cv': auc_cv,
                    'std_405': std_405,
                    'dd_soret': dd_soret,
                    # **constants,
                    # **experiment_constants,
                    }
                         )

                if plot:


                    plot_group(corrected_data,
                               diff_data=diff_data,
                               concs=concs,
                               ligand=ligand,
                               response=response,
                               vmax=vmax,
                               km=km, 
                               rsq=rsq,
                               a420_max=a420_max,
                               suptitle = f"UV-Visible Absorbance Profile of BM3 in Response to {ligand}",
                               show=show,
                               save_path=os.path.join(img_dir,
                                                      f'experiment-{experiment}-block-{block_num}-ligand-{ligand}.png',
                                                      )
                               )

    o = pd.DataFrame(o)
    o.to_csv(f'experiment-{experiment_number}-summary.csv', index=False)


    
@click.command()
@click.argument('config_path')
@click.option('-p', '--plot', is_flag=True, type=bool, default=False)
@click.option('-s', '--show', is_flag=True, type=bool, default=False)
def serial(config_path,
           plot,
           show,
           **kwargs,
           ):
    """ Analyse experiment directory from config json file
        Assumig the serial dilution-type experiment design 
        from iterations 2-10
    """

    working_directory = os.path.abspath(os.path.dirname(config_path))

    with open(config_path, 'r') as f:
        config_data = json.load(f)
    
    experiment_number = config_data["experiment_number"]

    constants = {i.lower(): j for i, j in zip(config_data.keys(),
                                      config_data.values(),
                                      ) if not isinstance(j, (list, dict))
                 }

    test_rows = config_data['test_rows']
    control_rows = config_data['control_rows']
    concs = np.array(config_data['concentrations'])

    o = []
    # order of concs is reversed (high at top of column)
    # so there's some messing here
    experiments = config_data.get('experiments')
    for plate_name in experiments.keys():

        experiment = experiments[plate_name]
        file_path = os.path.join(working_directory, experiment['file'])
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


            column_df = df.loc[df.index.str.contains(f'[A-Z]{column_num}$'), : ]
            if math.prod(column_df.dropna().shape) == 0:
                raise Warning(f'No data for wells: {", ".join(column_df.index)}')
            test_data = column_df.loc[column_df.index.str.contains('|'.join(test_rows)), :]
            control_data = column_df.loc[column_df.index.str.contains('|'.join(control_rows)), :]
            corrected_data = test_data.reset_index(drop=True).subtract(control_data.reset_index(drop=True))

            #corrected_data.index = concs
            # this dataset concs got high to low
            # for plotting better i want the reverse
            #corrected_data = corrected_data.loc[corrected_data.index[::-1], :]

            corrected_data.index = concs[::-1]
            corrected_data = corrected_data.sort_index()
            diff_data = corrected_data.subtract(corrected_data.loc[0, :], axis=1)
            response = utils.mm.calculate_response(diff_data)
            vmax, km = utils.mm.calculate_km(response, response.index)
            rsq = utils.mm.r_squared(response[::-1], utils.mm.curve(concs, vmax, km))

            a420_max = corrected_data.loc[:, 420].max()
            auc = utils.metrics.auc(corrected_data)
            auc_cv = auc.std() / auc.mean()
            std_405 = utils.metrics.std_405(corrected_data)
            dd_soret = utils.metrics.dd_soret(diff_data)

            o.append({
                'ligand': ligand,
                'km': km,
                'vmax': vmax,
                'rsq': rsq,
                'column_num': column_num,
                'protein_concentration': protein_concentration,
                'a420_max':a420_max,
                'auc': auc,
                'auc_cv': auc_cv,
                'std_405': std_405,
                'dd_soret': dd_soret,
                **constants,
                **experiment_constants,
                }
                     )


    o = pd.DataFrame(o)
    o.to_csv(f'experiment-{experiment_number}-summary.csv', index=False)

    group_columns =   [i for i in [
        'ligand', 
        'protein_concentration', 
        'protein_days_thawed', 
        'plate_type',
        ] if i in o.columns]

    agg_mean = o.drop('column_num', axis=1).groupby(group_columns).mean(numeric_only=True).reset_index()
    agg_std = o.drop('column_num', axis=1).groupby(group_columns).std(numeric_only=True).reset_index()

    agg = agg_mean.join(agg_std[['km', 'vmax', 'rsq']], rsuffix='_std')
    agg = agg.round(2)

    ideal_column_order = [
        'ligand',
        'protein_concentration',
        'protein_days_thawed',
        'plate_type',
        'km',
        'km_std',
        'vmax',
        'vmax_std',
        'rsq_std',
        'rsq',
        ]
    agg = agg.loc[:, map(lambda s : s in ideal_column_order, agg.columns) ]

    agg.to_markdown(f'experiment-{experiment_number}-agg.md', index=False)

cli.add_command(serial)
cli.add_command(echo)

if __name__ == "__main__":
    cli()
