from PlateObjects import Block, SourcePlateCompound, AssayPlate

def main():
    block = Block(4,4,'Compound','BSA')
    #assayplate = AssayPlate()
    #assayplate.AddBlocks(block)
    print(block.Transfer)


if __name__ == '__main__':
    main()
