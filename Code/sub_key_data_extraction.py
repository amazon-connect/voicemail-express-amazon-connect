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
from datetime import datetime

# Establish logging configuration
logger = logging.getLogger()

def key_data_extraction(function_payload):

    # Debug lines for troubleshooting
    logger.debug('Function Name: ' + os.environ['AWS_LAMBDA_FUNCTION_NAME'])
    logger.debug('Code Version: ' + current_version)
    logger.debug('VMX3 Package Version: ' + os.environ['package_version'])
    logger.info('********** Beginning Sub: Key Data Extraction **********')
    logger.debug(function_payload)

    # Establish an empty container
    sub_response = {}

    # Extract S3 buckets from environment vars, transcript key, recording key, and tags from the recording object
    sub_response.update({'function_data':{}})
    try:
        # Set S3 buckets from Environment Variables
        transcript_bucket = os.environ['s3_transcripts_bucket']
        recording_bucket = os.environ['s3_recordings_bucket']
        sub_response['function_data'].update({'transcript_bucket':transcript_bucket, 'recording_bucket':recording_bucket})

        # Extract S3 object keys for transcripts and recordings
        transcript_key = function_payload['detail']['object']['key']
        transcript_file_name = transcript_key.rsplit('/',1)[1]
        recording_key = transcript_key.replace('.json','.wav')
        sub_response['function_data'].update({'transcript_key':transcript_key,'transcript_file_name':transcript_file_name,'recording_key':recording_key})

        # Extract the contact ID
        contact_id = transcript_file_name.replace('.json','')
        sub_response['function_data'].update({'contact_id':contact_id})
        
        logger.debug('********** Sub: Key Data Extraction - Successfulluy extracted core attributes **********')

    except Exception as e:
        logger.error('********** Sub: Key Data Extraction - Failed to extract core attributes **********')
        logger.error(e)
        raise Exception
    
    try:
        # Load the tags from the initial recording object
        s3_client = boto3.client('s3')

        object_data = s3_client.get_object_tagging(
            Bucket = recording_bucket,
            Key = recording_key
        )

        object_tags = object_data['TagSet']
        loaded_tags = {}

        for i in object_tags:
            loaded_tags.update({i['Key']:i['Value']})
        
        logger.debug('********** Sub: Key Data Extraction - Extracted s3 tags from recording **********')

    except Exception as e:
        logger.error('********** Sub: Key Data Extraction - Record Result: Failed to extract tags **********')
        logger.error(e)
        raise Exception
    
    # Set instance attributes
    try:
        queue_arn = loaded_tags['vmx3_queue_arn']
        arn_substring = queue_arn.split('instance/')[1]
        instance_id = arn_substring.split('/queue')[0]
        sub_response['function_data'].update({'instance_id':instance_id})

        queue_id = arn_substring.split('queue/')[1]
        sub_response['function_data'].update({'queue_id':queue_id})
        logger.debug('********** Sub: Key Data Extraction - Instance attributes set **********')

    except Exception as e:
        logger.error('********** Sub: Key Data Extraction - Failed to set instance attributess **********')
        logger.error(e)
        raise Exception

    # Get the current date and time in UTC using timezone-aware objects
    sub_response.update({'vmx_data':{}})
    try:
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%A, %b %d at %I:%M %p (Instance Time)")
        sub_response['vmx_data'].update({'vmx3_datetime':formatted_datetime})
        logger.debug('Processed Timestamp: ' + formatted_datetime)
    
    except Exception as e:
        logger.error('********** Sub: Key Data Extraction - Failed to get timestamp **********')
        logger.error(e)
        
        formatted_datetime = 'UNKNOWN'
        sub_response['vmx_data'].update({'vmx3_datetime':formatted_datetime})

    # Get the existing contact attributes from the call, allocate to tghe 
    try:
        connect_client = boto3.client('connect')
        contact_attributes = connect_client.get_contact_attributes(
            InstanceId = instance_id,
            InitialContactId = contact_id
        )
        original_contact_attributes = contact_attributes['Attributes']

        # Add the VMX3 keys to the vmx_data container
        for key, value in original_contact_attributes.items():
            if key.startswith('vmx3_'):
                sub_response['vmx_data'].update({key:value})

        # Pop the VMX3 keys from the original_contact_attributes container
        for key in list(original_contact_attributes.keys()):
            if key.startswith('vmx3_'):
                original_contact_attributes.pop(key)

        sub_response.update({'original_contact_attributes':original_contact_attributes})

    except Exception as e:
        logger.error('********** Sub: Key Data Extraction - Failed to get contact attributes for voicemail **********')
        logger.error(e)
        raise Exception
    
    logger.info('********** Sub: Key Data Extraction - COMPLETE **********')
    logger.debug(sub_response)
    return sub_response