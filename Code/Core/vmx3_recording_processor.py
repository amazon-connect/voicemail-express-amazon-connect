current_version = '2025.09.12'
'''
**********************************************************************************************************************
 *  Copyright 2025 Amazon.com, Inc. or its affiliates. All Rights Reserved                                            *
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
'''

# Import the necessary modules for this function
import json
import os
import logging
import boto3
import io
import base64
import urllib.parse
from datetime import datetime, timezone
from pydub import AudioSegment

# Establish logging configuration
logger = logging.getLogger()

# Core handler that calls the other functions
def lambda_handler(event, context):

    # Debug lines for troubleshooting
    logger.debug('Code Version: ' + current_version)
    logger.debug('VMX3 Package Version: ' + os.environ['package_version'])
    logger.debug(event)

    # 1. Send incoming records to the record data processor
    try:
        # Iterate through records in the incoming event
        for record in event['Records']:
            logger.debug(record)

            # Send to data processor
            voicemail_data = process_recording_data(record)

            # Log successes
            logger.info('********** Step 1 Complete: Record Data Processed **********')
            logger.debug(voicemail_data)
    
    except Exception as e:
        logger.error(e)
        logger.error('********** Step 1 Failed: Could not process records **********')
        raise Exception

    # 2. Send to the audio processor
    try:
        # Send data to the audio processor to perform the trim and save
        voicemail_audio = audio_processor(voicemail_data)

        # Log success
        logger.info('********** Step 2 Complete: Record Audio Processed **********')
        
    except Exception as e:
        logger.error(e)
        logger.error('********** Step 2 Failed: Could not process recording **********')
        raise Exception

    # Log and return success
    logger.info('********** Process Complete: Voicemail Message extracted and saved **********')
    return 'Voicemail Audio Processing Complete - Move to Transcriber'

def process_recording_data(record):
    # Load the record, decode, and grab needed datas
    try:
        record_data = json.loads(base64.b64decode(record['kinesis']['data']))
        logger.debug('********** Record data loaded **********')
        logger.debug(record_data)

    except Exception as e:
        logger.error(e)
        logger.debug('********** Could not load record data **********')
        raise Exception

    if record_data['Recordings'] is None:
        logger.debug('******** No recordings data found **********')
        return {'status':'complete','result':'ERROR','reason':'No record data'}
    
    # A recording was identified in the record
    else:
        # Load the data needed to process recording
        try:
            for record in record_data['Recordings']:
                if record['ParticipantType'] == 'IVR':
                    logger.info('VM Found')
                    found_vm = record
                    break
            else:
                logger.info('VM not found in record')
        
        except Exception as e:
            logger.error(e)
            logger.debug('********** VM Recording Data Not Found **********')
            raise Exception

        # Extract some important keys for processing
        contact_id = record_data['ContactId']
        vm_attributes = record_data['Attributes']
        if 'vmx3_genai_summary' in vm_attributes:
            logger.debug('Genai option selected')
        else:
            vm_attributes.update({'vmx3_genai_summary':'false'})
        vm_timestamp = vm_attributes['vmx3_timestamp']
        source_bucket = found_vm['Location'].split("/",1)[0]
        source_key = found_vm['Location'].split('/',1)[1]
        source_timestamp = found_vm['StartTimestamp']

        # Extract date elements from timestamp
        dt_timestamp = datetime.strptime(vm_timestamp, '%Y-%m-%dT%H:%M:%SZ')
        dt_year = dt_timestamp.strftime('%Y')
        dt_month = dt_timestamp.strftime('%m')
        dt_day = dt_timestamp.strftime('%d')

        # Create the time offset for the recording
        ts1 = datetime.fromisoformat(vm_timestamp.replace('Z', '+00:00'))
        ts2 = datetime.fromisoformat(source_timestamp.replace('Z', '+00:00'))
        vm_timestamp_difference = ts1 - ts2
        vm_offset = vm_timestamp_difference.total_seconds()

        # Create new key
        vm_key = dt_year + '/' + dt_month + '/' + dt_day + '/' + contact_id + '.wav'

        # Build and return the response
        dproc_response = {
            'contact_id' : contact_id,
            'vm_attributes' : vm_attributes,
            'source_bucket' : source_bucket,
            'source_key' : source_key,
            'source_timestamp' : source_timestamp,
            'vm_timestamp' : vm_timestamp,
            'vm_bucket' : os.environ['vmx3_recordings_bucket'],
            'vm_key' : vm_key,
            'vm_offset' : vm_offset * 1000
        }
        logger.debug(dproc_response)

        return dproc_response
    
def audio_processor(recording_data):
    # Establish S3 Client
    s3_client = boto3.client('s3')

    # Open recording file for processing and write to buffer
    try:
        # Crete the buffer to write the S3 file into
        in_memory_audio = io.BytesIO()
        
        # Download the object and write the audio to the buffer
        recording_obj = s3_client.download_fileobj(recording_data['source_bucket'], recording_data['source_key'],in_memory_audio)
        in_memory_audio.seek(0)
        logger.debug('********** Loaded audio to buffer **********')

    except Exception as e:
        logger.error(e)
        logger.error('********** Could not load audio to buffer **********')
        raise Exception
    
    # Trim the recording
    try:
        # Load the recording audio to from buffer
        audio_segment = AudioSegment.from_file(in_memory_audio, format="wav")

        # Trim and write to new buffer
        vm_audio = audio_segment[recording_data['vm_offset']:]
        out_buffer = io.BytesIO()
        vm_audio.export(out_buffer, format='wav')
        out_buffer.seek(0)
        logger.debug('********** Trimmed recording **********')

    except Exception as e:
        logger.error(e)
        logger.debug('********** Could not trim audio **********')
        raise Exception
    
    # Write trimmed recording to S3
    try:
        # Set required tag values
        vm_tags = {
            'vmx3_lang_value' : recording_data['vm_attributes']['vmx3_lang'],
            'vmx3_queue_arn' : recording_data['vm_attributes']['vmx3_queue_arn'],
            'vmx3_genai_summary' : recording_data['vm_attributes']['vmx3_genai_summary'],
            'vmx3_lang' : recording_data['vm_attributes']['vmx3_lang']
        }
        logger.debug(vm_tags)

        # Encode the tags
        vm_encoded_tags = urllib.parse.urlencode(vm_tags)
        logger.debug(vm_encoded_tags)

        # Perform the upload
        vm_upload = s3_client.upload_fileobj(out_buffer, recording_data['vm_bucket'], recording_data['vm_key'],ExtraArgs={'Tagging': vm_encoded_tags})

        return vm_upload

    except Exception as e:
        logger.error(e)
        logger.debug('********** Could not upload new file to S3 **********')
        raise Exception