import numpy as np
from scipy import optimize


def calculate_response(data):
    return abs(data.loc[:, 420] - data.loc[:, 390])


def curve(x, vmax, km):
    y = (vmax*x)/(km + x)
    return y


def calculate_km(response, concs):
    params, cov = optimize.curve_fit(curve,
                                     concs,
                                     response,
                                     p0=[max(response), 250],
                                     bounds=(
                                         (0, 0),
                                         (max((abs(5*max(response)), 0.1)), np.inf)
                                         )
                                     )
    vmax = params[0]
    km = params[1]
    return vmax, km


def r_squared(y, y_hat):
    residuals = y - y_hat
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((y-np.mean(y))**2)
    r_squared = 1 - (ss_res / ss_tot)
    return r_squared
