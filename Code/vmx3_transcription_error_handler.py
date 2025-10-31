current_version = '2025.09.13'
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

# Import required modules
import boto3
import json
import logging
import os

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
    
    # Extract the needed content
    try:
        original_transcript_key = event['detail']['TranscriptionJobName']
        transcript_key = original_transcript_key[5:]
        transcript_job = transcript_key.replace('.json','')
        contact_id = transcript_job.split('_',1)[0]
        transcript_bucket = os.environ['s3_transcripts_bucket']
        aws_account = event['account']

        logger.debug('********** Successfully extracted data **********')

    except Exception as e:
        logger.error('********** Could not extract required data **********')
        logger.error(e)

        return {'status':'complete','result':'ERROR','reason':'Failed to extract data'}
    
    # Establish the default failure message
    message_content = {
        'jobName':transcript_job,
        'accountId':aws_account,
        'status':'COMPLETED',
        'results':{
            'transcripts':[
                {
                    'transcript':'Transcription failed. Please refer to the recording link below, and/or expand the "Show all task information" section for details about the contact.'
                }
            ]
        }
    }
    
    # Write the error message to S3, mimicking the normal transcription process.
    try:
        response = s3_client.put_object(Body=json.dumps(message_content), Bucket=transcript_bucket, Key=original_transcript_key)
        logger.info('Voicemail with contact id ' + contact_id + ' could not be transcribed.')

        return response

    except Exception as e:
        logger.error('********** Could not write message **********')
        logger.error(e)

        return {'status':'complete','result':'ERROR','reason':'Failed to write event'}