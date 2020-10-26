# James run this in python 2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from rdkit import Chem
from rdkit.Chem.Fingerprints import FingerprintMols
from rdkit import DataStructs

def data_2_Fingerprints(path):
    smiles_column_name = 'SMILES'
    # change here if it's lowercase or something
    data = pd.read_csv(path)
    smiles = data[smiles_column_name]
    mols = pd.Series([Chem.MolFromSmiles(i) for i in smiles])
    fingerprints = pd.Series([FingerprintMols.FingerprintMol(i) for i in mols])
    fingerprints.index = data['Name']

    return fingerprints


def pairwise_matrix(fingerprints, plot):
    list2 = []
    for i in fingerprints:
        list1 =[]
        for j in fingerprints:
            list1.append(DataStructs.DiceSimilarity(i,j))
        list2.append(list1)

    distance_matrix = np.array(list2)
    if plot == True:
        plt.figure(figsize = (10,10))
        plt.set_cmap('magma')
        plt.imshow(distance_matrix)
        plt.title('Pairwise similarity between compounds')
        #plt.yticks(np.arange(len(fingerprints)), fingerprints.index, fontsize = 2, rotation = 0)
        plt.colorbar()
        plt.show()

#############

fps = data_2_Fingerprints('~/Desktop/Work/Datasets/Chemical_Libs/HRAC_Herbicides.csv')
pairwise_matrix(fps, True)
