current_version = '2024.08.01'
'''
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
'''

# Import the necessary modules for this function
import json
import boto3
import os
import logging
import time

# Establish logging configuration
logger = logging.getLogger()

def lambda_handler(event, context):
     # Debug lines for troubleshooting
    logger.debug('Code Version: ' + current_version)
    logger.debug('VMX3 Package Version: ' + os.environ['package_version'])
    logger.debug(event)

    # Establish needed clients and resources
    try:
        s3_client = boto3.client('s3')
        logger.debug('********** Clients initialized **********')
    
    except Exception as e:
        logger.error('********** VMX Initialization Error: Could not establish needed clients **********')
        logger.error(e)
        
        return {'status':'complete','result':'ERROR','reason':'Failed to Initialize clients'}


    # Grab incoming data elements from the S3 event
    try:
        recording_key = event['detail']['object']['key']
        recording_name = recording_key.replace('voicemail_recordings/','')
        contact_id = recording_name.replace('.wav','')
        recording_bucket = event['detail']['bucket']['name']
        recording_region = event['region']
        logger.debug('********** Successfully set vars from S3 event **********')

    except Exception as e:
        logger.error('********** Failed to extract data from event **********')
        logger.error(e)
        
        return {'status':'complete','result':'ERROR','reason':'Failed to extract data from event'}

    # Establish the S3 client and get the object tags
    try:
        object_data = s3_client.get_object_tagging(
            Bucket=recording_bucket,
            Key=recording_key
        )

        object_tags = object_data['TagSet']
        loaded_tags = {}

        for i in object_tags:
            loaded_tags.update({i['Key']:i['Value']})

        logger.debug('********** Successfully loaded object tags **********')

    except Exception as e:
        logger.error('********** Failed to load tags from object **********')
        logger.error(e)
        
        return {'status':'complete','result':'ERROR','reason':'Failed to load tags from object'}

    # Build the Recording URL
    try:
        recording_url = 'https://{0}.s3-{1}.amazonaws.com/{2}'.format(recording_bucket, recording_region, recording_key)
        logger.debug('********** Successfully generated recording URL **********')

    except Exception as e:
        logger.error('********** Failed to generate recording URL **********')
        logger.error(e)
        
        return {'status':'complete','result':'ERROR','reason':'Failed to generate recording URL'}

    # Do the transcription
    try:
        # Esteablish the client
        transcribe_client = boto3.client('transcribe')

        # Submit the transcription job
        transcribe_response = transcribe_client.start_transcription_job(
            TranscriptionJobName='vmx3_' + contact_id + '_' + str(round(time.time())),
            LanguageCode=loaded_tags['vmx3_lang'],
            MediaFormat='wav',
            Media={
                'MediaFileUri': recording_url
            },
            OutputBucketName=os.environ['s3_transcripts_bucket']
        )
        logger.debug('********** Transcribe job submitted **********')

        return {'status': 'complete','result': 'voicemail processed'}

    except Exception as e:
        logger.error('********** Transcription job rejected **********')
        logger.error(e)
        
        return {'status':'complete','result':'ERROR','reason':'Transcription job rejected'}