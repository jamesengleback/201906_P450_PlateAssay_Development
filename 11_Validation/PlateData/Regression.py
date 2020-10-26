import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from tqdm import tqdm


def clean_data(path):
    data=pd.read_csv(path)
    data.drop(data.loc[(data['Final [Kpi]']==0) & (data['Final [Kcl]']==0)].index, inplace=True)
    data.drop(['Unnamed: 8','Unnamed: 0'],axis=1, inplace=True)
    data.drop(data.loc[data['R^2']==-np.inf].index,inplace=True)

    Y=data.loc[:,'R^2']
    #Y = data.loc[:,['vmax','Km','R^2' ]]

    X=data.loc[:,['Plate','Final [Kpi]','Final [Kcl]','Substrate']]
    plates=pd.get_dummies(X['Plate'])
    X=pd.concat([pd.get_dummies(X['Plate']),pd.get_dummies(X['Substrate']),X['Final [Kcl]'],X['Final [Kpi]']],\
    axis=1,join='inner')
    #Normalization
    X['Final [Kcl]']=X['Final [Kcl]']/X['Final [Kcl]'].max()
    X['Final [Kpi]']=X['Final [Kpi]']/X['Final [Kpi]'].max()
    return X, Y

def convert_to_torch(dataframe):
    return torch.tensor(dataframe.values,dtype=torch.float)

def make_model():
    model = nn.Sequential(nn.Linear(10,1))
    return model

def train_model(model,x,y):
    loss_function  = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr = 1e-3)
    lossrecord=[]
    for i in tqdm(range(10000)):
        yhat = model.forward(x)
        loss = loss_function(yhat, y)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        lossrecord.append(loss.data.numpy())
    model.eval()
    print 'Loss = ',loss.item()
    return lossrecord

def plotLoss(lossrecord):
    lossrecord=np.array(lossrecord)
    plt.ylabel('Loss')
    plt.xlabel('Interation')
    plt.plot(lossrecord)
    plt.title('Loss over time')
    plt.show()

def plot_model(Y,yhat):
    plt.scatter(Y,yhat)
    plt.xlim((0,1))
    plt.xlabel('Actual')
    plt.ylabel('Predicted')
    plt.title('Predicted vs Actual')
    plt.show()

def main():
    X,Y=clean_data('PlateValidationMetrix.csv')
    X_cols=X.columns
    X=convert_to_torch(X)
    Y=convert_to_torch(Y).reshape(-1,1)
    model = make_model()
    lossrec=train_model(model,X,Y)
    plotLoss(lossrec)
    plot_model(Y,model.forward(X).data.numpy())
    print(pd.DataFrame(model[0].weight.data.numpy(), columns=X_cols))
main()
