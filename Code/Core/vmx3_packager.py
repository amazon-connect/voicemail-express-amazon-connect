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
import os
import logging
import boto3
import phonenumbers
from datetime import datetime

# Import the VMX Model Types
import sub_connect_task
import sub_ses_email

# Establish logging configuration
logger = logging.getLogger()

def lambda_handler(event, context):
    
    # Debug lines for troubleshooting
    logger.debug('Code Version: ' + current_version)
    logger.debug('VMX3 Package Version: ' + os.environ['package_version'])
    logger.debug(event)

    # Establish required clients and resources
    try:
        connect_client = boto3.client('connect')
        lambda_client = boto3.client('lambda')
        s3_client = boto3.client('s3')
        s3_resource = boto3.resource('s3')
        transcribe_client = boto3.client('transcribe')
        logger.debug('********** Clients initialized **********')

    except Exception as e:
        logger.error('********** VMX INITIALIZATION: Failed to initialize clients **********')
        logger.error(e)
        
        return {'status':'complete','result':'ERROR','reason':'Failed to initialize'}

    # Establish writer data
    writer_payload = {}
    
    # Process the record
    # Establish data for transcript and recording, and clear out write tests.
    try:
        original_transcript_key = event['detail']['object']['key']
        if original_transcript_key == '.write_access_check_file.temp':
            return('********** WRITE TEST - IGNORE **********')
        transcript_key = original_transcript_key[5:]
        transcript_job = transcript_key.replace('.json','')
        contact_id = transcript_job.split('_',1)[0]
        recording_key = contact_id + '.wav'
        transcript_bucket = os.environ['s3_transcripts_bucket']
        recording_bucket = os.environ['s3_recordings_bucket']
        logger.debug('********** Successvulluy extracted ID data **********')

    except Exception as e:
        logger.error('********** Record Result: Failed to extract keys **********')
        logger.error(e)
        
        return {'status':'complete','result':'ERROR','reason':'Failed to extract keys'}

    # Invoke presigner Lambda to generate presigned URL for recording
    try:
        input_params = {
            'recording_bucket': recording_bucket,
            'recording_key': recording_key
        }

        lambda_response = lambda_client.invoke(
            FunctionName = os.environ['presigner_function_arn'],
            InvocationType = 'RequestResponse',
            Payload = json.dumps(input_params)
        )
        response_from_presigner = json.load(lambda_response['Payload'])
        raw_url = response_from_presigner['presigned_url']
        logger.debug('********** Presigner Completed **********')

    except Exception as e:
        logger.error('********** Record Result: Failed to generate presigned URL **********')
        logger.error(e)
        
        return {'status':'complete','result':'ERROR','reason':'Failed to generate presigned URL'}

    # Extract the tags from the recording object
    try:
        object_data = s3_client.get_object_tagging(
            Bucket = recording_bucket,
            Key = recording_key
        )

        object_tags = object_data['TagSet']
        loaded_tags = {}

        for i in object_tags:
            loaded_tags.update({i['Key']:i['Value']})
        
        logger.debug('********** Extracted s3 tags from recording **********')

    except Exception as e:
        logger.error('********** Record Result: Failed to extract tags **********')
        logger.error(e)
        
        return {'status':'complete','result':'ERROR','reason':'Failed to extract tags'}

    # Grab the transcript from S3
    try:
        transcript_object = s3_resource.Object(transcript_bucket, original_transcript_key)
        file_content = transcript_object.get()['Body'].read().decode('utf-8')
        json_content = json.loads(file_content)
        transcript_contents = json_content['results']['transcripts'][0]['transcript']
        logger.debug('********** Retrieved transcript from S3 **********')

    except Exception as e:
        logger.error('Failed to retrieve transcript')
        logger.error(e)
        
        return {'status':'complete','result':'ERROR','reason':'Failed to retrieve transcript'}

    # Set instance attributes
    try:
        queue_arn = loaded_tags['vmx3_queue_arn']
        arn_substring = queue_arn.split('instance/')[1]
        instance_id = arn_substring.split('/queue')[0]
        queue_id = arn_substring.split('queue/')[1]
        writer_payload.update({'instance_id':instance_id,'contact_id':contact_id,'queue_id':queue_id})
        logger.debug('********** Instance attributes set **********')

    except Exception as e:
        logger.error('********** Record Result: Failed to set instance attributess **********')
        logger.error(e)
        
        return {'status':'complete','result':'ERROR','reason':'Failed to set instance attributes'}

    # Determine queue type and set entity vars
    if queue_id.startswith('agent'):
        try:
            logger.debug('********** Agent routing **********')
            writer_payload.update({'entity_type':'agent'})
            # Set the Agent ID
            agent_id = arn_substring.split('agent/')[1]
            # Grab agent info
            get_agent = connect_client.describe_user(
                UserId = agent_id,
                InstanceId = instance_id
            )

            entity_name = get_agent['User']['IdentityInfo']['FirstName']+' '+get_agent['User']['IdentityInfo']['LastName']
            entity_id = get_agent['User']['Username']
            entity_description = 'Amazon Connect Agent'
            logger.debug('Targeted Agent: ' + entity_name)

        except Exception as e:
            logger.error('********** Record Result: Failed to find agent **********')
            logger.error(e)
            
            entity_name = 'UNKNOWN'

    else:
        try:
            logger.debug('********** Queue routing **********')
            writer_payload.update({'entity_type':'queue'})
            # Grab Queue info
            get_queue_details = connect_client.describe_queue(
                InstanceId=instance_id,
                QueueId=queue_id
            )

            entity_name = get_queue_details['Queue']['Name']
            entity_id = get_queue_details['Queue']['QueueArn']
            entity_description = 'Amazon Connect Queue'
            logger.debug('Targeted Queue: ' + entity_name)
            
        except Exception as e:
            logger.error('********** Record Result: Failed to extract queue details **********')
            logger.error(e)
            
            entity_name = 'UNKNOWN'

    # Get the current date and time in UTC using timezone-aware objects
    try:
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%A, %b %d at %I:%M %p (Instance Time)")
        logger.debug('Processed Timestamp: ' + formatted_datetime)
    
    except Exception as e:
        logger.error('********** Record Result: Failed to get timestamp **********')
        logger.error(e)
        
        formatted_datetime = 'UNKNOWN'

    # Get the existing contact attributes from the call and append the standard vars for voicemail to the attributes
    try:
        contact_attributes = connect_client.get_contact_attributes(
            InstanceId = instance_id,
            InitialContactId = contact_id
        )
        json_attributes = contact_attributes['Attributes']
        json_attributes.update({'entity_name':entity_name,'entity_id':entity_id,'entity_description':entity_description,'transcript_contents':transcript_contents,'callback_number':json_attributes['vmx3_from'],'presigned_url':raw_url,'vmx3_dateTime': formatted_datetime})
        writer_payload.update({'json_attributes':json_attributes})
        contact_attributes = json.dumps(contact_attributes['Attributes'])
        logger.debug('Original Contact Attributes: ' + contact_attributes)

    except Exception as e:
        logger.error('********** Record Result: Failed to extract attributes **********')
        logger.error(e)
        
        contact_attributes = 'UNKNOWN'

    logger.debug(writer_payload)

    # Determing VMX mode
    if 'vmx3_mode' in writer_payload['json_attributes']:
        if writer_payload['json_attributes']['vmx3_mode']:
            vmx3_mode = writer_payload['json_attributes']['vmx3_mode']
    else:
        vmx3_mode = os.environ['default_vmx_mode']

    logger.debug('VM Mode set to {0}.'.format(vmx3_mode))

    # Execute the correct VMX mode
    if vmx3_mode == 'task':

        try:
            write_vm = sub_connect_task.vmx3_to_connect_task(writer_payload)

        except Exception as e:
            logger.error('********** Failed to activate task function **********')
            logger.error(e)
            
            return {'status':'complete','result':'ERROR','reason':'Failed to activate task function'}
        
    elif vmx3_mode == 'email':

        # Define the appropriate email target
        if writer_payload['entity_type'] == 'agent':
            try:
                entity_email = get_agent['User']['IdentityInfo']['Email']
            except: 
                entity_email = os.environ['default_email_target']

        else:
            try:
                entity_email = get_queue_details['Queue']['Tags']['vmx3_queue_email']
            except: 
                entity_email = os.environ['default_email_target']

        writer_payload.update({'entity_email':entity_email})
        logger.debug('Entity Email: ' + entity_email)

        try:
            write_vm = sub_ses_email.vmx3_to_ses_email(writer_payload)

        except Exception as e:
            logger.error('********** Failed to activate email function **********')
            logger.error(e)
            
            return {'status':'complete','result':'ERROR','reason':'Failed to activate email function'}

    else:
        logger.error('********** Invalid mode selection **********')
        return {'status':'complete','result':'ERROR','reason':'Invalid mode selection'}

    if write_vm == 'success':
        logger.info('********** VM successfully written **********')

    else:
        logger.error('********** VM failed to write **********')
        return {'status':'complete','result':'ERROR','reason':'Record VM failed to write'}

    # End Voicemail Writer

    # Do some cleanup
    # Delete the transcription job
    try:
        
        transcribe_client.delete_transcription_job(
            TranscriptionJobName=original_transcript_key.replace('.json','')
        )
        logger.debug('Transcribe Job Deleted')

    except Exception as e:
        logger.error('********** Record Failed to delete transcription job **********')
        logger.error(e)
        

    # Clear the vmx_flag for this contact
    try:
        update_flag = connect_client.update_contact_attributes(
            InitialContactId=contact_id,
            InstanceId=instance_id,
            Attributes={
                'vmx3_flag': '0'
            }
        )
        logger.debug('********** vmx_3_flag cleared for contact **********')

    except Exception as e:
        logger.error('********** Failed to change vmx3_flag **********')
        logger.error(e)
        

    return {'status': 'complete','result': 'Record processed'}