import os
from string import ascii_uppercase
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import utils

def main(args):

    EXPERIMENT_NUMBER = 6
    PROTEIN_CONCENTRATION = 3.86 
    PLATE_TYPE = 'Corning 3660'
    PROTEIN_DAYS_THAWED = 0 # batch thawed on 20190620

    experiments = {
            'plate_1':{
                'file':"20190620_AM.CSV", 
                'columns':{
                    1: 'Protein and DMSO',
                    2: 'Arachadionic Acid',
                    3: 'Arachadionic Acid',
                    4: 'Arachadionic Acid',
                    5: 'Arachadionic Acid',
                    6: 'Arachadionic Acid',
                    7: 'Arachadionic Acid',
                    8: 'Palmitic Acid',
                    9: 'Palmitic Acid',
                    10: 'Palmitic Acid',
                    11: 'Palmitic Acid',
                    12: 'Palmitic Acid',
                    13: 'Palmitic Acid',
                    14: 'Lauric Acid',
                    15: 'Lauric Acid',
                    16: 'Lauric Acid',
                    17: 'Lauric Acid',
                    18: 'Lauric Acid',
                    19: 'Lauric Acid',
                    },
                },
            }

    if not os.path.exists('img'):
        os.mkdir('img')

    test_rows = ascii_uppercase[:16][::2]
    control_rows = ascii_uppercase[:16][1::2]
    # concs = np.array([round(500 / i**2, 2) for i in range(1, 8)] + [0])
    concs = np.array([0] + [round(500 / i**2, 2) for i in range(1, 8)][::-1])

    o = []
    # order of concs is reversed (high at top of column)
    # so there's some messing here
    for plate_name in experiments.keys():
        experiment = experiments[plate_name]
        file_path = experiment['file']
        columns = experiment['columns']

        df = utils.bmg.parse_bmg(file_path)
        df = df.subtract(df[800], axis=0) # 800 nm correction

        for column_num in columns:

            ligand = columns[column_num]  if columns[column_num] not in [
                                                                         'Protein',
                                                                         'Protein and DMSO',
                                                                        ] else None

            column_data = df.loc[df.index.str.contains(f'[A-Z]{column_num}$'), : ]
            test_data = column_data.loc[column_data.index.str.contains('|'.join(test_rows)), :]
            control_data = column_data.loc[column_data.index.str.contains('|'.join(control_rows)), :]
            corrected_data = test_data.reset_index(drop=True).subtract(control_data.reset_index(drop=True))
            #corrected_data.index = concs
            # this dataset concs got high to low
            # for plotting better i want the reverse
            corrected_data = corrected_data.loc[corrected_data.index[::-1], :]
            corrected_data.index = concs[::-1]
            diff_data = corrected_data.subtract(corrected_data.loc[0, :], axis=1)
            response = utils.mm.calculate_response(diff_data)
            vmax, km = utils.mm.calculate_km(response, response.index)
            rsq = utils.mm.r_squared(response[::-1], utils.mm.curve(concs, vmax, km))

            o.append({
                'ligand': ligand,
                'km': km,
                'vmax': vmax,
                'rsq': rsq,
                'column_num': column_num,
                'protein_concentration': PROTEIN_CONCENTRATION,
                'protein_days_thawed': PROTEIN_DAYS_THAWED,
                'plate_type': PLATE_TYPE,
                'centrifuge_minutes':2,
                'centrifuge_rpm':4000,
                }
                     )

            if args.plot:
                fig, axs = plt.subplots(2, 2, figsize=(16,8))

                utils.plot.plot_plate_data(corrected_data,
                                           ax=axs[0, 0],
                                           concs=concs,
                                           ligand_name=ligand,
                                           ylim=(-0.1, 0.3),
                                           )

                utils.plot.plot_plate_data(corrected_data,
                                           ax=axs[0, 1],
                                           concs=concs,
                                           ligand_name=ligand,
                                           ylim=(-0.1, 0.3),
                                           )

                utils.plot.plot_plate_data(diff_data,
                                           ax=axs[1, 0],
                                           concs=concs,
                                           ligand_name=ligand,
                                           ylim=(-0.1, 0.3),
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

                if ligand is None:
                    plt.suptitle(f'P450 BM3 Control: {columns[column_num]}')
                else:
                    plt.suptitle(f'P450 BM3 with Additions of {ligand}')

                if args.show:
                    plt.show()
                else:
                    plt.savefig(os.path.join('img', f'{EXPERIMENT_NUMBER}_{plate_name}-{columns[column_num]}-{column_num}.png'))
                    plt.close()

    o = pd.DataFrame(o)
    o.to_csv(f'experiment-{EXPERIMENT_NUMBER}-summary.csv', index=False)

    agg_mean = o.drop('column_num', axis=1).groupby(['ligand', 
                                                'protein_concentration', 
                                                'protein_days_thawed', 
                                                'plate_type'
                                                ]
                                               ).mean().reset_index()
    agg_std = o.drop('column_num', axis=1).groupby(['ligand', 
                                                'protein_concentration', 
                                                'protein_days_thawed', 
                                                'plate_type'
                                                ]
                                               ).std().reset_index()

    agg = agg_mean.join(agg_std[['km', 'vmax', 'rsq']], rsuffix='_std')
    agg = agg.round(2)
    agg = agg.loc[:, [
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
                  ]


    agg.to_markdown(f'experiment-{EXPERIMENT_NUMBER}-agg.md', index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--plot', action='store_true', default=False)
    parser.add_argument('-s', '--show', action='store_true', default=False)
    args = parser.parse_args()
    main(args)