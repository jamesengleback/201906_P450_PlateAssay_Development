from PlateObjects import Block, SourcePlateCompound, AssayPlate
import pandas as pd
import dexpy
import dexpy.optimal
from dexpy.model import ModelOrder
from sklearn.preprocessing import MinMaxScaler
import string


def MakeDesign(additives, factors):
    # Design size is the factors plus one additive
    design = dexpy.optimal.build_optimal(len(factors)+1,order=ModelOrder.quadratic)
    cols = list(factors)
    cols.append(additives)
    design.columns = cols
    return design

def NormalizeDesign(design,factors):
    for i in design:
        # new scaler for each column
        low = factors[i][0]
        high = factors[i][1]
        scaler = MinMaxScaler(feature_range = (low, high))
        design[i] = scaler.fit_transform(design[[i]])
    design.fillna(0,inplace=True)
    return design
        
def main():
    
    Factors = {'Protein Vol':[20,30],'Protein Conc':[10,20]}
    Additives = {'Arginine':[100,200],'BSA':[0.1,0.5],'Triton':[0.01,0.1]}
    
    
    # Just arginine today
    design = pd.DataFrame([],columns=list(Factors) + list(Additives))
    design = design.append(MakeDesign('Arginine', Factors),sort = True)
    design.dropna(inplace=True,axis=1)
    Factors.update(Additives)
    design = NormalizeDesign(design, Factors)
    assayplate1 = AssayPlate()
    
    for i in design.index:
        row = design.loc[i,:]
        additive = 'Arginine'
        additive += ' '+str(round(row[additive],2))
       
        for repeat in range(2):
            block = Block(row['Protein Vol'],row['Protein Conc'], 'Arachadionic acid',additive)
            assayplate1.AddBlocks(block) 
    assayplate1.MakeTransfer()
    print(assayplate1.TransferPlan)
    
    for i in assayplate1.blocks:
        print(i,'\t','Vol:','\t',round(assayplate1.blocks[i].WorkingVol/1000,2),\
        '\t','Conc','\t', round(assayplate1.blocks[i].ProteinConc,2),\
        '\tAdditive:\t',assayplate1.blocks[i].Additive)
    '''
    for i in Additives:
        design = design.append(MakeDesign(i, Factors),sort = True)
    design.reset_index(inplace=True,drop=True)
    Factors.update(Additives)
    design = NormalizeDesign(design, Factors)
    print(design)

    
    assayplate1 = AssayPlate()
    assayplate2 = AssayPlate()
    assayplate3 = AssayPlate()
    assayplate4 = AssayPlate()
    for i in design.index:
        row = design.loc[i,:]
        additive = row[['Arginine','BSA','Triton']].idxmax()
        additive += str(row[additive])
       
        
        block = Block(row['Protein Vol'],row['Protein Conc'], 'Arachadionic acid',additive)
        for i in range(2):
            if len(assayplate1.blocks)<24:
                assayplate1.AddBlocks(block) 
            else: 
                if len(assayplate2.blocks)<24:
                    assayplate2.AddBlocks(block)
                else: 
                    if len(assayplate3.blocks)<24:
                        assayplate3.AddBlocks(block) 
                    else: 
                        if len(assayplate4.blocks)<24:
                            assayplate4.AddBlocks(block) 

    assayplate1.MakeTransfer()
    assayplate2.MakeTransfer()
    assayplate3.MakeTransfer()
    assayplate4.MakeTransfer()
    
    print(assayplate1.TransferPlan)'''
    
    
    
if __name__ == '__main__':
    main()
