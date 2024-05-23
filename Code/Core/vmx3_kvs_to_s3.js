// Version: 2024.05.01
/*
 **********************************************************************************************************************
 *  Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved                                            *
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
const {Decoder} = require('ebml');
const AWS = require('aws-sdk');
const s3 = new AWS.S3();
const BUCKET_NAME = process.env.s3_recordings_bucket;
const AUDIO_MIME_TYPE = 'audio/x-wav';

/* function that returns a promise to wait until the stream is done writing to the S3 bucket because tries to reduce the init time lambda runs the same function that was already in memory or container.*/
let streamFinished = false
const done  = () => {
    return new Promise ((resolve, reject) => {
        var checkFinished = () => {
            if(streamFinished) {
                console.log('finished')
                resolve()
            } else {
                console.log('not finished, waiting 500 ms...')
                setTimeout(checkFinished, 500)
            }
        }
        setTimeout(checkFinished, 500)
    })
};

var decoder;
var wavBufferArray = [];
var wavOutputStream;

var kinesisvideo = new AWS.KinesisVideo({region: process.env.aws_region});
var kinesisvideomedia = new AWS.KinesisVideoMedia({region: process.env.aws_region});

exports.handler = async (event) => {
    // Uncomment the following line for debugging
    console.log('Event Received ==>', JSON.stringify(event, null, 2))

    // Establish a response container
    var responseContainer = {};

    // Set counters for final status
    var totalRecordCount = 0;
    var processedRecordCount = 0;

    // Process incoming records
    for (const record of event.Records) {
        let shouldProcessKvs = true;
        let currentTagName = '';
        let currentTagString = '';
        let currentFragment = BigInt(0);


        // Increment record counter
        totalRecordCount = totalRecordCount + 1
        console.log('Starting record #' + totalRecordCount)

        // Grab the data from the event for the record, decode it, grab the attributes we need, and check if this is a voicemail to process
        try {
            // Decode the payload
            const payload = Buffer.from(record.kinesis.data, 'base64').toString();
            var vmrecord = JSON.parse(payload);
            // Uncomment the following line for debugging
            // console.log(vmrecord)
            // Grab ContactID & Instance ARN
            var currentContactID = vmrecord.ContactId;
        } catch(e) {
            console.log('FAIL: Record extraction failed');
            responseContainer['record' + totalRecordCount + 'result'] = 'Failed to extract record and/or decode';
            continue;
        };

        // Check for the positive vmx3_flag attribute so we know that this is a vm to process
        try {
            var vmx3_flag = vmrecord.Attributes.vmx3_flag || '99';
            if (vmx3_flag == '0') {
                responseContainer['record ' + totalRecordCount + 'result'] = ' ContactID: ' + currentContactID + ' - IGNORE - voicemail already processed';
                processedRecordCount = processedRecordCount + 1;
                continue;
            } else if (vmx3_flag == '1') {
                console.log('Record #' + totalRecordCount  + ' ContactID: ' + currentContactID + ' -  is a voicemail - begin processing.')
            } else {
                responseContainer['record' + totalRecordCount + 'result'] = ' ContactID: ' + currentContactID + ' - IGNORE - voicemail flag not valid';
                processedRecordCount = processedRecordCount + 1;
                continue;
            }
        } catch(e) {
            responseContainer['record' + totalRecordCount + 'result'] = ' ContactID: ' + currentContactID + ' - IGNORE - Some other bad thing happened with the attribute comparison.';
            processedRecordCount = processedRecordCount + 1;
            continue;
        };

        // Grab kvs stream data
        try {
            var streamARN = vmrecord.Recordings[0].Location;
            var startFragmentNum = BigInt(vmrecord.Recordings[0].FragmentStartNumber);
            var stopFragmentNum = BigInt(vmrecord.Recordings[0].FragmentStopNumber);
            var streamName = vmrecord.Recordings[0].Location.substring(streamARN.indexOf("/") + 1, streamARN.lastIndexOf("/"));
        } catch(e) {
            console.log('FAIL: Counld not identify KVS info');
            responseContainer['record' + totalRecordCount + 'result'] = 'Failed to extract KVS info';
            continue;
        };

        // Iterate through the attributes to get the tags
        try {
            var attr_data = vmrecord.Attributes;
            var attr_tag_container = '';
            Object.keys(attr_data).forEach(function (key) {
                if (key.startsWith('vmx3_lang')||key.startsWith('vmx3_queue_arn')){
                    attr_tag_container = attr_tag_container + ('' + key + '=' + attr_data[key] + '&');
                };
            });
            attr_tag_container = attr_tag_container.replace(/&\s*$/, '');
        } catch(e) {
            console.log('FAIL: Counld not extract vm tags');
            responseContainer['record' + totalRecordCount + 'result'] = 'Failed to extract vm tags';
            continue;
        }

        // Process audio and write to S3
        try {
            // Establish decoder and start listening. AS we get data, push it  into the array to be processed by writer
            decoder = new Decoder();
            decoder.on('data', chunk => {
                /**
                 * Check the shouldProcessKvs field.  If it's true, then proceed with looking at this chunk.  If it's
                 * false, then don't look at this chunk at all.
                 *
                 * This will be set to false once the current fragment number greater than the stop fragment number
                 * indicating that we've gone as far as we should go in this KVS.
                 *
                 */

                const {name, value} = chunk[1];

                //console.log(`Examining a chunk named: ${name}`);

                if (shouldProcessKvs) {
                    switch (name) {
                        case 'TagName':
                            /**
                             * This chunk contains a tag name indicating what type of data is contained in the next
                             * TagString chunk.
                             *
                             * Store the value of the chunk in the currentTagName field.
                             *
                             */
                            currentTagName = value;
                            break;

                        case 'TagString':
                            /**
                             * This chunk contains a tag string containing the value of the tag name above.  If the
                             * current tag name is AWS_KINESISVIDEO_FRAGMENT_NUMBER we know that this tag string is
                             * the value of the AWS_KINESISVIDEO_FRAGMENT_NUMBER.
                             *
                             * Store the BigInt value of the chunk in the currentFragment field.  Fragment numbers are
                             * very large and require a BigInt data type.
                             *
                             */
                            if (currentTagName === 'AWS_KINESISVIDEO_FRAGMENT_NUMBER') {
                                currentFragment = BigInt(value);

                                /**
                                 * If the current fragment number is after the stop fragment number from the CTR, then
                                 * set the shouldProcessKvs field to false to tell the system to not look at this
                                 * stream in this Lambda execution any longer.
                                 *
                                 */
                                if (currentFragment > stopFragmentNum) {
                                    console.log(`Current fragment number [${currentFragment}] is greater than the stop fragment number [${stopFragmentNum}].  Stopping KVS processing.`);
                                    shouldProcessKvs = false;
                                }
                            }
                            break;

                        case 'Block':
                        case 'SimpleBlock':
                            /**
                             * This chunk contains audio data so write it to the wav file buffer.
                             *
                             */
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

                // Whack the data so we have a clean start point
                s3ObjectData = []
                wavBufferArray = []

                // Increment processed records
                processedRecordCount = processedRecordCount + 1;
                console.log('record' + totalRecordCount + 'result ContactID: ' + currentContactID + ' -  Write complete');
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
            kinesisvideomedia.endpoint = new AWS.Endpoint(data.DataEndpoint);

            await parseNextFragmentNew(streamARN, startFragmentNum.toString(), null);

            //waiting until the recorded stream
            await done();

        } catch(e) {
            //console.log('FAIL: Counld write audio to S3');
            responseContainer['record' + totalRecordCount + 'result'] = ' ContactID: ' + currentContactID + ' -  Failed to write audio to S3';
            continue;
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

    // Uncomment the following line for debugging
    // console.log(response)

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
