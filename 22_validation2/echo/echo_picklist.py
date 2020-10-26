import pandas as pd
import numpy as np

# substrates
# [ara, laur, palm, 4phe]
# k = 3

def v1(c1,v2,c2):
    return (v2 * c2) / c1 

def make_concs(n,k,max_conc):
    return (np.linspace(0, 1, n) ** k) * max_conc
        
class block:
    def __init__(self, cpd, n=8, k=3, vol = 30,  max_conc=500, dual_beam = True):
        self.cpd = cpd
        self.n = 8
        self.k = k 
        self.vol = vol
        self.max_conc = max_conc
        self.dual_beam = dual_beam
        self.wells = None # placeholder
    @property
    def concs(self):
        return make_concs(self.n, self.k, self.max_conc)

class plate:
    def __init__(self, *blocks):
        self.blocks = {i:j for i,j in enumerate(blocks)}

def main():
    b1, b2 = block('ara'), block('lau')
    p1 = plate(b1,b2)
    print(p1.blocks)

if __name__ == '__main__':
    main()
