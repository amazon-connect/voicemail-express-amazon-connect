current_version = '2024.08.01'
"""
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
"""

# Import the necessary modules for this function
import datetime
import boto3
import os
import json
import base64
import logging
import time
import re
from amazon_kinesis_video_consumer_library.kinesis_video_streams_parser import KvsConsumerLibrary
from amazon_kinesis_video_consumer_library.kinesis_video_fragment_processor import KvsFragementProcessor

# Establish logging configuration
logger = logging.getLogger()

def lambda_handler(event, context):
    # Debug lines for troubleshooting
    logger.debug('Code Version: ' + current_version)
    logger.debug('VMX3 Package Version: ' + os.environ['package_version'])
    logger.debug(event)

    # Process the records coming in
    try:
        for record in event['Records']:
            processor = ConnectAudioProcessor()
            processor.process_record(record)
    
    except Exception as e:
        logger.error(e)
        logger.debug('********** Could not process records **********')
        return {'status':'complete','result':'ERROR','reason':'Failed to process records'}


class ConnectAudioProcessor:
    def __init__(self):
        # Define the initialization parameters
        try:
            self.kvs_fragment_processor = KvsFragementProcessor()
            self.last_good_fragment_tags = None
            self.is_done = False
            self.contact_id = None
            self.audio_bytes = bytearray()
            self.encoded_tags = None
            logger.debug('********** Processer parameters initialized **********')

        except Exception as e:
            logger.error(e)
            logger.debug('********** Could not initialize parameters **********')
            return {'status':'complete','result':'ERROR','reason':'Could not initialize parameters'}

    def process_record(self, record):
        # Load the record data and decode
        try:
            record_data = json.loads(base64.b64decode(record['kinesis']['data']))
            logger.debug('********** Record data loaded **********')
            logger.debug(record_data)

        except Exception as e:
            logger.error(e)
            logger.debug('********** Could not load record data **********')
            return {'status':'complete','result':'ERROR','reason':'Could not load record data'}
    
        if record_data['Recordings'] is None:
            logger.debug('******** No recordings data found **********')
            return {'status':'complete','result':'ERROR','reason':'No record data'}
        
        else:
            # Load the data needed to process KVS and setup tags
            try:
                self.contact_id = record_data['ContactId']
                recording = record_data['Recordings'][0]
                stream_arn = recording['Location']
                start_timestamp = recording['StartTimestamp']
                end_timestamp = recording['StopTimestamp']
                start_fragment = recording['FragmentStartNumber']
                stop_fragment = recording['FragmentStopNumber']
                attr_tag_container = ''
                attribute_details = record_data['Attributes']
                vmx3_lang_value = attribute_details['vmx3_lang']
                vmx3_queue_arn_value = attribute_details['vmx3_queue_arn']
                
                attr_tag_container = f'vmx3_lang={vmx3_lang_value}&vmx3_queue_arn={vmx3_queue_arn_value}'
                logger.debug(attr_tag_container)

                self.encoded_tags = re.sub(r'&\s*$', '', attr_tag_container)

                logger.debug('********** Successfully processed data **********')

            except Exception as e:
                logger.error(e)
                logger.debug('********** Could not load necessary data **********')
                return {'status':'complete','result':'ERROR','reason':'Could not load necessary data'}

            # Retrieve and generate the fragment list
            try:
                fragments = self.list_fragments(
                    stream_arn,
                    datetime.datetime.fromisoformat(start_timestamp),
                    datetime.datetime.fromisoformat(end_timestamp)
                )
    
                fragment_numbers = list(map(lambda fragment: fragment['FragmentNumber'], fragments))

                # Make sure the start and stop fragments are in the list
                if start_fragment not in fragment_numbers:
                    fragment_numbers.append(start_fragment)

                if stop_fragment not in fragment_numbers:
                    fragment_numbers.append(stop_fragment)

                # Sort fragment list
                fragment_numbers.sort(key=int)
                
                logger.debug(fragment_numbers)

                logger.debug('********** Successfully generated fragment list **********')

            except Exception as e:
                logger.error(e)
                logger.debug('********** Could not generate fragment list **********')
                return {'status':'complete','result':'ERROR','reason':'Could not generate fragment list'}

            # Process fragment list
            try:
                media_response = self.get_media_for_fragment_list(
                    stream_arn,
                    fragment_numbers
                )
                logger.debug('********** Fragment list processed **********')
            
            except Exception as e:
                logger.error(e)
                logger.debug('********** Could not process fragment list **********')
                return {'status':'complete','result':'ERROR','reason':'Could not process fragment list'}

            # Configure and initialize the stream consumer
            try:
                stream_consumer = KvsConsumerLibrary(
                    stream_arn,
                    media_response,
                    self.on_fragment_arrived,
                    self.on_stream_read_complete,
                    self.on_stream_read_exception
                )
                logger.debug('********** Consumer configured **********')
    
                stream_consumer.start()
                logger.debug('********** Consumber started **********')
        
                while not self.is_done:
                    logger.debug('.......... processing ..........')
                    time.sleep(5)
                else:
                    logger.debug('********** End of stream **********')
                    stream_consumer.stop_thread()

            except Exception as e:
                logger.error(e)
                logger.debug('********** Could not consume stream **********')
                return {'status':'complete','result':'ERROR','reason':'Could not consume stream'}
    
    # Function to retrieve the data endpoint for KVS processing
    def get_kinesis_video_data_endpoint(self, stream_arn, api_name):

        try:
            client = boto3.client('kinesisvideo')
        
            response = client.get_data_endpoint(
                StreamARN=stream_arn,
                APIName=api_name
            )
            logger.debug('*********** KVS endpoint retrieved **********')
            logger.debug('Data Endpoint: ' + response['DataEndpoint'])
        
            return response['DataEndpoint']
        
        except Exception as e:
            logger.error(e)
            logger.debug('********** Could not get stream endpoint **********')
            return {'status':'complete','result':'ERROR','reason':'Could not get stream endpoint'}
    
    #  Function to get the fragment list
    def list_fragments(self, stream_arn, start_timestamp, end_timestamp):

        try:
            endpoint = self.get_kinesis_video_data_endpoint(stream_arn, 'LIST_FRAGMENTS')
        
            client = boto3.client('kinesis-video-archived-media', endpoint_url=endpoint)
        
            response = client.list_fragments(
                StreamARN=stream_arn,
                MaxResults=1000,
                FragmentSelector={
                    'FragmentSelectorType': 'SERVER_TIMESTAMP',
                    'TimestampRange': {
                        'StartTimestamp': start_timestamp,
                        'EndTimestamp': end_timestamp
                    }
                }
            )
        
            return response['Fragments']
        
        except Exception as e:
            logger.error(e)
            logger.debug('********** Could not get fragment list **********')
            return {'status':'complete','result':'ERROR','reason':'Could not get fragment list'}
    
    # Function to get the media
    def get_media_for_fragment_list(self, stream_arn, fragment_numbers):
        try:
            endpoint = self.get_kinesis_video_data_endpoint(stream_arn, 'GET_MEDIA_FOR_FRAGMENT_LIST')
        
            client = boto3.client('kinesis-video-archived-media', endpoint_url=endpoint)
        
            response = client.get_media_for_fragment_list(
                StreamARN=stream_arn,
                Fragments=fragment_numbers
            )

            logger.debug('********** Media retrieved **********')
        
            return response
        
        except Exception as e:
            logger.error(e)
            logger.debug('********** Could not process media **********')
            return {'status':'complete','result':'ERROR','reason':'Could not process media'}

    # Function to write the bytes to a mav file    
    def write_wav_to_s3(self):

        try:
            wav_bytes = self.kvs_fragment_processor.convert_track_to_wav(self.audio_bytes)
            client = boto3.client('s3')
            logger.debug('self.encoded_tags value: ' + self.encoded_tags)
            client.put_object(Body=wav_bytes.getvalue(), Bucket=f'{os.getenv("s3_recordings_bucket")}', Key=f'{self.contact_id}.wav', Tagging=self.encoded_tags, ContentType='audio/x-wav')
            
        except Exception as e:
            logger.error(e)
            logger.debug('********** Could not write data to S3 **********')

    # KVS Consumer Library call-backs
    def on_fragment_arrived(self, stream_name, fragment_bytes, fragment_dom, fragment_receive_duration):

        try:
            # Log the arrival of a fragment.
            # use stream_name to identify fragments where multiple instances of the KvsConsumerLibrary are running on different streams.
            logger.debug(
                f'##########################\nFragment Received on Stream: {stream_name}##########################')

            # Print the fragment receive and processing duration as measured by the KvsConsumerLibrary
            logger.debug('')
            logger.debug(f'####### Fragment Receive and Processing Duration: {fragment_receive_duration} secs')

            # Get the fragment tags and save in local parameter.
            self.last_good_fragment_tags = self.kvs_fragment_processor.get_fragment_tags(fragment_dom)
            
            logger.debug(f'######## Fragment Tags: {self.last_good_fragment_tags}#######')
            
            if (self.last_good_fragment_tags['ContactId'] != self.contact_id):
                logger.debug(f'######## Fragment ContactId tag [{self.last_good_fragment_tags['ContactId']} does not equals current contact id {self.contact_id}.  Skipping this fragment')
            else:
                bytes = self.kvs_fragment_processor.get_connect_fragment_audio_track_from_customer_as_bytes(fragment_dom)
                self.audio_bytes.extend(bytes)

        except Exception as err:
            logger.error(f'on_fragment_arrived Error: {err}')

    def on_stream_read_complete(self, stream_name):

        # Do something here to tell the application that reading from the stream ended gracefully.
        logger.info(f'Read Media on stream: {stream_name} Completed successfully - Last Fragment Tags: {self.last_good_fragment_tags}')
        self.is_done = True
        logger.debug(f'######## Audio Bytes Length {len(self.audio_bytes)} ########')
        logger.debug(f'######## Audio Bytes {self.audio_bytes} ########')
        
        self.write_wav_to_s3()
        

    def on_stream_read_exception(self, stream_name, error):

        # Here we just log the error
        logger.error(f'####### ERROR: Exception on read stream: {stream_name}\n####### Fragment Tags:\n{self.last_good_fragment_tags}\nError Message:{error}')