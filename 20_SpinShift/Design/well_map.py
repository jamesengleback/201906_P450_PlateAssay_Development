from PlateObjects import SourcePlateCompound, AssayPlate, Block

aracadonic = SourcePlateCompound('Arachadonic acid',['A'+str(i) for i in range(4,8)],ldv=False)
DMSO = SourcePlateCompound('DMSO',['B'+str(i) for i in range(4,15)],ldv=False)

assayplate1 = AssayPlate()
assayplate2 = AssayPlate()

for vol in [20,40]:
    for repeat in range(12):
        block1 = Block(aracadonic,DMSO,vol)
        assayplate1.AddBlocks(block1)
        
        block2 = Block(aracadonic,DMSO,vol)
        assayplate2.AddBlocks(block2)
import ipdb ; ipdb.set_trace()

