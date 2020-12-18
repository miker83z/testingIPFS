import os
import csv
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import numpy as np
import scipy.stats
import math


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


def get_data(data, startingDir, totReqBus, printFlag):
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


def plot(data, totNum, lstyl, lwid):
    # plt.yscale('log')
    err = [np.zeros(totNum), np.zeros(totNum), np.zeros(totNum)]
    avg = [np.zeros(totNum), np.zeros(totNum), np.zeros(totNum)]
    nmbrs = []
    flag = True

    serviceTypeNum = 0
    for serviceType in data:
        usersNumberNum = 0
        for usersNumber in serviceType:
            tmp = np.array(usersNumber[1])
            avg[serviceTypeNum][usersNumberNum] = round(np.mean(tmp), 2)
            #err[serviceTypeNum+usersNumberNum] = avg[usersNumberNum+serviceTypeNum] - confInt(tmp, .95)[0]
            err[serviceTypeNum][usersNumberNum] = usersNumber[2]
            usersNumberNum += 1
            if flag:
                nmbrs.append(usersNumber[3])
        serviceTypeNum += 1
        flag = False

    colors = ['brown', 'royalblue', 'tab:green']

    ax[0].plot(nmbrs, avg[0]/nmbrs, linestyle=lstyl,
               linewidth=lwid, color=colors[0])
    ax[0].plot(nmbrs, avg[1]/nmbrs, linestyle=lstyl,
               linewidth=lwid, color=colors[1])
    ax[0].plot(nmbrs, avg[2]/nmbrs, linestyle=lstyl,
               linewidth=lwid, color=colors[2])

    ax[1].plot(nmbrs, err[0]/nmbrs, linestyle=lstyl,
               linewidth=lwid, color=colors[0])
    ax[1].plot(nmbrs, err[1]/nmbrs, linestyle=lstyl,
               linewidth=lwid, color=colors[1])
    ax[1].plot(nmbrs, err[2]/nmbrs, linestyle=lstyl,
               linewidth=lwid, color=colors[2])

    ax[1].set_xticks(np.arange(10, 101, 10))
    #ax[1].set_ylim(0, 0.012)
    # ax[0].set_xscale('log')
    # ax[0].set_yscale('log')

    ax[0].set_ylabel('relative latency (ms/users count)')
    ax[1].set_ylabel('relative errors (errors/users count)')
    ax[1].set_xlabel('users count')

    patch1 = mpatches.Patch(color=colors[0], label='IPFS Proprietary')
    patch2 = mpatches.Patch(color=colors[1], label='IPFS Service')
    patch3 = mpatches.Patch(color=colors[2], label='Sia Skynet')
    soli = mlines.Line2D([], [], color='black',
                         linestyle='dotted', label='100 B')
    dott = mlines.Line2D([], [], color='black',
                         linestyle='solid', label='1 MB')

    ax[0].legend(handles=[patch1, patch2, patch3,
                          soli, dott], fontsize='x-large')


def small():
    startingDir = 'datasetIPFS'
    totNum = len(next(os.walk(startingDir))[1])
    data = [[], [], []]

    get_data(data, startingDir, 15, False)
    # plot1()
    plot(data, totNum, 'dotted', 3)


def big():
    startingDir = 'datasetIPFSImage'
    totNum = len(next(os.walk(startingDir))[1])
    data = [[], [], []]

    get_data(data, startingDir, 15, False)
    # plot1()
    plot(data, totNum, 'solid', 2)


heights = [2, 1]
fig, ax = plt.subplots(
    nrows=2, ncols=1, sharex=True, constrained_layout=True, gridspec_kw=dict(height_ratios=heights))
fig.set_size_inches(7, 7)

small()
big()

plt.savefig('complete.png', bbox_inches='tight', dpi=300)
