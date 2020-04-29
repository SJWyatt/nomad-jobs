import os
import pandas as pd
import numpy as np
import time
from datetime import datetime
from tqdm import tqdm

def to_epoch_ymd(dt_format):
    epoch = int((datetime.strptime(dt_format, "%Y-%m-%d") - datetime(1970, 1, 1)).total_seconds()) * 1000
    return epoch

def loadCSVs(dataFile, censusFile):
    # Read in the covid data for the estimation and projection date ranges
    print("Loading usaDf...")
    
    # read in the data for each county
    colToRead     = ['Admin2','Province_State','Date','Confirmed','Deaths']
    usaDf         = pd.read_csv(dataFile, usecols=colToRead, parse_dates=True)

    # rename columns
    usaDf.dropna(axis='index',inplace=True)
    usaDf.rename(columns={'Admin2':'County','Province_State':'State'},inplace=True)

    # convert to datetime object
    usaDf['Date'] = pd.to_datetime(usaDf['Date'])

    # create an array of dates
    usaDfTimes = np.asarray([to_epoch_ymd(thetime.strftime("%Y-%m-%d")) for thetime in usaDf['Date']])
    print("Finished loading usaDf.")

    # Read in the census date for the current location
    print("Loading censusDf...")
    colToRead      = ['Geography','Population Estimate (as of July 1) - 2018 - Both Sexes; Total']
    censusDf       = pd.read_csv(censusFile, usecols=colToRead, encoding = 'ISO-8859-1')
    censusDf.dropna(axis='index',inplace=True)

    # new data frame with split value columns 
    splitNameDf1 = censusDf[colToRead[0]].str.split("County,", n = 1, expand = True)
    #splitNameDf2 = splitNameDf1[0].str.split(" ", n = 1, expand = True)

    try:
        splitNameDf_cities = censusDf[colToRead[0]].str.split("city,", n = 1, expand = True) 
        censusDf['CountyBackup'] = splitNameDf_cities[0]
        censusDf['StateBackup'] = splitNameDf_cities[1]
        censusDf['CountyBackup'] = censusDf['CountyBackup'].str.strip()
        censusDf['StateBackup'] = censusDf['StateBackup'].str.strip()
    except Exception:
        print("Error loading backup Counties!")

    try:
        splitNameDf_cities_2 = censusDf[colToRead[0]].str.split(",", n = 1, expand = True) 
        censusDf['CountyBackup2'] = splitNameDf_cities_2[0]
        censusDf['StateBackup2'] = splitNameDf_cities_2[1]
        censusDf['CountyBackup2'] = censusDf['CountyBackup2'].str.strip()
        censusDf['StateBackup2'] = censusDf['StateBackup2'].str.strip()
    except Exception:
        print("Error loading secondary backup Counties!")

    censusDf['State'] = splitNameDf1[1]
    censusDf['County'] = splitNameDf1[0]
    censusDf.drop(columns='Geography', inplace=True)
    censusDf.rename(columns={colToRead[1]:'Total Population'}, inplace=True)
    censusDf = censusDf[['State', 'County', 'StateBackup', 'CountyBackup', 'StateBackup2', 'CountyBackup2', 'Total Population']]
    censusDf['State'] = censusDf['State'].str.strip()
    censusDf['County'] = censusDf['County'].str.strip()
    print("Finished loading censusDf.")

    return usaDf, censusDf, usaDfTimes

current_dir = os.getcwd()
dataFile = current_dir+"/Data/covid_kaggle/usa_county_wise.csv"
censusFile = current_dir+"/Data/census/PEP_2018_PEPAGESEX_with_ann.csv"
usaDf, censusDf, usaDfTimes = loadCSVs(dataFile, censusFile)

def readCSVs(covidFile=None, censusFile=None, stateName=None, countyName=None, estStartDate=None, estStopDate=None, 
             projStartDate=None, projStopDate=None):
    
    estStartDate = to_epoch_ymd(estStartDate)
    estStopDate = to_epoch_ymd(estStopDate)
    projStartDate = to_epoch_ymd(projStartDate)
    projStopDate = to_epoch_ymd(projStopDate)
    
    # Process national
    if(stateName == 'USA'):
        mask1  = np.logical_and((usaDfTimes >= estStartDate), (usaDfTimes <= estStopDate))
        mask2  = np.logical_and((usaDfTimes >= projStartDate), (usaDfTimes <= projStopDate))
        estStateDf  = usaDf.loc[mask1]
        projStateDf = usaDf.loc[mask2]
    else:
        # Process states only
        if(countyName == None):
            estAllStates  = []
            projAllStates = []
            for i in tqdm(np.arange(0,len(stateName)), "Getting states..."):
                mask1  = np.logical_and((usaDfTimes >= estStartDate), (usaDfTimes <= estStopDate)) & (usaDf['State']==stateName[i])
                mask2  = np.logical_and((usaDfTimes >= projStartDate), (usaDfTimes <= projStopDate)) & (usaDf['State']==stateName[i])
                tempStateDf = usaDf.loc[mask1]
                estAllStates.append(tempStateDf)
                tempStateDf = usaDf.loc[mask2]
                projAllStates.append(tempStateDf)
            
            estStateDf  = pd.concat(estAllStates)
            projStateDf = pd.concat(projAllStates)
        
        # Process counties in corresponding states
        else:
            estAllCounties  = []
            projAllCounties = []
            for i in tqdm(np.arange(0,len(countyName)), "Getting counties..."):
                mask1  = np.logical_and((usaDfTimes >= estStartDate), (usaDfTimes <= estStopDate)) & (usaDf['County']==countyName[i]) & (usaDf['State']==stateName[i])
                mask2  = np.logical_and((usaDfTimes >= projStartDate), (usaDfTimes <= projStopDate)) & (usaDf['County']==countyName[i]) & (usaDf['State']==stateName[i])
                tempCountyDf = usaDf.loc[mask1]
                estAllCounties.append(tempCountyDf)
                tempCountyDf = usaDf.loc[mask2]
                projAllCounties.append(tempCountyDf)
            
            estStateDf  = pd.concat(estAllCounties)
            projStateDf = pd.concat(projAllCounties)
        
    
    estStateDf    = estStateDf[['Date','State','County','Confirmed','Deaths']]
    estCovidTots  = estStateDf.groupby('Date')[['Confirmed','Deaths']].sum()
    projStateDf   = projStateDf[['Date','State','County','Confirmed','Deaths']]
    projCovidTots = projStateDf.groupby('Date')[['Confirmed','Deaths']].sum()

    # Get total population for the state/county
    if(stateName == 'USA'): 
        totalPop = censusDf['Total Population'].sum()
    else:
        # Process states only
        if(countyName == None):
            statePop = []
            for i in np.arange(0,len(stateName)):
                cPop = censusDf[(censusDf['State']==stateName[i])]['Total Population'].sum()
                #print(stateName[i], stateName[i], ' ', cPop)
                statePop.append(cPop)
            totalPop = sum(statePop)    
        # Process counties in corresponding states
        else:

            countyPop = []
            for i in np.arange(0,len(countyName)):
                cPop = censusDf[(censusDf['County']==countyName[i]) & (censusDf['State']==stateName[i])]['Total Population'].sum()
                try:
                    if (cPop == 0):
                        the_county = censusDf[(censusDf['CountyBackup']==countyName[i]) & (censusDf['StateBackup']==stateName[i])]
                        cPop = the_county['Total Population'].sum()
                except:
                    print("Error loading backup Counties!")
                
                try:
                    if (cPop == 0):
                        print("Getting backup2 counties (%s)"%(countyName[i],))
                        the_county = censusDf[(censusDf['CountyBackup2']==countyName[i]) & (censusDf['StateBackup2']==stateName[i])]
                        print("County Data:", the_county.head(5))
                        cPop = the_county['Total Population'].sum()
                except:
                    print("Error loading backup2 Counties!")

                if (cPop == 0):
                    print("!! Population of %s, %s == %d !!"%(countyName[i], stateName[i], cPop))

                countyPop.append(cPop)
            totalPop = sum(countyPop)

    # print("Total Population:", totalPop)
    
    return estCovidTots, projCovidTots, totalPop
