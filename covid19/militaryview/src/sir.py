import numpy as np
from scipy.integrate import odeint
from scipy.signal import find_peaks
import matplotlib.dates as mdates
from scipy.optimize import minimize
from scipy.integrate import solve_ivp
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import pandas as pd
from datetime import date
import os
import time
import dataPreProcess as dataPre


def sirFunc(y, t, params):
    """
    Defines the differential equations for the SIR system.

    Input Arguments:
        y      : state vector of the state variables:
                  y = [-beta*S*I, beta*S*I - gamma*I, gamma*I]
        t      : time
        params : vector of the parameters:
                  params = [beta, gamma]
    """
    S, I, R = y
    beta, gamma, N = params

    f = [-beta*S*I/N,
          beta*S*I/N - gamma*I,
          gamma*I]

    return f

def sirFuncIVP(t, y, params):
    """
    Defines the differential equations for the SIR system.

    Input Arguments:
        y      : state vector of the state variables:
                  y = [-beta*S*I, beta*S*I - gamma*I, gamma*I]
        t      : time
        params : vector of the parameters:
                  params = [beta, gamma]
    """
    S, I, R = y
    beta, gamma, N = params

    f = [-beta*S*I/N,
          beta*S*I/N - gamma*I,
          gamma*I]

    return f

def sirModelInit(N=None,I0=None,D0=None,beta0=None, gamma0=None, cases=None, numDaysToSim=None, abserr = 1.0e-8, relerr = 1.0e-6):
    S0     = N - I0 - D0
    R0     = D0
    y0     = [S0, I0, R0] # S[0], I[0], R[0]
  
    optParams = minimize(sqloss, [beta0, gamma0], args=(cases, y0, N, numDaysToSim, abserr, relerr), method='L-BFGS-B', bounds=[(0.00000001, 0.5), (0.00000001, 0.5)])
    
    return optParams.x

def runSIR(N=None, beta=None, gamma=None, numDays=None, y0=None, abserr = 1.0e-8, relerr = 1.0e-6):
    
    params = [beta, gamma, N]
    
    t = np.arange(0,numDays)    
    
    # Call the ODE solver.
    y = odeint(sirFunc, y0, t, args=(params,), atol=abserr, rtol=relerr)
    S = y[:,0]
    I = y[:,1]
    R = y[:,2]
    
    return S,I,R
    
def sqloss(paramsForOpt, cases, y0, N, numDaysToSim, abserr, relerr):
    beta   = paramsForOpt[0]
    gamma  = paramsForOpt[1]
    params = [beta, gamma, N]
    
    # Time samples to use for ODE solver.
    t = np.arange(0,numDaysToSim)        
    
    # Call the ODE solver.
    y = odeint(sirFunc, y0, t, args=(params,), atol=abserr, rtol=relerr)
    S = y[:,0]
    I = y[:,1]
    R = y[:,2]
    
    estCases = I[0:len(cases)] + R[0:len(cases)]

    return (np.linalg.norm(cases - estCases)) **2


def calculate_sir(counties, states):
    # os.chdir('/home/ubuntu/api/Code')
    covidDataDir    = "Data/covid_kaggle/"
    covidFileName   = "usa_county_wise.csv"
    censusDataDir   = "Data/census/"
    censusFileName  = "PEP_2018_PEPAGESEX_with_ann.csv"
    
    labelRotDeg     = 60
    timeMultFac     =  5
    numCasesToStart = 10
    betaInit        = 0.19
    gammaInit       = 0.07
    perctSocialDist = .4        # 1-% implies % effective
    perctHospital   = .03       # % of infected that get hospitalized
    perctICU        = .0045     # % of hospitalized that go into ICU
    perctVent       = .004      # % of ICU that need vents.
    
    countyName = counties
    stateName = states

    # Date range to use to estimate SIR model parameters
    estStartDate = '2020-03-01'
    estStopDate  = '2020-04-09'
    
    # Date to show projections
    projStartDate = '2020-03-01'
    projStopDate  = '2020-04-09'
    
    # Read in the COVID-19 data for the estimated and projected dates
    start_csvs = time.time()
    estCovid, projCovid, N = dataPre.readCSVs(covidDataDir+covidFileName, 
                                            censusDataDir+censusFileName, 
                                            stateName, 
                                            countyName, 
                                            estStartDate, 
                                            estStopDate, 
                                            projStartDate, 
                                            projStopDate)
    print(f"readCSVs took {time.time() - start_csvs:.02f}s")
    
    # Use the data to estimate parameters for running the SIR model.
    cases     = estCovid['Confirmed'].values
    deaths    = estCovid['Deaths'].values
    
    # Find the first case idx
    startIdx = 0
    for c in cases:
        if(c > numCasesToStart):
            break
        startIdx += 1


    cases  = np.asarray(cases[startIdx:])
    deaths = np.asarray(deaths[startIdx:])
    estCovid.drop(estCovid.index[0:startIdx],axis=0,inplace=True)
    
    cases     = estCovid['Confirmed'].values
    deaths    = estCovid['Deaths'].values
    numDaysToSim = int(timeMultFac*estCovid.shape[0])
    sirModelInit_time = time.time()
    estParams = sirModelInit(N,cases[0],deaths[0],betaInit, gammaInit, cases+deaths, numDaysToSim)
    print(f"sirModelInit took {time.time() - sirModelInit_time:.02f}s")
    
    #beta, gamma, S0 = estParams
    beta, gamma = estParams
    R0     = beta/gamma
    # print("beta = ",beta)
    # print("gamma = ",gamma)
    # print("R0 = ",R0)

    # Run SIR model using estimated parameters
    # Make sure to run the model for the dates of the projection
    initI = estCovid['Confirmed'][0]
    initR = estCovid['Deaths'][0]
    
    y0    = [N-initI-initR,initI,initR]
    runSIR_time = time.time()
    S,I,R = runSIR(N, beta, gamma, numDaysToSim, y0)
    print(f"runSIR_time took {time.time() - runSIR_time:.02f}s")

    # Find peak in infection curve.
    optIdx = np.argmax(I)
    
    endSIRTimestamp   = estCovid.index[0] + pd.Timedelta(days=numDaysToSim)
    dateTimeVec = np.linspace(estCovid.index[0].value, endSIRTimestamp.value, int(timeMultFac*estCovid.shape[0]))
    dateTimeVec = pd.to_datetime(dateTimeVec)

    sir_model = pd.DataFrame()
    sir_model['date'] = dateTimeVec 
    sir_model['date'] = sir_model['date'].dt.strftime('%m/%d/%Y')
    sir_model['S'] = S
    sir_model['I'] = I
    sir_model['R'] = R
    sir_model['hospitalization'] = perctHospital*I
    sir_model['icu'] = perctICU*I
    sir_model['ventilator'] = perctVent*I
    # sir_model.to_csv('sir_model.csv', index=False)
    
    return sir_model, R0

if __name__ == "__main__":
    sir_model, R0 = calculate_sir(None, 'All')
