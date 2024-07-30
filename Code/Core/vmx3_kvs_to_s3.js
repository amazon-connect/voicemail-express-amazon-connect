// Version: 2024.07.03
/*
 **********************************************************************************************************************
 *  Copyright 2024 Amazon.com, Inc. or its affiliates. All Rights Reserved                                            *
 *                                                                                                                    *
 *  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated      *
 *  documentation files (the "Software"), to deal in the Software without restriction, including without limitation   *
 *  the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and  *
 *  to permit persons to whom the Software is furnished to do so.                                                     *
 *                                                                                                                    *
 *  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO  *
 *  THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE    *
 *  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF         *
 *  CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS *
 *  IN THE SOFTWARE.                                                                                                  *
 **********************************************************************************************************************
 */

// Establish constants and globals
const { Decoder } = require('ebml');
const AWS = require('aws-sdk');
const s3 = new AWS.S3();
const BUCKET_NAME = process.env.s3_recordings_bucket;
const AUDIO_MIME_TYPE = 'audio/x-wav';

/* function that returns a promise to wait until the stream is done writing to the S3 bucket because tries to reduce the init time lambda runs the same function that was already in memory or container.*/
let streamFinished = false;
const done = () => {
    return new Promise((resolve, reject) => {
        var checkFinished = () => {
            if (streamFinished) {
                console.info('finished');
                resolve();
            } else {
                console.info('not finished, waiting 500 ms...');
                setTimeout(checkFinished, 500);
            }
        };
        setTimeout(checkFinished, 500);
    });
};

var decoder;
var wavBufferArray = [];
var wavOutputStream;

var kinesisvideo = new AWS.KinesisVideo({ region: process.env.aws_region });
var kinesisvideomedia = new AWS.KinesisVideoMedia({ region: process.env.aws_region });

exports.handler = async (event) => {
    console.debug('VMX3 Version: ' + process.env.package_version)
    console.debug(event);

    // Establish a response container
    var responseContainer = {};

    // Set counters for final status
    var totalRecordCount = 0;
    var processedRecordCount = 0;

    // Process incoming records one by one
    console.log('event.Records.length value: ' + event.Records.length);
    for (let i = 0; i < event.Records.length; i++) {
        const record = event.Records[i];

        console.debug('record: ' + i);
        console.debug(JSON.stringify(record));
        
        // async process records to ensure they don't overlap. 
        // running multiple simultaneously was causing contention.
        await processRecord(record, i, totalRecordCount, processedRecordCount, responseContainer);
    }

    async function processRecord(record, i, totalRecordCount, processedRecordCount, responseContainer) {
        let shouldProcessKvs = true;
        let currentTagName = '';
        let currentTagString = '';
        let currentFragment = BigInt(0);

        // Increment record counter
        totalRecordCount = i;
        console.info('Starting record #' + totalRecordCount);

        // Grab the data from the event for the record, decode it, grab the attributes we need, and check if this is a voicemail to process
        try {
            // Decode the payload
            const payload = Buffer.from(record.kinesis.data, 'base64').toString();
            var vmrecord = JSON.parse(payload);

            console.debug(vmrecord)
            // Grab ContactID & Instance ARN
            var currentContactID = vmrecord.ContactId;
        } catch (e) {
            console.error(e)
            console.error('FAIL: Record extraction failed');
            responseContainer['record' + totalRecordCount + 'result'] = 'Failed to extract record and/or decode';
        };

        // Grab kvs stream data
        try {
            var streamARN = vmrecord.Recordings[0].Location;
            var startFragmentNum = BigInt(vmrecord.Recordings[0].FragmentStartNumber);
            var stopFragmentNum = BigInt(vmrecord.Recordings[0].FragmentStopNumber);
            var streamName = vmrecord.Recordings[0].Location.substring(streamARN.indexOf("/") + 1, streamARN.lastIndexOf("/"));
        } catch (e) {
            console.error(e)
            console.error('FAIL: Counld not identify KVS info');
            responseContainer['record' + totalRecordCount + 'result'] = 'Failed to extract KVS info';
        };

        // Iterate through the attributes to get the tags
        try {
            var attr_data = vmrecord.Attributes;
            var attr_tag_container = '';
            Object.keys(attr_data).forEach(function (key) {
                if (key.startsWith('vmx3_lang') || key.startsWith('vmx3_queue_arn')) {
                    attr_tag_container = attr_tag_container + ('' + key + '=' + attr_data[key] + '&');
                };
            });
            attr_tag_container = attr_tag_container.replace(/&\s*$/, '');
        } catch (e) {
            console.error(e)
            console.error('FAIL: Counld not extract vm tags');
            responseContainer['record' + totalRecordCount + 'result'] = 'Failed to extract vm tags';
        }

        // Process audio and write to S3
        try {
            let chunkCount = 0;
            // Establish decoder and start listening. AS we get data, push it  into the array to be processed by writer
            decoder = new Decoder();
            decoder.on('data', chunk => {
                 
                chunkCount++;
                
                const { name, value } = chunk[1];

                console.trace(`Examining a chunk named: ${name}`);

                if (shouldProcessKvs) {
                    switch (name) {
                        case 'TagName':
                            currentTagName = value;
                            break;

                        case 'TagString':
                            if (currentTagName === 'ContactId') {
                                if (value !== currentContactID) {
                                    console.info(`Contact ID mismatch. Expected ${currentContactID}, got ${value}`);
                                    shouldProcessKvs = false;
                                }
                            }

                            if (currentTagName === 'AWS_KINESISVIDEO_FRAGMENT_NUMBER') {
                                currentFragment = BigInt(value);


                                if (currentFragment > stopFragmentNum) {
                                    console.info(`Current fragment number [${currentFragment}] is greater than the stop fragment number [${stopFragmentNum}].  Stopping KVS processing.`);
                                    console.debug('chunkCount', chunkCount);
                                    decoder.destroy();
                                    console.debug('decoder.destroyed()', decoder.destroyed());
                                    shouldProcessKvs = false; 
                                }
                            }
                            break;

                        case 'Block':
                        case 'SimpleBlock':

                            wavBufferArray.push(chunk[1].payload);
                            break;

                        default:
                            break;

                    }
                }
            });

            // Establish the writer which transforms PCM data from KVS to wav using the defined params
            var Writer = require('wav').Writer;
            wavOutputStream = new Writer({
                sampleRate: 8000,
                channels: 1,
                bitDepth: 16
            });

            //Receive chunk data and push it to a simple Array
            var s3ObjectData = [];
            wavOutputStream.on('data', (d) => {
                s3ObjectData.push(d);
            });

            //Receive the end of the KVS chunk and process it
            wavOutputStream.on('finish', async () => {
                var s3_params = {
                    Bucket: BUCKET_NAME,
                    Key: currentContactID + ".wav",
                    Body: Buffer.concat(s3ObjectData),
                    ContentType: AUDIO_MIME_TYPE,
                    Tagging: attr_tag_container
                };
                var out = await s3.putObject(s3_params).promise();
                console.debug('s3.putObject response', out);

                // Whack the data so we have a clean start point
                s3ObjectData = []
                wavBufferArray = []

                // Increment processed records
                processedRecordCount = processedRecordCount + 1;
                console.info('record' + totalRecordCount + 'result ContactID: ' + currentContactID + ' -  Write complete');
                responseContainer['record' + totalRecordCount + 'result'] = ' ContactID: ' + currentContactID + ' -  Write complete';
                streamFinished = true;
            });

            // Set params for the stream
            var stream_params = {
                APIName: "GET_MEDIA",
                StreamName: streamName
            };

            // Extract data from stream for processing using the data extraction function
            var data = await kinesisvideo.getDataEndpoint(stream_params).promise();
            console.debug(data)
            kinesisvideomedia.endpoint = new AWS.Endpoint(data.DataEndpoint);

            await parseNextFragmentNew(streamARN, startFragmentNum.toString(), null);

            //waiting until the recorded stream
            await done();

        } catch (e) {
            console.error(e)
            console.error('FAIL: Counld write audio to S3');
            responseContainer['record' + totalRecordCount + 'result'] = ' ContactID: ' + currentContactID + ' -  Failed to write audio to S3';
        }
    };

    // return the resonse for ALL records
    var summary = 'Complete. Processed ' + processedRecordCount + ' of ' + totalRecordCount + ' records.';

    const response = {
        statusCode: 200,
        body: {
            status: summary,
            recordResults: responseContainer
        }
    };

    console.debug(response)

    return response;
};

// Data extraction function
async function parseNextFragmentNew(streamArn, fragmentNumber, contToken) {
    var fragment_paramsData = {
        StartSelector: {
            StartSelectorType: 'FRAGMENT_NUMBER',
            AfterFragmentNumber: fragmentNumber,
        },
        StreamName: streamArn.split('/')[1]
    };

    return new Promise((resolve, reject) => {
        var listener = AWS.EventListeners.Core.HTTP_DATA;
        var request = kinesisvideomedia.getMedia(fragment_paramsData);
        request.removeListener('httpData', listener);
        request.on('httpData', function (chunk, response) {
            decoder.write(chunk);
        });
        request.on('httpDone', function (response) {
            wavOutputStream.write(Buffer.concat(wavBufferArray));
            wavOutputStream.end();
            resolve({});
        });
        request.send();
    });
}