
def generate_markdown_Table(titles):
    for i in titles:
        print('|![]('+(i + ' Corrected Spectra PM.png').replace(' ','_')+')|![]('\
        +(i + ' Difference Spectra PM.png').replace(' ','_')\
        +')|![]('+(i + ' Michaelis Menten PM.png').replace(' ','_')+')|')

titles = ['protein and dmso 1','protein and dmso 2',
'arachadnic acid 1','arachadnic acid 2',
'Lauric Acid 1','Lauric Acid 2',
'Palmitic acid 1','Palmitic acid 2',
'4-Phenylimidazole 1']

titles = ['15.14 uM BM3 '+i for i in titles]
generate_markdown_Table(titles)
