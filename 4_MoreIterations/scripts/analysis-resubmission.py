import os
from string import ascii_uppercase
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import utils

def main():

    experiments = {
            'plate_1':{
                'file':"20190618_Assay1.CSV", 
                'columns':{
                    1: 'Protein',
                    2: 'Protein and DMSO',
                    3: 'Lauric Acid',
                    4: 'Lauric Acid',
                    5: 'Lauric Acid',
                    6: 'Arachadionic Acid',
                    7: 'Arachadionic Acid',
                    8: 'Arachadionic Acid',
                    9: '4-Phenylimidazole',
                    10: '4-Phenylimidazole',
                    11: '4-Phenylimidazole',
                    },
                },
            'plate_2':{
                'file': "20190618_Assay2.csv",
                'columns':{
                    13: 'Protein',
                    14: 'Lauric Acid',
                    15: 'Lauric Acid',
                    16: 'Arachadionic Acid',
                    17: 'Arachadionic Acid',
                    18: '4-Phenylimidazole',
                    19: '4-Phenylimidazole',
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

        df = utils.parse.bmg(file_path)
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
                }
                     )

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
            plt.savefig(os.path.join('img', f'4_{columns[column_num]}-{column_num}.png'))
            #plt.show()
            plt.close()

    o = pd.DataFrame(o)
    o.to_csv('experiment-4-summary.csv')



if __name__ == "__main__":
    main()
