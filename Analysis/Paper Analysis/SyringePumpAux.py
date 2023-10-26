import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib import cm
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
from matplotlib import colors
import matplotlib as mpl
from pathlib import Path
from scipy import stats

figureTargetFolder = Path(r"C:\Users\bruno.cruz\Downloads\ExperimentalData\Figures")
def saveFigure(fig, title = None, rootSaveFolder = figureTargetFolder):
    if title is None:
        title = fig.gca().get_title()
    print(rootSaveFolder / (title + '.pdf' ))
    fig.savefig(rootSaveFolder / (title + '.pdf' ))
    return None


def parseFileName(inPathObject):
    f = inPathObject
    StrSplited = f.with_suffix('').name.split("_")
    outDict = {
    "fullDir" : f,
    "fName" : f.with_suffix('').name,
    "PumpID" : StrSplited[0] + "_" + StrSplited[1],
    "SyringeID" : StrSplited[2] + "_" + StrSplited[3],
    "NSteps" : int(StrSplited[4].replace('steps', '')),
    "StepSize" : StrSplited[5].split('Step')[0],
    "Date" : f.with_suffix('').name.split('Step')[1],
    };
    return outDict





def LoadAndExtractData(inPath, 
                       Fs = 20, 
                       stepWin = np.array([-1,15]), 
                       baselineWin = np.array([-1, -0.1]),
                       finalVolumeWindow = np.array([1, 3]), 
                       ratioFinalVolume = 0.95
                      ):
    # Load Data and the correct field
    rawData = pd.read_csv(inPath, sep = "\t")
    lengthOfLiquid = rawData["Item2.MajorAxisLength"].to_numpy()

    # Try to use the TTL to determine each trial start, if this fails use the derivative of the volume
    try:
        ttl = rawData.Item5 > np.mean(rawData.Item5)
        TTL_ERROR_FLAG = False
    except:
        print("Could not use the TTL to determine trial START")
        TTL_ERROR_FLAG = True
        ttl = np.diff(lengthOfLiquid) > 5.0 * np.std(np.diff(lengthOfLiquid))

    pulseStart = np.where(np.diff(ttl.astype(int)) == 1)[0]
    pulseStart = pulseStart[0:]

    blSamples = baselineWin * Fs
    win_s = stepWin * Fs
    finalVolumeWindow = finalVolumeWindow * Fs

    windows2grab = pulseStart[:, np.newaxis] + win_s[np.newaxis,:]

    while (windows2grab[-1,1] >  len(lengthOfLiquid)):
        print(windows2grab.shape)
        windows2grab  = windows2grab[:-1,:]
        pulseStart = pulseStart[:-1]

    blWin = pulseStart[:, np.newaxis] + blSamples[np.newaxis,:].astype(int)
    finalVolumeWindow = pulseStart[:, np.newaxis] + finalVolumeWindow[np.newaxis,:].astype(int)

    ts_aligned = np.linspace(stepWin[0], stepWin[1], np.diff(stepWin)[0]*Fs + 1)[0:-1]

    dAligned = np.zeros((len(pulseStart), len(ts_aligned)))
    finalVolume = np.zeros(len(pulseStart))
    timeFinalVolume = np.zeros(len(pulseStart))



    for iRow,RowData in enumerate(windows2grab):
        dAligned[iRow,:] = lengthOfLiquid[RowData[0]: RowData[1]]
        dAligned[iRow,:] = dAligned[iRow,:]  - np.nanmean(
            lengthOfLiquid[blWin[iRow,0]: blWin[iRow,1]])
        finalVolume[iRow] = np.nanmean(lengthOfLiquid[finalVolumeWindow[iRow,0]: finalVolumeWindow[iRow,1]]) - \
            np.nanmean(lengthOfLiquid[blWin[iRow,0]: blWin[iRow,1]])
        timeFinalVolume[iRow] = np.argmin(np.abs(
            lengthOfLiquid[pulseStart[iRow] : finalVolumeWindow[iRow,1]] - np.nanmean(lengthOfLiquid[blWin[iRow,0]: blWin[iRow,1]]) - \
                ratioFinalVolume*finalVolume[iRow]))

    meanDeliveryTrace = np.nanmean(dAligned,axis=0)
    timeFinalVolume = timeFinalVolume/Fs
    pulseStart_seconds = pulseStart/Fs
    pulseStart_diff = np.concatenate([[np.nan], np.diff(pulseStart_seconds)])
    data = {"rawData": rawData,
        "pulseStart": pulseStart,
        "lengthOfLiquid": lengthOfLiquid,
        "fs":Fs,
        "stepWin": stepWin,
        "baselineWin":baselineWin,
        "finalVolumeWin":finalVolumeWindow,
        "ratioFinalVolume":ratioFinalVolume,
        "ts_aligned":ts_aligned,
        "pulseStart_diff":pulseStart_diff,
        "volumeAligned":dAligned,
        "finalVolume":finalVolume,
        "timeFinalVolume":timeFinalVolume,
        "fileName":inPath,
        "TTL_ERROR_FLAG":TTL_ERROR_FLAG}
    return data

def plot_single_session(row, axs = None, fig = None):
    if axs is None:
        axs = plt.gca()
    if fig is None:
        fig = plt.figure(figsize=(4, 3))
    sessionCmap = cm.get_cmap('rainbow', row["volumeAligned"].shape[0])
    ts_aligned = row["ts_aligned"]
    for ii, trialData in enumerate(row["volumeAligned"]):
        axs.plot(ts_aligned,trialData, lw = 1, color = sessionCmap(ii))

    meanDeliveryTrace = np.mean(row["volumeAligned"], axis=0)
    axs.plot(ts_aligned,meanDeliveryTrace, lw = 3, color = 'black')
    axs.grid(linestyle='-', linewidth=0.5, which = 'both', markevery = (0,1 ,0.5))
    axs.set_ylim(bottom=0)
    axs.set_xlim(row["stepWin"])
    axs.set_ylabel(r'$\Delta$ Volume (capillary x-section)')
    axs.set_xlabel('Time since pulse (s)')
    axs.tick_params(labelcolor='k', top=False, bottom=True, left=True, right=False)
    plt.rc('font', family='serif')
    plt.rc('xtick', labelsize='medium')
    plt.rc('ytick', labelsize='medium')

    bounds = np.linspace(1, row["volumeAligned"].shape[0], row["volumeAligned"].shape[0])
    norm = colors.BoundaryNorm(bounds, sessionCmap.N)
    tempAxes = fig.add_axes([axs.get_position().x0,
        axs.get_position().y0 + axs.get_position().height + 0.02,
        axs.get_position().width, 0.03])
    cb = mpl.colorbar.ColorbarBase(tempAxes, cmap=sessionCmap,
                                    orientation='horizontal',norm=norm,
                                    spacing='proportional', ticks=bounds[[0,-1]],
                                    boundaries=bounds, format='%1i')

    axins = axs.inset_axes([0.6, 0.1, 0.3, 0.3])
    for ii, trialData in enumerate(row["volumeAligned"]):
        axins.plot(ts_aligned,trialData, lw = 1, color = sessionCmap(ii))

    y_min, y_max = axs.get_ylim()
    # sub region of the original image
    x1, x2, y1, y2 = -0.2, 1, 0, y_max
    axins.set_xlim(x1, x2)
    axins.set_ylim(y1, y2)
    axins.tick_params(labelcolor='k', top=False, bottom=True, left=True, right=False)
    return(axs, fig)


def plot_multiple_sessions(rows, axs = None, fig = None):
    if axs is None:
        axs = plt.gca()
    if fig is None:
        fig = plt.figure(figsize=(4, 3))
    trialSize = np.stack(rows.head(1)["volumeAligned"]).shape[2]
    nTrials = rows.apply(lambda row : row["volumeAligned"].shape[0], axis = 1)
    maxTrials = np.max(nTrials)
    sessionCmap = cm.get_cmap('rainbow', maxTrials)

    AllTrials = np.reshape(np.stack(rows["volumeAligned"].to_numpy(), axis = 0), [-1, trialSize])

    for jj, row in rows.iterrows():
        ts_aligned = row["ts_aligned"]
        for ii, trialData in enumerate(row["volumeAligned"]):
            axs.plot(ts_aligned,trialData, lw = 2, color = sessionCmap(ii))

    meanDeliveryTrace = np.mean(AllTrials, axis=0)
    axs.plot(ts_aligned,meanDeliveryTrace, lw = 3, color = 'black')
    axs.grid(linestyle='-', linewidth=0.5, which = 'both', markevery = (0,1 ,0.5))
    axs.set_ylim(bottom=0)
    axs.set_xlim(row["stepWin"])
    axs.set_ylabel(r'$\Delta$ Volume (capillary x-section)')
    axs.set_xlabel('Time since pulse (s)')
    axs.tick_params(labelcolor='k', top=False, bottom=True, left=True, right=False)
    plt.rc('font', family='serif')
    plt.rc('xtick', labelsize='medium')
    plt.rc('ytick', labelsize='medium')

    bounds = np.linspace(1, maxTrials, maxTrials)
    norm = colors.BoundaryNorm(bounds, sessionCmap.N)
    tempAxes = fig.add_axes([axs.get_position().x0,
        axs.get_position().y0 + axs.get_position().height + 0.02,
        axs.get_position().width, 0.03])
    cb = mpl.colorbar.ColorbarBase(tempAxes, cmap=sessionCmap,
                                    orientation='horizontal',norm=norm,
                                    spacing='proportional', ticks=bounds[[0,-1]],
                                    boundaries=bounds, format='%1i')

    axins = axs.inset_axes([0.6, 0.1, 0.3, 0.3])
    for jj, row in rows.iterrows():
        for ii, trialData in enumerate(row["volumeAligned"]):
            axins.plot(ts_aligned,trialData, lw = 1, color = sessionCmap(ii))

    y_min, y_max = axs.get_ylim()
    # sub region of the original image
    x1, x2, y1, y2 = -0.2, 1, 0, y_max
    axins.set_xlim(x1, x2)
    axins.set_ylim(y1, y2)
    axins.tick_params(labelcolor='k', top=False, bottom=True, left=True, right=False)
    return(axs, fig)

def plot_volume_aligned(rows, axs = None, fig = None, inColor = (0,0,0), singleColor = (0.8,0.8,0.8), alpha = 0.1):
    if axs is None:
        axs = plt.gca()
    if fig is None:
        fig = plt.figure(figsize=(4, 3))
    trialSize = np.stack(rows.head(1)["volumeAligned"]).shape[2]
    nTrials = rows.apply(lambda row : row["volumeAligned"].shape[0], axis = 1)
    maxTrials = np.max(nTrials)

    AllTrials = np.reshape(np.stack(rows["volumeAligned"].to_numpy(), axis = 0), [-1, trialSize])

    for jj, row in rows.iterrows():
        ts_aligned = row["ts_aligned"]
        if not(singleColor is None):
            for ii, trialData in enumerate(row["volumeAligned"]):
                axs.plot(ts_aligned,trialData, lw = 0.5, color = singleColor, alpha = alpha)

    meanDeliveryTrace = np.mean(AllTrials, axis=0)
    stdDeliveryTrace = np.std(AllTrials, axis = 0)
    axs.plot(ts_aligned,meanDeliveryTrace, lw = 3, color = inColor)
    axs.fill_between(ts_aligned, meanDeliveryTrace-stdDeliveryTrace, meanDeliveryTrace+stdDeliveryTrace,
     facecolor = inColor,alpha=0.5)

    axs.set_ylim(bottom=0)
    axs.set_xlim(row["stepWin"])
    axs.set_ylabel(r'$\Delta$ Volume (capillary x-section)',fontsize = 14)
    axs.set_xlabel('Time since pulse (s)',fontsize = 14)
    axs.tick_params(labelcolor='k', top=False, bottom=True, left=True, right=False)
    axs.spines["right"].set_visible(False)
    axs.spines["top"].set_visible(False)
    plt.rc('xtick', labelsize='large')
    plt.rc('ytick', labelsize='large')
    return(axs, fig)
## LEGACY FUNCTIONS

def concat_run_dict(dataFrameSlice):
    sessionID = []
    for iS,row in dataFrameSlice.iterrows():
        nTrials = len(row["dataDict"]["pulseStart"])
        sessionID.append(np.zeros(nTrials) + iS)
        row["dataDict"]["SessionID"] = sessionID

    d = {}
    keys2merge = ['pulseStart',\
        'pulseStart_diff', 'volumeAligned', 'finalVolume', 'timeFinalVolume', 'SessionID']
    for k in keys2merge:
        d[k] = np.concatenate(list(a[k] for a in dataFrameSlice["dataDict"].tolist()))

    dummy = row["dataDict"]
    data = {"rawData" : None,
        "pulseStart" : d["pulseStart"],
        "lengthOfLiquid" : None,
        "fs" : dummy["fs"],
        "stepWin" : dummy["stepWin"],
        "baselineWin" : dummy["baselineWin"],
        "finalVolumeWin" : dummy["finalVolumeWin"],
        "ratioFinalVolume" : dummy["ratioFinalVolume"],
        "ts_aligned" : None,
        "pulseStart_diff" : d["pulseStart_diff"],
        "volumeAligned" : d["volumeAligned"],
        "finalVolume" : d["finalVolume"],
        "timeFinalVolume" : d["timeFinalVolume"],
        "SessionID" : d["SessionID"],
        "fileName" : None,
        "TTL_ERROR_FLAG" : None}
    return data