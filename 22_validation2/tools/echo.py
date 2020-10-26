from string import ascii_uppercase
import numpy as np
import re

plateSizes = {6:{'h':2, 'w':3},
            48:{'h':6,'w':8},
            96:{'h':8,'w':12},
            384:{'h':16, 'w':24},
            1536:{'h':32, 'w':48}}

plateLetters = list(ascii_uppercase) + [i+j for i in ascii_uppercase for j in ascii_uppercase]

def dil(v1,c1,v2):
    return (v1*c1)/v2 # c2

class liquid:
    def __init__(self, name, vol,conc=None):
        self.name = name
        self.vol = vol
        self.conc = conc
    def sample(self,vol):
        assert vol < self.vol
        self.vol -= vol
        return liquid(self.name, vol = vol, conc = self.conc)

class mixture:
    def __init__(self, *liquids):
        self.liquids = self.unpack(liquids)
    @property
    def vol(self):
        return sum([i.vol for i in self.liquids])
    @property
    def ratios(self):
        return {i.name:i.vol/self.vol for i in self.liquids}
    @property
    def concs(self):
        return {i.name:dil(i.vol,i.conc,self.vol) if i.conc != None else f'{100 * i.vol/self.vol} %v/v' for i in self.liquids}
    def unpack(self,liquids):
        # comprehension?
        o = []
        for i in liquids:
            if type(i) is liquid:
                o.append(i)
            elif type(i) is mixture:
                for j in i.liquids:
                    o.append(j)
        return o
    def sample(self, vol):
        assert vol < self.vol
        new_liquids = []
        for l,r in zip(self.liquids, self.ratios.values()):
            l.vol -= r * vol
            new_liquids.append(l.sample(r * vol))
        return mixture(*new_liquids)


class well:
    def __init__(self, contents = {}):
        self.contents = contents
        self.plate = None
        self.id = None
        self.maxvol = None
        self.minvol = None
    @property
    def vol(self):
        return sum(self.contents.values())
    def transfer(self, vol, dest):
        pass

class plate:
    def __init__(self, *wells, nwells = 384):
        assert nwells in plateSizes.keys()
        self.nwells = nwells
        self.dims = [plateSizes[self.nwells]['h'], plateSizes[self.nwells]['w']] # letters, numbers
        self.wells = self.assignWells(wells)
        self.array = [[0 for i in range(self.dims[1])] for i in range(self.dims[0])]
        for i in self.wells:
            h_pos, w_pos = self.loc(i)
            self.array[h_pos][w_pos] = self.wells[i]
    @property
    def wellIDs(self):
        return [plateLetters[i] + str(j) for i in range(self.dims[0]) for j in range(1,self.dims[1] + 1)]
    def loc(self, ID):
        # splits id and locates well in array
        letter = ''.join(re.findall('\D', ID))
        number = ''.join(re.findall('\d',ID))
        w_pos = int(number)
        h_pos = plateLetters.index(letter)
        return h_pos, w_pos #self.array[h_pos, w_pos]
    def assignWells(self, wells):
        # different assignment methods
        return {id:contents for id, contents in zip(self.wellIDs, wells)}
