import os
import csv
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import numpy as np
import scipy.stats
import math

printFlag = False
startingDir = 'datasetIPFS'
errorsFlag = True
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
    startDir[1].sort(key=lambda x: int(x))
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
                correcTot = (int(numberDir) * totReqBus)
                if lenTC != correcTot:
                    print('Check: ' + directory[0] +
                          ' ' + str(lenTC) + '/' + str(correcTot))
                    errorsNotWritten = correcTot - lenTC
                    tempTestData['errors'] += errorsNotWritten
                    tmpToAppend[2] += errorsNotWritten

                tmpToAppend[0].append(tempTestData)
                if printFlag:
                    print('Test ' + tempTestData['name'] + '-' + typeDir +
                          ':\t Avg= ' + str(round(np.mean(tempTestData['values'])/1000, 2)) +
                          ':\t Std= ' + str(round(np.std(tempTestData['values'])/1000, 2)) +
                          ',\t Err%= ' +
                          str(round(
                              (tempTestData['errors'] / (tempTestData['errors'] + len(tempTestData['values'])))*100, 2)))
            data[typeIndex].append(tmpToAppend)

            print('Test ' + numberDir + '-' + typeDir +
                  ':\t Avg= ' + str(round(np.mean(tmpToAppend[1])/1000, 2)) +
                  ':\t Std= ' + str(round(np.std(tmpToAppend[1])/1000, 2)) +
                  ',\t Err%= ' + str(round((tmpToAppend[2] / (tmpToAppend[2] + len(tmpToAppend[1])))*100, 2)) +
                  ',\t ConfInt= ' + str(confInt(tmpToAppend[1])))
        print('\n')


def plot1():
    fig, ax = plt.subplots(constrained_layout=True)
    fig.set_size_inches(11, 11)
    # plt.yscale('log')
    allLatenciesTemp = [[] for x in range(totNum * len(data))]
    err = np.zeros(totNum * len(data))
    avg = np.zeros(totNum * len(data))
    nmbrs = []
    flag = True
    sumNum = 0
    if errorsFlag:
        for typ in data:
            mulNum = 0
            for num in typ:
                avg[mulNum+sumNum] = num[2] / (len(num[1]) + num[2])
                mulNum += len(data)
                if flag:
                    nmbrs.append(num[3])
            sumNum += 1
            flag = False
    else:
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
        labels.append(str(nmbrs[x]))
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
    # ax.set_yticks(np.arange(0, np.max(ax.get_yticks()), step=1))
    if errorsFlag:
        ax.set_ylabel("errors (%)")
    else:
        ax.set_ylabel("latency (sec)", fontsize=13)
    ax.set_xlabel("buses", fontsize=13)

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


get_data()
plot1()

plt.show()
