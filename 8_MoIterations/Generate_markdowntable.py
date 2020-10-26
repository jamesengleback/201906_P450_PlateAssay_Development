'''import os
import pandas as pd
direc = pd.Series(os.listdir('.'))
direc = direc[direc.str.contains('.png')]
direc = direc[direc.str.contains('_')]
direc = direc[direc.str.contains('BM3')]

df=direc.str.split('_',expand=True)
df.loc[:,0]=df.loc[:,0].astype(float)
df.sort_values(0,inplace=True,ascending=True)
#df.sort_values(3,inplace=True,ascending=True)

print(direc.loc[df.index])'''


def generate_markdown_Table(titles):
    for i in titles:
        print('|![]('+(i + ' Corrected Spectra PM.png').replace(' ','_')+')|![]('\
        +(i + ' Difference Spectra PM.png').replace(' ','_')\
        +')|![]('+(i + ' Michaelis Menten PM.png').replace(' ','_')+')|')

titles = ['protein and dmso',
'arachadnic acid 1','arachadnic acid 2',
'arachadnic acid 3','arachadnic acid 4',
'Lauric Acid 1','Lauric Acid 2',
'Lauric Acid 3','Lauric Acid 4',
'Palmitic acid 1','Palmitic acid 2',
'Lauric acid 3','Palmitic acid 4',
'4-Phenylimidazole 1','4-Phenylimidazole 2',
'4-Phenylimidazole 3','4-Phenylimidazole 4'
]

titles = ['27.56 uM BM3 '+i for i in titles]
generate_markdown_Table(titles)
#7.09_uM_BM3_4-Phenylimidazole_4_Michaelis_Menten_PM.png
#7.09_uM_4-Phenylimidazole_4_Corrected_Spectra_PM.png
#7.09_uM_BM3_4-Phenylimidazole_4_Corrected_Spectra_PM.png
