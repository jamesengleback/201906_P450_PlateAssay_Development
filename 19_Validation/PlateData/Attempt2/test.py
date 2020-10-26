from PlateAnalysis_b import PlateDataset

def main():
    TritonPlate = PlateDataset('20191202_KPi_Triton.CSV','20191202_pathlength_kpi_Triton.CSV',True)
    CompoundMap = dict(zip(range(1,25),['Lauric Acid']*6 + \
                       ['Arachadionic Acid']*6 + \
                       ['Palmitic Acid']*6 + \
                       ['4-Phenylimidazole']*6))
                   
    for i in range(1,25):    
        spinshift = TritonPlate.AnalysisPipeline_2(i)
        


if __name__ == '__main__':
    main()
