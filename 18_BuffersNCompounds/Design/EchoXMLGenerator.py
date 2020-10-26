import pandas as pd
import re
import string

'''
Output Format:
<?xml version="1.0"?>
<TransferPlate>
<Transfer SrcID="1" DestID="3" Volume="50"  />
</TransferPlate>

The wells are numbered instead of lettered
The machine can't handle zeros so they all have to go
<Transfer SrcID="1" DestID="3" Volume="0.0"  /> # No!!!
'''

def Generate(dataframe, path):
    '''
    The dataframe needs the columns
    SrcID,DestID and Volume
    '''
    dataframe = dataframe.loc[dataframe['Volume']!= 0.0]
    output = open(path, 'w')
    output.write('<?xml version="1.0"?>\n')
    output.write('<TransferPlate>\n')
    for i,j,k in zip(dataframe['SrcID'],dataframe['DestID'],dataframe['Volume']):
        output.write('<Transfer SrcID="{}" DestID="{}" Volume="{}"  />\n'.format(i,j,k))
    output.write('</TransferPlate>')
    output.close()

def WellIDtoNumber(wellID):
    '''
    Assumes the plate has 384 wells
    '''
    number = int(re.findall(r'\d+', wellID)[0])
    letter = re.findall(r'\w', wellID)[0].lower()
    alphabet = dict((letter,number) for letter,number in zip(string.ascii_lowercase,range(0,26)))

    return alphabet[letter]*24 + number
