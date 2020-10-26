from os import listdir
from os.path import isfile, join
import pandas as pd

mypath='/home/james/Documents/Work/201906_PlateAssayDevelopment/11_Validation/PlateData/'
onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
files=pd.Series(onlyfiles)
files=files.loc[files.str.contains('PM.png')]

theblackone=files.loc[files.str.contains('that_black_one')].sort_values()
Thermo_Delta=files.loc[files.str.contains('Thermo_Delta')].sort_values()
Brand_PS_Standard=files.loc[files.str.contains('Brand_PS_Standard')].sort_values()
Brand_Lipograde=files.loc[files.str.contains('Brand_Lipograde')].sort_values()

def addBitsToStrings(series):
    return '|![](PlateData/'+series+')'


theblackone=addBitsToStrings(theblackone).reset_index(drop=True)
Thermo_Delta=addBitsToStrings(Thermo_Delta).reset_index(drop=True)
Brand_PS_Standard=addBitsToStrings(Brand_PS_Standard).reset_index(drop=True)
Brand_Lipograde=addBitsToStrings(Brand_Lipograde).reset_index(drop=True)+'|'

df=pd.concat([theblackone,Thermo_Delta,Brand_PS_Standard,Brand_Lipograde],axis=1,join='inner')
df.to_clipboard(index=False)
