import ROOT
from matplotlib.ticker import MaxNLocator
import numpy as np
import glob
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import json
import collections

sns.set_context('poster')
sns.set(font_scale=1.4)

LEDNUM = 6
DATEDB = "./DB/RunDateLED%i.json"%(LEDNUM)
GAINDB = "./DB/TransparencyGains.json"
DATAPATH = "./data/Transparency/LED%i/"%(LEDNUM)

# ratios per channel, same order as TUBES, default/original voltages
CHARGE_MEAN_RATIOS = [1.538859874,	1.311711584,	1.998275689,	3.118397926,	1.112314599,	2.154926575,	1.767571333] 



if __name__ == "__main__":
    TUBES = [356,364,365,368,370,357,367] #360 has low gain, high uncertainty on fit
    intensity_bases = {}
    relative_intensities = [1.0]
    relative_intensity_stdevs = [0.0]
    alldata = {"run":[], "LED":[], "date":[],"channel":[],
            "relative_mean":[], "charge_mean":[],"QPerPE":[],
            "QPerPEUnc":[]}
    
    data = None
    with open(DATEDB,"r") as f:
        data = json.load(f, object_pairs_hook=collections.OrderedDict)
    gaindata = None
    with open(GAINDB,"r") as f:
        gaindata = json.load(f)
    gd = pd.DataFrame(gaindata["Gauss2"])
    original = True

    for j,date in enumerate(data): # iterate over runs
        print(date)
        if date == "2020/11/13": # check if run was taken with original or default voltages (before 2020/11/13 = original)
              original = False
        r = int(data[date])
        myfile= ROOT.TFile.Open("%sLEDRun%iS0LED%i_AllPMTs_Run-1.root"%(DATAPATH,r,LEDNUM))
        these_means = []
        tcount = 0
        for t in TUBES: # iterate over PMTs 
            myhist = myfile.Get("hist_charge_%i"%(t))
            themean = myhist.GetMean()
            if j==0: # the first date
                alldata["run"].append(r)
                alldata["LED"].append(LEDNUM)
                alldata["date"].append(date)
                alldata["channel"].append(t)
                alldata["charge_mean"].append(themean*CHARGE_MEAN_RATIOS[tcount]) # scale to match data taken at this PMT's default voltage
                alldata["QPerPE"].append(gd.loc[gd["Channel"] == t, 'c1Mu'].mean())
                alldata["QPerPEUnc"].append(gd.loc[gd["Channel"] == t, 'c1Mu'].std())
                alldata["relative_mean"].append(1.0) # for normalizing to first day
                intensity_bases[t] = themean*CHARGE_MEAN_RATIOS[tcount] # scale to match data taken at this PMT's default voltage
            elif original: # if this data was taken with original voltages
                alldata["run"].append(r)
                alldata["LED"].append(LEDNUM)
                alldata["date"].append(date)
                alldata["channel"].append(t)
                alldata["QPerPE"].append(gd.loc[gd["Channel"] == t, 'c1Mu'].mean())
                alldata["QPerPEUnc"].append(gd.loc[gd["Channel"] == t, 'c1Mu'].std())
                alldata["charge_mean"].append(themean*CHARGE_MEAN_RATIOS[tcount]) # scale to match data taken at this PMT's default voltage
                alldata["relative_mean"].append(themean/intensity_bases[t]*CHARGE_MEAN_RATIOS[tcount]) # scale to match data taken at this PMT's default voltage
            else: # no corrections to data taken with default voltages
                alldata["run"].append(r)
                alldata["LED"].append(LEDNUM)
                alldata["date"].append(date)
                alldata["channel"].append(t)
                alldata["QPerPE"].append(gd.loc[gd["Channel"] == t, 'c1Mu'].mean())
                alldata["QPerPEUnc"].append(gd.loc[gd["Channel"] == t, 'c1Mu'].std())
                alldata["charge_mean"].append(themean) 
                alldata["relative_mean"].append((themean/intensity_bases[t]))
                for i in gd.loc[gd["Channel"] == t, 'c1Mu']:
                    if i == 0:
                        print("WE GOT A ZERO VALUE! Run: " + r) #BAMBOOZLE	 
            tcount += 1

    #print("RELATIVE MEANS:")
    #print(alldata["relative_mean"])
    ndpd = pd.DataFrame(alldata)
    ndpd['date']=pd.to_datetime(ndpd['date'], format='%Y/%m/%d')

    #Plot1
    fig = plt.figure()
    ax = sns.barplot(x='date',y='relative_mean',estimator=np.mean,
            data=ndpd)
    ax.set_xlabel("Date") 
    ax.set_ylabel("Charge mean average, relative to first day") 
    plt.xticks(rotation='vertical',fontsize=10)
    plt.title(("Average of ETEL charge means (all PMTs normalized to first day)\n" +
        "LED %i only (PIN 3500)"%(LEDNUM)))
    plt.show()

    #Plot2
    fig = plt.figure()
    ax = sns.pointplot(x='date',y='charge_mean',hue='channel',
            data=ndpd)
    ax.set_xlabel("Date") 
    ax.set_ylabel("PMT charge mean (nC)") 
    plt.xticks(rotation='vertical',fontsize=12)
    plt.title(("Mean of charge distribution from ETEL tubes flashed with \n" +
        "LED %i only (PIN 3500)"%(LEDNUM)))
    plt.show()

    #Plot3
    fig = plt.figure()
    ax = sns.pointplot(x='date',y='relative_mean',hue='channel',
            data=ndpd)
    ax.set_xlabel("Date") 
    ax.set_ylabel("PMT charge mean, normalized to first day") 
    plt.xticks(rotation='vertical')
    plt.title(("ETEL charge means (normalized to first day) \n" +
        "LED %i only (PIN 3500)"%(LEDNUM)))
    plt.show()

    #Plot4
    fig,ax = plt.subplots()
    #ndpd["PE"] = ndpd["charge_mean"]/ndpd["QPerPE"]
    #ndpd["PEUnc"] = (ndpd["charge_mean"]/(ndpd["QPerPE"]**2))*ndpd["QPerPEUnc"]
    
    ndpd["PE"] = ndpd["charge_mean"]/ndpd["QPerPE"]
    ndpd["PEUnc"] = (ndpd["charge_mean"]/(ndpd["QPerPE"]**2))*ndpd["QPerPEUnc"]
    dates = []
    date_sums = []
    date_stdevs = []
    default = False
    for j,date in enumerate(data):
        if date == "2020/11/13":
                default = True 
        dates.append(date)
        print("RESULT IS: ")
        print(ndpd.loc[ndpd["date"] == date, 'PE'])
        date_sums.append(float((ndpd.loc[(ndpd["date"] == date), 'PE'].sum()))) # Locate the total PE for each date, add to list of date_sums (y values)
        QToPE_err = np.linalg.norm((ndpd.loc[(ndpd["date"] == date), 'PEUnc']))
        IErr = np.sqrt((date_sums[j]*0.005)**2)
        date_stdevs.append(np.sqrt(QToPE_err**2 + IErr**2))

    #?fig,ax = plt.subplots()
    dates = pd.to_datetime(dates)
    ax.scatter(dates, date_sums, color='purple', alpha=0.5)
    min_limit=min(0, min(date_sums))
    ax.set_ylim(min_limit, max(date_sums)+10)
    #ax.bar(dates,date_sums,yerr=date_stdevs,alpha=0.5,color='purple',ecolor='black')
    measurement_dates=pd.to_datetime(ndpd["date"].unique())
   
    def closest_spaced_dates(dates, num_dates):
        evenly_spaced = pd.date_range(start=dates.min(), end=dates.max(), periods=num_dates)
        return pd.Series([min(dates, key=lambda d: abs(d-esp_date)) for esp_date in evenly_spaced]).unique()

    num_x_ticks=12
    subset_dates=closest_spaced_dates(measurement_dates, num_x_ticks)
    #ax.set_xticks(dates)
    ax.set_xticks(subset_dates)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

    #make the x axis legible
    '''
    every_nth = 20
    for n,label in enumerate(ax.xaxis.get_ticklabels()):
        if n % 1 == 0:
                label.set_visible(False)
    for n,label in enumerate(ax.xaxis.get_ticklabels()):
        if n % every_nth == 0:
            label.set_visible(True)
    '''
    ax.set_xlabel("Date") 
    ax.set_ylabel("Total PE per flash")
    plt.xticks(rotation='vertical',fontsize=12)
    plt.title(("Total PE seen by 7 top tubes per LED flash \n" +
        " LED %i only"%(LEDNUM)))
    plt.show()
    
    fig,ax = plt.subplots()
    for cnum in TUBES:
        myx = []
        myy = []
        myyerr = []
        for j,date in enumerate(data):
            myx.append(date)
            myy.append(float(ndpd.loc[((ndpd["date"] == str(date)) & (ndpd["channel"] == cnum)), "PE"])),
            myyerr.append(float(ndpd.loc[((ndpd["date"] == str(date)) & (ndpd["channel"] == cnum)), "PEUnc"]))
        ax.errorbar(myx,myy,yerr=myyerr,alpha=0.8,label=cnum,linestyle='None',marker='o',markersize=6)
    ax.set_xlabel("Date")

    leg = ax.legend(loc=1,fontsize=15)
    leg.set_frame_on(True)
    leg.draw_frame(True)
    ax.set_xlabel("Date") 
    ax.set_ylabel("PEs") 
    plt.xticks(rotation='vertical',fontsize=10)
    plt.title(("Average PE seen per LED flash \n" +
        "LED %i only (PIN 3500)"%(LEDNUM)))
    plt.show()
