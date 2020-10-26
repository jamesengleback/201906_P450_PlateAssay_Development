from PlateObjects import SourcePlateCompound, AssayPlate, Block
from EchoXMLGenerator import WellIDtoNumber, Generate
import string
from tqdm import tqdm

def main():
    aracadonic = SourcePlateCompound('Arachadonic acid',['B'+str(i) for i in range(1,6)],ldv=False)
    DMSO = SourcePlateCompound('DMSO',['A'+str(i) for i in range(1,24)],ldv=False)
    
    assayplate1 = AssayPlate()
    for i in tqdm([lauric, aracadonic, palmitic,phenylimidazole]):
        for repeat in range(6):
            block = Block(i,DMSO)
            assayplate1.AddBlocks(block)
            
    
                
    assayplate1.MapWells()
    transferMap1 = assayplate1.TransferPlan
    transferMap1 = transferMap1.loc[transferMap1['Volume']>0]
    print(transferMap1)
    transferMap1.to_csv('20191206_transferMap1.csv')
    #transferMap1['SrcID'] = transferMap1['SrcID'].apply(WellIDtoNumber)
    #transferMap1['DestID'] = transferMap1['DestID'].apply(WellIDtoNumber)
    
    
    #Generate(transferMap1,'20191206_1.xml')
    
if __name__ == '__main__':
    main()
