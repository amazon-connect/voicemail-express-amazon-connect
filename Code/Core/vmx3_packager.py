# Version: 2024.05.01
"""
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
"""

# Import the necessary modules for this function
import json
import os
import logging
import boto3
import phonenumbers
from datetime import datetime, timezone

# Import the VMX Model Type
import sub_connect_task

# Establish logging configuration
logger = logging.getLogger()
logger.setLevel(logging.getLevelName(os.getenv('lambda_logging_level', 'DEBUG')))
connect_client = boto3.client('connect')

def lambda_handler(event, context):
    logger.debug(event)

    # Process the record
    # Establish writer data
    writer_payload = {}

    # Establish data for transcript and recording, and clear out write tests.
    try:
        original_transcript_key = event['detail']['object']['key']
        if original_transcript_key == '.write_access_check_file.temp':
            return('**********WRITE TEST - IGNORE**********')
        transcript_key = original_transcript_key[5:]
        transcript_job = transcript_key.replace('.json','')
        contact_id = transcript_job.split('_',1)[0]
        recording_key = contact_id + '.wav'
        transcript_bucket = os.environ['s3_transcripts_bucket']
        recording_bucket = os.environ['s3_recordings_bucket']

    except Exception as e:
        logger.error(e)
        logger.error('Record Result: Failed to extract keys')
        return {'result':'Failed to extract keys'}

    # Invoke presigner Lambda to generate presigned URL for recording
    try:
        client = boto3.client('lambda')

        input_params = {
            'recording_bucket': recording_bucket,
            'recording_key': recording_key
        }

        lambda_response = client.invoke(
            FunctionName = os.environ['presigner_function_arn'],
            InvocationType = 'RequestResponse',
            Payload = json.dumps(input_params)
        )
        response_from_presigner = json.load(lambda_response['Payload'])
        raw_url = response_from_presigner['presigned_url']

    except Exception as e:
        logger.error(e)
        logger.error('Record Result: Failed to generate presigned URL')
        return {'result':'Failed to generate presigned URL'}

    # Extract the tags from the recording object
    try:
        s3_client = boto3.client('s3')
        object_data = s3_client.get_object_tagging(
            Bucket = recording_bucket,
            Key = recording_key
        )

        object_tags = object_data['TagSet']
        loaded_tags = {}

        for i in object_tags:
            loaded_tags.update({i['Key']:i['Value']})

    except Exception as e:
        logger.error(e)
        logger.error('Record Result: Failed to extract tags')
        return {'result':'Failed to extract tags'}

    # Grab the transcript from S3
    try:
        s3_resource = boto3.resource('s3')

        transcript_object = s3_resource.Object(transcript_bucket, original_transcript_key)
        file_content = transcript_object.get()['Body'].read().decode('utf-8')
        json_content = json.loads(file_content)

        transcript_contents = json_content['results']['transcripts'][0]['transcript']

    except Exception as e:
        logger.error(e)
        logger.error('Record Result: Failed to retrieve transcript')
        return {'result':'Failed to retrieve transcript'}

    # Set some key vars
    queue_arn = loaded_tags['vmx3_queue_arn']
    arn_substring = queue_arn.split('instance/')[1]
    instance_id = arn_substring.split('/queue')[0]
    queue_id = arn_substring.split('queue/')[1]
    writer_payload.update({'instance_id':instance_id,'contact_id':contact_id,'queue_id':queue_id})

    # Determine queue type and set additional vars
    if queue_id.startswith('agent'):
        try:
            writer_payload.update({'entity_type':'agent'})
            # Set the Agent ID
            agent_id = arn_substring.split('agent/')[1]
            # Grab agent info
            get_agent = connect_client.describe_user(
                UserId = agent_id,
                InstanceId = instance_id
            )
            logger.debug(get_agent['User']['IdentityInfo'])
            entity_name = get_agent['User']['IdentityInfo']['FirstName']+' '+get_agent['User']['IdentityInfo']['LastName']
            entity_id = get_agent['User']['Username']
            entity_description = 'Amazon Connect Agent'

        except Exception as e:
            logger.error(e)
            logger.error('Record Result: Failed to find agent')
            entity_name = 'UNKNOWN'

    else:
        writer_payload.update({'entity_type':'queue'})
        # Grab Queue info
        get_queue_details = connect_client.describe_queue(
            InstanceId=instance_id,
            QueueId=queue_id
        )

        try:
            entity_name = get_queue_details['Queue']['Name']
            entity_id = get_queue_details['Queue']['QueueArn']
            entity_description = 'Amazon Connect Queue'
        except Exception as e:
            logger.error(e)
            logger.error('Record Result: Failed to extract queue name')
            entity_name = 'UNKNOWN'

    # Get the current date and time in UTC using timezone-aware objects
    current_datetime = datetime.now(timezone.utc).isoformat()

    # Get the existing contact attributes from the call and append the standard vars for voicemail to the attributes
    try:
        contact_attributes = connect_client.get_contact_attributes(
            InstanceId = instance_id,
            InitialContactId = contact_id
        )
        json_attributes = contact_attributes['Attributes']
        json_attributes.update({'entity_name':entity_name,'entity_id':entity_id,'entity_description':entity_description,'transcript_contents':transcript_contents,'callback_number':json_attributes['vmx3_from'],'presigned_url':raw_url,'vmx3_dateTime': current_datetime})
        writer_payload.update({'json_attributes':json_attributes})
        contact_attributes = json.dumps(contact_attributes['Attributes'])

    except Exception as e:
        logger.error(e)
        logger.error('Record Result: Failed to extract attributes')
        contact_attributes = 'UNKNOWN'

    logger.debug(writer_payload)

    # Determing VMX mode
    if 'vmx3_mode' in writer_payload['json_attributes']:
        if writer_payload['json_attributes']['vmx3_mode']:
            vmx3_mode = writer_payload['json_attributes']['vmx3_mode']
    else:
        vmx3_mode = 'task' 

    logger.debug('VM Mode set to {0}.'.format(vmx3_mode))

    # Execute the correct VMX mode
    if vmx3_mode == 'task':

        try:
            write_vm = sub_connect_task.vmx_to_connect_task(writer_payload)

        except Exception as e:
            logger.error(e)
            logger.error('Failed to activate task function')
            return {'result':'Failed to activate task function'}

    else:
        logger.error('Invalid mode selection')
        return {'result':'Invalid mode selection'}

    if write_vm == 'success':
        logger.info('Record VM successfully written')

    else:
        logger.info('Record VM failed to write')
        return {'result':'Record VM failed to write'}

    # End Voicemail Writer

    # Do some cleanup
    # Delete the transcription job
    try:
        transcribe_client = boto3.client('transcribe')
        transcribe_client.delete_transcription_job(
            TranscriptionJobName=original_transcript_key.replace('.json','')
        )

    except Exception as e:
        logger.error(e)
        logger.error('Record Failed to delete transcription job')

    # Clear the vmx_flag for this contact
    try:

        update_flag = connect_client.update_contact_attributes(
            InitialContactId=contact_id,
            InstanceId=instance_id,
            Attributes={
                'vmx3_flag': '0'
            }
        )

    except Exception as e:
        logger.error(e)
        logger.error('Record Failed to change vmx3_flag')

    return {
        'status': 'complete',
        'result': 'Record processed'
    }