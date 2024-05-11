import numpy as np 
import pandas as pd
import scipy

def scattering(data: pd.DataFrame):
    # fit x**-4 curve 
    pass

def linear_fit(x):
    # 1d array 
    (m, c), cov = scipy.optimize.curve_fit(lambda x, m, c: x*m + c,
                                           xdata=range(len(x)),
                                           ydata=x
                                           )
    return m, c

def dd_soret(diff_data: pd.DataFrame):
    between = diff_data.loc[:, 390:420].values
    m_c = np.array(list(map(linear_fit, between)))
    return m_c.mean()

def auc(data: pd.DataFrame):
    return np.trapz(data, axis=1, dx=1)

def std_405(data: pd.DataFrame):
    return data.loc[:, 405].std()
