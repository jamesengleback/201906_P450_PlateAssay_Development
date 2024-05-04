import utils

def main():

    experiments = {
            'plate_1':{
                'file': "20190618_Assay2.csv",
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
                'file': "20190618_Assay1.CSV",
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

    for plate_name in experiments.keys():
        experiment = experiments[plate_name]
        file_path = experiment['file']
        columns = experiment['columns']
        df = utils.bmg.parse_bmg(file_path)
        print(df)


if __name__ == "__main__":
    main()
