import sys
import json
from PlateObjects import SourcePlateCompound, Block, AssayPlate

aracadonic = SourcePlateCompound('Arachadonic acid',['C'+str(i) for i in range(1,10)],ldv=False)
DMSO = SourcePlateCompound('DMSO',['D'+str(i) for i in range(1,24)],ldv=False)

assayplate1 = AssayPlate()
assayplate2 = AssayPlate()
assayplate3 = AssayPlate()
assayplate4 = AssayPlate()


for vol in [20,30,40]:
    for repeat in range(8):
        block1 = Block(aracadonic,DMSO,vol)
        assayplate1.AddBlocks(block1)

for vol in [20,30,40]:
    for repeat in range(8):      
        block2 = Block(aracadonic,DMSO,vol)
        assayplate2.AddBlocks(block2)
        
for vol in [20,30,40]:
    for repeat in range(8):
        block3 = Block(aracadonic,DMSO,vol)
        assayplate3.AddBlocks(block3)
        
for vol in [20,30,40]:
    for repeat in range(8):
        block4 = Block(aracadonic,DMSO,vol)
        assayplate4.AddBlocks(block4)

        
assayplate1.MapWells()

blocks_dict = {}

for i in assayplate1.blocks.keys():
    block = assayplate1.blocks[i]
    blocks_dict[i] = {
                "well_volume": block.WorkingVol,
                "test_wells": block.TestWells,
                "control_wells": block.BlankWells,
                # "protein_concentration": block.ProteinConc,
                "concentrations": block.concentrations,
            }


sys.stdout.write(json.dumps(blocks_dict))
