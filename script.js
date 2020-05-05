const fs = require('fs');
const lineByLine = require('n-readlines');
const createCsvWriter = require('csv-writer');
const ipfsAPI = require('ipfs-http-client');
const axios = require('axios').default;
const skynet = require('@nebulous/skynet');

const optionDefinitions = [
  { name: 'number', alias: 'n', type: Number, defaultValue: 10 },
  { name: 'await', alias: 'a', type: Number, defaultValue: 0 },
  { name: 'image', alias: 'i', type: Boolean, defaultValue: false },
  { name: 'prop', alias: 'p', type: Boolean, defaultValue: false },
  { name: 'service', alias: 'k', type: Boolean, defaultValue: false },
  { name: 'sia', alias: 's', type: Boolean, defaultValue: false },
  { name: 'timeout', alias: 't', type: Number, defaultValue: 200000 },
];
const commandLineArgs = require('command-line-args');
const options = commandLineArgs(optionDefinitions);

// Constant Values
const imagePath = 'inputDatasets/image.jpg';
const dirTypeConst = ['dataProp/', 'dataService/', 'dataSia/'];
let ipfsService = ipfsAPI({
  host: 'ipfs.infura.io',
  port: 5001,
  protocol: 'https',
});
const ipfsProp = ipfsAPI({
  host: '34.65.225.155',
  port: '80',
  protocol: 'http',
});

let propFlag = (serviceFlag = siaFlag = true);
if (options.prop || options.service || options.sia) {
  propFlag = options.prop;
  serviceFlag = options.service;
  siaFlag = options.sia;
}

const timeoutValue = options.timeout;
const numberOfBuses = options.number;
const awaitFor = options.await;
const image = options.image;
const inputBuses = 'inputDatasets/inputDataset' + numberOfBuses + '.csv';
const dirImg = image ? 'datasetIPFSImage/' : 'datasetIPFS/';
const dirTemp = dirImg + numberOfBuses + '/';
let dirDate;
let bus;

const sleep = (ms) => {
  return new Promise((resolve) => setTimeout(resolve, ms, false));
};

const setupEnvironment = () => {
  bus = {};

  if (!fs.existsSync(dirTemp)) fs.mkdirSync(dirTemp);
  dirDate = new Date().toISOString();

  const dirType = [];
  if (propFlag) dirType.push(dirTypeConst[0]);
  if (serviceFlag) dirType.push(dirTypeConst[1]);
  if (siaFlag) dirType.push(dirTypeConst[2]);
  dirType.forEach((element) => {
    const dirPart = dirTemp + element;
    if (!fs.existsSync(dirPart)) fs.mkdirSync(dirPart);
    const dir = dirPart + dirDate;
    if (!fs.existsSync(dir)) fs.mkdirSync(dir);
  });
};

const initBus = async (busID) => {
  try {
    // Bus object
    bus[busID] = {
      csv: [],
    };

    if (propFlag) bus[busID].csv.push(dirTypeConst[0]);
    else bus[busID].csv.push(0);
    if (serviceFlag) bus[busID].csv.push(dirTypeConst[1]);
    else bus[busID].csv.push(0);
    if (siaFlag) bus[busID].csv.push(dirTypeConst[2]);
    else bus[busID].csv.push(0);

    for (let i = 0; i < dirTypeConst.length; i++) {
      if (bus[busID].csv[i] != 0) {
        // Create log file
        const filepath = (bus[busID].csv[i] =
          dirTemp + dirTypeConst[i] + dirDate + '/bus-' + busID + '.csv');
        fs.writeFile(filepath, 'start,finish,counter\n', (err) => {
          if (err) throw err;
        });
      }
      sleep(2);
    }
  } catch (error) {
    console.log('SETUP ERROR: ' + error);
  }
};

const publish = async (b, id, json, prop) => {
  console.log;
  const ipfs = !prop ? ipfsProp : ipfsService;
  let startTS = -1,
    finishTS = -1;
  try {
    //Start operations
    startTS = new Date().getTime();
    const raceRes = await Promise.race([
      //first
      new Promise(async (resolve, reject) => {
        for await (const result of ipfs.add(JSON.stringify(json))) {
          //console.log(result);
        }
        resolve(true);
      }),
      //second
      sleep(timeoutValue),
    ]);
    if (raceRes) {
      finishTS = new Date().getTime();
      // Latency measures
      r = finishTS - startTS;
      // Log result
      console.log(prop + ') bus ' + b + ': ' + r + 'ms');
      fs.appendFile(
        bus[b].csv[prop],
        startTS + ',' + finishTS + ',' + id + '\n',
        (err) => {
          if (err) throw err;
        }
      );
    } else {
      throw new Error('ipfs add timeout');
    }
  } catch (err) {
    console.log(prop + ')' + b + ': ' + err);
    fs.appendFile(
      bus[b].csv[prop],
      startTS + ',' + finishTS + ',' + id + '\n',
      (err) => {
        if (err) throw err;
      }
    );
  }
};

const publishSia = async (b, id, json) => {
  let startTS = -1,
    finishTS = -1;
  try {
    data = JSON.stringify(json);

    //Start operations
    startTS = new Date().getTime();

    if (image) {
      a = skynet.DefaultUploadOptions;
      a.customFilename = 's' + startTS;
      const resp = await skynet.UploadFile(imagePath, a);
    } else {
      const resp = await axios.post(
        'https://siasky.net/skynet/skyfile/file/' + data + '?filename=' + data,
        data,
        {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          timeout: timeoutValue,
        }
      );
    }

    finishTS = new Date().getTime();
    //console.log(resp.data);
    // Latency measures
    r = finishTS - startTS;
    // Log result
    console.log('2) bus ' + b + ': ' + r + 'ms');
    fs.appendFile(
      bus[b].csv[2],
      startTS + ',' + finishTS + ',' + id + '\n',
      (err) => {
        if (err) throw err;
      }
    );
  } catch (err) {
    console.log('2)' + b + ': ' + err);
    fs.appendFile(
      bus[b].csv[2],
      startTS + ',' + finishTS + ',' + id + '\n',
      (err) => {
        if (err) throw err;
      }
    );
  }
};

// Main phase, reading buses behavior in order to publish messages to MAM channels
const go = async () => {
  const liner = new lineByLine(inputBuses);
  try {
    const base64image = new Buffer(fs.readFileSync(imagePath)).toString(
      'base64'
    );
    let line = liner.next(); // read first line
    while ((line = liner.next())) {
      let row = line.toString('ascii').split(',');
      if (bus[row[1]] == undefined) initBus(row[1]);

      console.log('Waiting ' + row[0]);
      await sleep(parseInt(row[0]) * 1000);
      //console.log('Waited ' + row[0] + ' seconds for bus ' + row[1]);
      const payloadValue = image
        ? { photo: base64image }
        : { latitude: row[2], longitude: row[3] };

      if (propFlag) {
        publish(
          row[1],
          row[4],
          {
            payload: payloadValue,
            timestampISO: new Date().toISOString(),
          },
          0
        );
      }

      if (serviceFlag) {
        publish(
          row[1],
          row[4],
          {
            payload: payloadValue,
            timestampISO: new Date().toISOString(),
          },
          1
        );
      }

      if (siaFlag) {
        publishSia(row[1], row[4], {
          payload: payloadValue,
          timestampISO: new Date().toISOString(),
        });
      }
    }
  } catch (error) {
    console.log(error);
  }
};

const main = async () => {
  await sleep(awaitFor * 60000);
  setupEnvironment();
  await go();
  console.log('Finished approximately at : ' + new Date().toString());
};

main();
