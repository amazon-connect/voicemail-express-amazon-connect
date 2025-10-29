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

# Import the Packager Key Functions
import sub_genai_summary

# Establish logging configuration
logger = logging.getLogger()

def process_transcript(function_payload):

    # Debug lines for troubleshooting
    logger.info('********** Beginning Sub:Process Transcription **********')
    logger.debug(function_payload)

    # Establish an empty container
    sub_response = {}

     # Load the transcript from S3
    try:
        s3_resource = boto3.resource('s3')
        transcript_object = s3_resource.Object(function_payload['function_data']['transcript_bucket'], function_payload['function_data']['transcript_key'])
        file_content = transcript_object.get()['Body'].read().decode('utf-8')
        json_content = json.loads(file_content)
        vmx3_transcript_contents = json_content['results']['transcripts'][0]['transcript']
        sub_response.update({'vmx3_transcript_contents':vmx3_transcript_contents})
        logger.debug('********** Sub:Process Transcription - Retrieved transcript from S3 **********')

    except Exception as e:
        logger.error('********** Sub:Process Transcription - Failed to retrieve transcript from S3 **********')
        logger.error(e)
        raise Exception
    
    # Check for GenAI Summary option and complete if necessary
    if 'vmx3_do_genai_summary' not in function_payload['vmx_data']:
        function_payload['vmx_data'].update({'vmx3_do_genai_summary':os.environ['vmx3_do_genai_summary']})
    
    if function_payload['vmx_data']['vmx3_do_genai_summary'] == 'true':
        try:
            do_genai_summary = sub_genai_summary.genai_summarizer({'vmx3_transcript_contents':sub_response['vmx3_transcript_contents']})
            sub_response.update(do_genai_summary)

        except Exception as e:
            logger.error('********** Sub:Process Transcriptionn - Summarization Failed **********')
            logger.error(e)
            sub_response.update({'vmx3_genai_summary':'Summarization Failed'})
    
    else: 
        sub_response.update({'vmx3_genai_summary':'Summarization not enabled for this contact.'})
        logger.debug('********** Sub:Process Transcriptionn - Summarization not enabled for contact **********')

    logger.info('********** Sub:Process Transcription - COMPLETE **********')
    logger.debug(sub_response)
    return sub_response