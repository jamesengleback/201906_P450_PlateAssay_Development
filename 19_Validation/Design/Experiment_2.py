from PlateObjects import SourcePlateCompound, AssayPlate, Block
from EchoXMLGenerator import WellIDtoNumber, Generate
import string
from tqdm import tqdm

def main():
    lauric = SourcePlateCompound('Lauric acid',['J'+str(i) for i in range(1,6)])
    aracadonic = SourcePlateCompound('Arachadonic acid',['K'+str(i) for i in range(1,6)])
    palmitic = SourcePlateCompound('Palmitic acid',['L'+str(i) for i in range(1,6)])
    phenylimidazole = SourcePlateCompound('4-phenylimidazole',['M'+str(i) for i in range(1,6)])
    
    DMSO = SourcePlateCompound('DMSO',['G'+str(i) for i in range(1,24)] + \
    ['H'+str(i) for i in range(1,24)]\
    + ['I'+str(i) for i in range(1,12)])
    
    assayplate1 = AssayPlate()
    for i in tqdm([lauric, aracadonic, palmitic,phenylimidazole]):
        for repeat in range(6):
            block = Block(i,DMSO)
            assayplate1.AddBlocks(block)
            
    assayplate2 = AssayPlate()
    for i in tqdm([lauric, aracadonic, palmitic,phenylimidazole]):
        for repeat in range(6):
            block = Block(i,DMSO)
            assayplate2.AddBlocks(block)

    assayplate3 = AssayPlate()
    for i in tqdm([lauric, aracadonic, palmitic,phenylimidazole]):
        for repeat in range(6):
            block = Block(i,DMSO)
            assayplate3.AddBlocks(block)
                
    assayplate1.MapWells()
    transferMap1 = assayplate1.TransferPlan
    transferMap1['SrcID'] = transferMap1['SrcID'].apply(WellIDtoNumber)
    transferMap1['DestID'] = transferMap1['DestID'].apply(WellIDtoNumber)
    
    
    assayplate2.MapWells()
    transferMap2 = assayplate2.TransferPlan
    transferMap2['SrcID'] = transferMap2['SrcID'].apply(WellIDtoNumber)
    transferMap2['DestID'] = transferMap2['DestID'].apply(WellIDtoNumber)

    assayplate3.MapWells()
    transferMap3 = assayplate3.TransferPlan
    transferMap3['SrcID'] = transferMap3['SrcID'].apply(WellIDtoNumber)
    transferMap3['DestID'] = transferMap3['DestID'].apply(WellIDtoNumber)
    
    Generate(transferMap1,'20191202_1.xml')
    Generate(transferMap2,'20191202_2.xml')
    Generate(transferMap3,'20191202_3.xml')
    
if __name__ == '__main__':
    main()