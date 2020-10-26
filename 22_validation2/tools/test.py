import echo
import numpy as np

def reqVol(c1, c2, v2):
    return (c2 *v2) / c1

def main():
    protein = echo.liquid('protein',vol = 20, conc = 0.1)
    buffer = echo.liquid('buffer',10_000, 100)
    dmso = echo.liquid('dmso',6000)
    compound = echo.liquid('cpd',1000, 10)

    assayVol = 50
    max_conc = echo.dil(0.05 * assayVol, 10_000, assayVol)

    wells = []
    for conc in  np.linspace(0,max_conc,8):
        v1 = reqVol(10_000, conc, 50)
        mx = echo.mixture(buffer.sample(0.95 * assayVol),
                            compound.sample(v1),
                            dmso.sample((0.05 * assayVol) - v1))
        well = echo.well(mx)
        wells.append(well)
    plate = echo.plate(*wells)
    print(plate.array)


if __name__ == '__main__':
    main()
