import torch
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from tqdm import tqdm

def r_squared_torch(y,yh):
    residuals = y-yh
    ss_res = (residuals**2).sum()
    ss_tot = ((y-y.mean())**2).sum()
    r_squared = 1 - (ss_res / ss_tot)
    return r_squared

    
    
def FitMichaelisMenten(x,y):
    x = torch.tensor(x,dtype=torch.float) # concs are numpy array, 500 is max conc
    y = torch.tensor(y,dtype=torch.float) # Diffdiff is pd.series, 500 is max conc
    km = torch.tensor([0.5],requires_grad=True,dtype=torch.float)
    vmax = torch.tensor([0.5],requires_grad=True,dtype=torch.float)
    optimizer = torch.optim.Adam({km,vmax},lr = 1e-2)
    loss_fn =  r_squared_torch
    for i in range(5_000):
        y_pred = (vmax*0.05*x)/(km*500 + x) # scaling
        loss = 1 - loss_fn(y,y_pred) # 1 - r squared
        if km <0:
            # making sure that Km isn't negative
            loss -= km.item()
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
    return (km*500).item(), (vmax*0.05).item(), loss.item()

def GenerateMichaelisMenten(kd, vmax, noise, k, nPoints):
    x = (np.linspace(0,1,nPoints)**k)*500
    y = (vmax*x)/(kd + x)
    y = np.array([i + np.random.normal(0,noise) for i in y])
    return x, y
    
    
def main():
    # Fake data
    data = pd.DataFrame([],columns = ['Kd','vmax','Noise','K','nPoints'])
    
    for i in tqdm(range(1000)):
        kd = np.random.uniform(0,100)
        vmax = np.random.uniform(0,1)
        noise = np.random.uniform(0,0.1)
        K = np.random.uniform(1,4)
        nPoints = np.random.randint(1,10)
        temp = pd.DataFrame([[kd, vmax, noise,K,nPoints]],columns = ['Kd','vmax','Noise','K','nPoints'])
        data = data.append(temp)
        
    data.reset_index(inplace = True, drop = True)
    data.to_csv('/DATA/james/MonteCarloMichaelisMenten_x.csv')
    
    results = pd.DataFrame([],columns = ['Kd','vmax','R Squared'])
    for i in tqdm(data.index):
        kd, vmax, noise, k, nPoints= data.loc[i,'Kd'],data.loc[i,'vmax'],data.loc[i,'Noise'],data.loc[i,'K'],data.loc[i,'nPoints']
        x,y = GenerateMichaelisMenten(kd, vmax, noise, k,nPoints)
        kd_pred, vmax_pred, loss = FitMichaelisMenten(x,y)
        temp = pd.DataFrame([[kd_pred, vmax_pred, 1-loss]],columns = ['Kd','vmax','R Squared'])
        results = results.append(temp)
        
    results.reset_index(inplace = True, drop = True)
    results.to_csv('/DATA/james/MonteCarloMichaelisMenten_y.csv')
     
if __name__ == '__main__':
    main()
