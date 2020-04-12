import os
import csv
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import numpy as np
import scipy.stats
import math

startingDir = 'datasetIPFS'
totReqBus = 15
totNum = len(next(os.walk(startingDir))[1])

data = [[], [], []]


def confInt(data, confidence=0.95):
    a = 1.0 * np.array(data)
    n = len(a)
    m, se = np.mean(a), scipy.stats.sem(a)
    h = se * scipy.stats.t.ppf((1 + confidence) / 2., n-1)
    return round((m-h)/1000, 2), round((m+h)/1000, 2)


def ecdf(data):
    x = np.sort(data)
    n = x.size
    y = np.arange(1, n+1) / n
    return(x, y)


def get_data():
    path = os.walk(startingDir)
    startDir = next(path)
    startDir[1].sort()
    for numberDir in startDir[1]:
        numberPath = os.walk(startDir[0] + '/' + numberDir)
        startNumberDir = next(numberPath)
        startNumberDir[1].sort()
        for typeIndex, typeDir in enumerate(startNumberDir[1]):
            # testsDataForNumber, allLatencies, allErrors
            tmpToAppend = [[], [], 0, int(numberDir)]
            typePath = os.walk(startNumberDir[0] + '/' + typeDir)
            next(typePath)
            for directory in typePath:
                tempTestData = {
                    'name': directory[0].split('/')[-1],
                    'values': [],
                    'errors': 0
                }
                for csvFilename in directory[2]:
                    with open(directory[0]+'/'+csvFilename, 'r') as csvFile:
                        reader = csv.reader(csvFile)
                        next(reader)
                        for row in reader:
                            srt = int(row[0])
                            fin = int(row[1])
                            if fin == -1:
                                tempTestData['errors'] += 1
                                tmpToAppend[2] += 1
                            else:
                                value = fin - srt
                                tempTestData['values'].append(value)
                                tmpToAppend[1].append(value)
                    csvFile.close()

                lenTC = len(tempTestData['values']) + tempTestData['errors']
                if lenTC != (int(numberDir) * totReqBus):
                    print('Check: ' + directory[0] + ' ' + str(lenTC))
                    errorsNotWritten = (int(numberDir) * totReqBus) - lenTC
                    tempTestData['errors'] += errorsNotWritten
                    tmpToAppend[2] += errorsNotWritten

                tmpToAppend[0].append(tempTestData)
            data[typeIndex].append(tmpToAppend)

            print('Test ' + numberDir + ' - ' + typeDir +
                  ': \t Avg= ' + str(round(np.mean(tmpToAppend[1])/1000, 2)) +
                  ': \t Std= ' + str(round(np.std(tmpToAppend[1])/1000, 2)) +
                  ', \t Err%= ' + str(round((tmpToAppend[2] / (tmpToAppend[2] + len(tmpToAppend[1])))*100, 2)) +
                  ', \t ConfInt= ' + str(confInt(tmpToAppend[1])))
        print('\n')


def plot1(ids):
    widths = [2, 2, 2]
    heights = [3, 1]
    width = .7
    width2 = 0.2
    sxrange = np.arange(plotTestNumber60bus)

    fig, axes = plt.subplots(nrows=2, ncols=3, sharex=True,
                             constrained_layout=True, gridspec_kw=dict(width_ratios=widths, height_ratios=heights))
    fig.set_size_inches(19, 7.5)
    red_patch = mpatches.Patch(color='tab:red', label='Errors')
    orange_patch = mpatches.Patch(color='tab:orange', label='Tips')
    blue_patch = mpatches.Patch(color='tab:blue', label='PoWs')

    for i in range(len(ids)):
        errorsData = []
        tipsData = []
        tipsDataSTD = []
        powsData = []
        powsDataSTD = []
        groupDim = round(len(data[ids[i]]) / plotTestNumber60bus)

        sTestTemp = sorted(data[ids[i]], key=lambda x: x['name'])

        x = 0
        while x < len(sTestTemp):
            tmp = [0, [], []]
            for k in range(groupDim):
                tmp[0] += int(sTestTemp[x+k]['errors'])
                tmp[1].extend(sTestTemp[x+k]['tipsValue'])
                tmp[2].extend(sTestTemp[x+k]['powValue'])
            x += groupDim

            errorsData.append(
                round(int(tmp[0]) / (totalRequests * groupDim), 4))
            tipsData.append(round(np.mean(tmp[1]), 4))
            tipsDataSTD.append(round(np.std(tmp[1]), 4))
            powsData.append(round(np.mean(tmp[2]), 4))
            powsDataSTD.append(round(np.std(tmp[2]), 4))

        # First Row
        if i == 0:
            titl1 = 'Fixed Random'
        elif i == 1:
            titl1 = 'Dynamic Random'
        elif i == 2:
            titl1 = 'Adaptive RTT'
        ylab1 = 'Tips Selection and PoW Latency (ms)' if i == 0 else ''
        axes[0][i].set_ylabel(ylab1, fontsize=13)
        axes[0][i].set_title(titl1, fontdict={'fontsize': 16}, weight='heavy')
        axes[0][i].bar(sxrange, tipsData, width, color='tab:orange',
                       align='center')
        axes[0][i].bar(sxrange, powsData, width,
                       bottom=tipsData, color='tab:blue', align='center')
        if i > 0:
            axes[0][i].set_yticklabels([])
        axes[0][i].set_ylim([0, 105000])

        # First Row Errors
        ax2 = axes[0][i].twinx()
        ylab2 = 'Errors (%)' if i == 2 else ''
        ax2.set_ylabel(ylab2, fontsize=13)
        ax2.bar(sxrange, errorsData, width2,
                color='tab:red', align='center')
        if i < len(ids) - 1:
            ax2.set_yticklabels([])
        else:
            ax2.legend(handles=[red_patch, orange_patch,
                                blue_patch], fontsize='x-large')
        ax2.set_ylim([0, 0.5])

        # Second Row
        axes[1][i].bar(sxrange - (width/4), tipsDataSTD, (width/2), color='tab:orange',
                       align='center')
        axes[1][i].bar(sxrange + (width/4), powsDataSTD, (width/2), color='tab:blue',
                       align='center')
        ylab3 = 'Latency STD (ms)' if i == 0 else ''
        axes[1][i].set_xlabel('Test ID')
        axes[1][i].set_ylabel(ylab3, fontsize=13)
        if i > 0:
            axes[1][i].set_yticklabels([])
        axes[1][i].set_ylim([0, 180000])


def plot2(ids):
    colors = ['tab:green', 'tab:orange', 'tab:blue']
    linesize = [2, 3]
    patch1 = mpatches.Patch(color=colors[0], label='Fixed Random')
    patch2 = mpatches.Patch(color=colors[1], label='Dynamic Random')
    patch3 = mpatches.Patch(color=colors[2], label='Adaptive RTT')
    soli = mlines.Line2D([], [], color='black',
                         linestyle='solid', label='120 buses')
    dott = mlines.Line2D([], [], color='black',
                         linestyle='dotted', label='240 buses')
    fig, _ = plt.subplots(nrows=1, ncols=1, constrained_layout=True)
    fig.set_size_inches(8, 6)
    plt.xscale('log')
    plt.ylabel("ECDF", fontsize=13)
    plt.xlabel("latency (sec) (in log scale)", fontsize=13)
    plt.legend(handles=[patch1, patch2, patch3, soli, dott], fontsize='large')

    for i in range(len(ids)):
        l = ['solid', 'dotted']
        x, y = ecdf(np.array(allLatencies[ids[i]])/1000)
        plt.plot(x, y, color=colors[i % 3], linestyle=l[math.floor(
            i/3)], linewidth=linesize[math.floor(i/3)])
        plt.xlim([0.5, 6500])


def plot3():
    fig, ax = plt.subplots(constrained_layout=True)
    fig.set_size_inches(11, 11)
    # plt.yscale('log')
    allLatenciesTemp = [[] for x in range(totNum * len(data))]
    err = np.zeros(totNum * len(data))
    avg = np.zeros(totNum * len(data))
    nmbrs = []
    flag = True
    sumNum = 0
    for typ in data:
        mulNum = 0
        for num in typ:
            tmp = np.array(num[1])
            allLatenciesTemp[sumNum+mulNum] = tmp
            avg[mulNum+sumNum] = round(np.mean(tmp)/1000, 2)
            err[sumNum+mulNum] = avg[mulNum+sumNum] - confInt(tmp, .9)[0]
            mulNum += len(data)
            if flag:
                nmbrs.append(num[3])
        sumNum += 1
        flag = False

    width = .6
    distWidth = .05
    positions = []
    labels = []
    startNum = .5
    for x in range(totNum):
        a = startNum + width
        positions.append(a)
        labels.append('  ')
        b = a + width + distWidth
        positions.append(b)
        labels.append(str(nmbrs[x]) + '\nbuses')
        c = b + width + distWidth
        positions.append(c)
        labels.append('  ')
        startNum = c + width

    bp = ax.bar(positions, avg, .5, yerr=err,
                align='center', ecolor='black', capsize=10)
    ax.yaxis.grid(True)

    # bp = ax.boxplot(allLatenciesTemp, positions=positions,
    #                sym = 'x', patch_artist = True)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, fontsize=15)
    ax.set_yticks(np.arange(0, np.max(ax.get_yticks()), step=1))
    ax.set_ylabel("latency (sec)", fontsize=13)

    colors = ['tab:blue', 'tab:red', 'tab:green']
    for i, bar in enumerate(bp):
        bar.set_color(colors[i % 3])

    # ax2 = ax.twinx()
    # ylab2 = 'Errors (%)'
    # ax2.set_ylabel(ylab2, fontsize=13)
    # ax2.plot(positions[0:3], err[0:3], color='gold', marker='*', markeredgecolor='black', markersize=15, zorder=10)
    # ax2.plot(positions[3:6], err[3:6], color='gold', marker='*', markeredgecolor='black', markersize=15, zorder=10)
    # ax2.plot(positions[6:9], err[6:9], color='gold', marker='*', markeredgecolor='black', markersize=15, zorder=10)
    # ax2.set_ylim([0, 0.5])

    # star = mlines.Line2D([], [], color='gold', marker='*', linestyle='None', markeredgecolor='black',
    #                      markersize=15, label='Errors')
    # diamond = mlines.Line2D([], [], color='w', marker='D', linestyle='None', markeredgecolor='black',
    #                        markersize=10, label='Averages')

    patch1 = mpatches.Patch(color=colors[0], label='IPFS Proprietary')
    patch2 = mpatches.Patch(color=colors[1], label='IPFS Service')
    patch3 = mpatches.Patch(color=colors[2], label='Sia Skynet')

    ax.legend(handles=[patch1, patch2, patch3], fontsize='x-large')


def plot4():
    colors = ['tab:green', 'tab:orange', 'tab:blue']
    patch1 = mpatches.Patch(color=colors[0], label='Fixed Random')
    patch2 = mpatches.Patch(color=colors[1], label='Dynamic Random')
    patch3 = mpatches.Patch(color=colors[2], label='Adaptive RTT')
    fig, ax = plt.subplots(constrained_layout=True)
    fig.set_size_inches(8, 6)
    plt.ylabel("latency (sec)", fontsize=13)
    plt.xlabel("# buses", fontsize=13)
    avg = []
    for x in allLatencies:
        tmp = np.array(x)/1000
        avg.append(np.mean(tmp))
    xs = ['60', '120', '240']
    ax.plot(xs, avg[0:3], color=colors[0])
    ax.plot(xs, avg[3:6], color=colors[1])
    ax.plot(xs, avg[6:9], color=colors[2])
    ax.legend(handles=[patch1, patch2, patch3], fontsize='large')


get_data()
# get_local_data()
# plot1([0,3,6])
# plot2([1,4,7,2,5,8])
plot3()
# plot4()

plt.show()
