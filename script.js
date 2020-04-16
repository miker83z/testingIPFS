const fs = require('fs');
const lineByLine = require('n-readlines');
const createCsvWriter = require('csv-writer');
const ipfsAPI = require('ipfs-http-client');
const axios = require('axios').default;
const secret = require('./secret.json');
const skynet = require('@nebulous/skynet');

const optionDefinitions = [
  { name: 'number', alias: 'n', type: Number, defaultValue: 10 },
  { name: 'await', alias: 'a', type: Number, defaultValue: 0 },
  { name: 'image', alias: 'i', type: Boolean, defaultValue: false },
];
const commandLineArgs = require('command-line-args');
const options = commandLineArgs(optionDefinitions);

// Constant Values
const numberOfBuses = options.number;
const awaitFor = options.await;
const image = options.image;
const imagePath = 'inputDatasets/image.jpg';
const inputBuses = 'inputDatasets/inputDataset' + numberOfBuses + '.csv';
const dirTemp = 'datasetIPFS/' + numberOfBuses + '/';
const dirType = ['dataProp/', 'dataService/', 'dataSia/'];
let dirDate;
let bus;
let ipfsService;
const ipfsProp = ipfsAPI({
  host: '34.65.225.155',
  port: '80',
  protocol: 'http',
});

const sleep = (ms) => {
  return new Promise((resolve) => setTimeout(resolve, ms));
};

const setupEnvironment = () => {
  bus = {};
  if (!fs.existsSync(dirTemp)) fs.mkdirSync(dirTemp);
  dirDate = new Date().toISOString();
  dirType.forEach((element) => {
    const dirPart = dirTemp + element;
    if (!fs.existsSync(dirPart)) fs.mkdirSync(dirPart);
    const dir = dirPart + dirDate;
    if (!fs.existsSync(dir)) fs.mkdirSync(dir);
  });
};

const handleLoginIPFSService = async (usr, psw) => {
  try {
    const resp = await axios.post(
      'https://api.temporal.cloud/v2/auth/login',
      JSON.stringify({
        username: usr,
        password: psw,
      }),
      {
        headers: {
          'Content-Type': 'text/plain',
        },
      }
    );
    ipfsService = ipfsAPI({
      // the hostname (or ip address) of the endpoint providing the ipfs api
      host: 'api.ipfs.temporal.cloud',
      // the port to connect on
      port: '443',
      'api-path': '/api/v0/',
      // the protocol, https for security
      protocol: 'https',
      // provide the jwt within an authorization header
      headers: {
        authorization: 'Bearer ' + resp.data.token,
      },
    });
  } catch (error) {
    console.log(error);
  }
};

const initBus = async (busID) => {
  try {
    // Bus object
    bus[busID] = {
      csv: [],
    };

    for (let i = 0; i < dirType.length; i++) {
      // Create log file
      const filepath = (bus[busID].csv[i] =
        dirTemp + dirType[i] + dirDate + '/bus-' + busID + '.csv');
      fs.writeFile(filepath, 'start,finish,counter\n', (err) => {
        if (err) throw err;
      });
      sleep(2);
    }
  } catch (error) {
    console.log('SETUP ERROR: ' + error);
  }
};

const publish = async (b, id, json, prop) => {
  const ipfs = !prop ? ipfsProp : ipfsService;
  let startTS = -1,
    finishTS = -1;
  try {
    //Start operations
    startTS = new Date().getTime();

    for await (const result of ipfs.add(JSON.stringify(json))) {
      finishTS = new Date().getTime();
      //console.log(result);
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
    //Start operations
    startTS = new Date().getTime();

    if (image) {
      a = skynet.DefaultUploadOptions;
      a.customFilename = 's' + startTS;
      const resp = await skynet.UploadFile(imagePath, a);
    } else {
      const resp = await axios.post(
        'https://siasky.net/skynet/skyfile/file/' +
          JSON.stringify(json) +
          '?filename=' +
          JSON.stringify(json),
        JSON.stringify(json),
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
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
      publish(
        row[1],
        row[4],
        {
          payload: payloadValue,
          timestampISO: new Date().toISOString(),
        },
        0
      );

      publish(
        row[1],
        row[4],
        {
          payload: payloadValue,
          timestampISO: new Date().toISOString(),
        },
        1
      );
      publishSia(row[1], row[4]);
    }
  } catch (error) {
    console.log(error);
  }
};

const main = async () => {
  await sleep(awaitFor * 60000);
  setupEnvironment();
  await handleLoginIPFSService(secret.username, secret.password);
  await go();
  console.log('Finished approximately at : ' + new Date().toString());
};

main();
