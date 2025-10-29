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

# Import required modules
import boto3
import json
import logging
import os
from datetime import datetime

# Import the VMX Model Types
import sub_connect_task
import sub_ses_email
import sub_connect_guided_task

# Import the Packager Key Functions
import sub_key_data_extraction
import sub_process_transcript
import sub_build_data_payload

# Establish logging configuration
logger = logging.getLogger()

def lambda_handler(event, context):
    
    # 0. Debug lines for troubleshooting
    logger.debug('Function Name: ' + os.environ['AWS_LAMBDA_FUNCTION_NAME'])
    logger.debug('Code Version: ' + current_version)
    logger.debug('VMX3 Package Version: ' + os.environ['package_version'])
    logger.debug('********** Beginning Voicemail Packager **********')
    logger.debug(event)
    
    # 1. Initialization: Process the incoming event, filter write checks, establish clients
    try:
        # Establish empty containers
        function_response = {} # for the response
        function_payload = {} # for passing data to sub functions

        # Filter out write checks
        if event['detail']['object']['key'].endswith('.write_access_check_file.temp'):
            logger.info('********** WRITE TEST - IGNORE **********')
            return('********** WRITE TEST - IGNORE **********')
    
        # Establish required clients
        lambda_client = boto3.client('lambda')
        transcribe_client = boto3.client('transcribe')
        connect_client = boto3.client('connect')
        logger.debug('********** Initialization Complete **********')
        logger.debug('********** Step 1 of 7 complete **********')

    except Exception as e:
        logger.error('********** Initialization Failed **********')
        logger.debug('********** Step 1 of 7 failed **********')
        logger.error(e)
        raise Exception
    

    # 2. Gather Voicemail Data for packaging (invoke sub_key_data_extraction)
    try:
        get_base_data = sub_key_data_extraction.key_data_extraction(event)
        logger.debug('********** Retrieved core data from events **********')
        function_payload.update(get_base_data)
        logger.debug('********** Step 2 of 7 complete **********')

    except Exception as e:
        logger.error('********** Failed to retrieve core data from events **********')
        logger.debug('********** Step 2 of 7 failed **********')
        logger.error(e)
        raise Exception
    

    # 3. Process transcript & do genai summary (invoke sub_process_transcript)
    try:
        process_transcript = sub_process_transcript.process_transcript(function_payload)
        logger.debug('********** Processed transcript **********')
        function_payload['vmx_data'].update(process_transcript)
        logger.debug('********** Step 3 of 7 complete **********')

    except Exception as e:
        logger.error('********** Failed to process transcript **********')
        logger.debug('********** Step 3 of 7 failed **********')
        logger.error(e)
        raise Exception
    

    # 4. Configure delivery payload (invoke sub_build_data_payload)
    try:
        configure_delivery_payload = sub_build_data_payload.build_data_payload(function_payload)
        logger.debug('********** Payload Set **********')
        function_payload['vmx_data'].update(configure_delivery_payload)
        logger.debug('********** Step 4 of 7 complete **********')

    except Exception as e:
        logger.error('********** Failed to set payload **********')
        logger.debug('********** Step 4 of 7 failed **********')
        logger.error(e)
        raise Exception

    logger.debug(function_payload['original_contact_attributes'])


    # 5. Invoke presigner Lambda to generate presigned URL for recording
    if function_payload['vmx_data']['vmx3_mode'] == 'email' or function_payload['vmx_data']['vmx3_mode'] == 'task':
    
        try:
            input_params = {
                'recording_bucket': function_payload['function_data']['recording_bucket'],
                'recording_key': function_payload['function_data']['recording_key'],
                'vmx3_mode': function_payload['vmx_data']['vmx3_mode']
            }

            presigner_lambda_response = lambda_client.invoke(
                FunctionName = os.environ['presigner_function_arn'],
                InvocationType = 'RequestResponse',
                Payload = json.dumps(input_params)
            )

            response_from_presigner = json.load(presigner_lambda_response['Payload'])
            raw_url = response_from_presigner['presigned_url']
            function_payload['vmx_data'].update({'vmx3_presigned_url':raw_url})
            logger.debug('********** Presigner Completed **********')
            logger.debug('********** Step 5 of 7 complete **********')

        except Exception as e:
            logger.error('********** Record Result: Failed to generate presigned URL **********')
            logger.error('********** Step 5 of 7 failed, but continuing with deliver since we have a transcript **********')
            logger.error(e)
            function_payload['vmx_data'].update({'vmx3_presigned_url':'https://github.com/amazon-connect/voicemail-express-amazon-connect/blob/main/Docs/vmx_troubleshooting.md#presigner-fails'})

    else:
        function_payload['vmx_data'].update({'vmx3_recording_key':function_payload['function_data']['recording_key']})

    logger.debug(function_payload)
    

    # 6. Deliver Voicemail
    if function_payload['vmx_data']['vmx3_mode'] == 'task':

        try:
            write_vm = sub_connect_task.vmx3_to_connect_task(function_payload)

        except Exception as e:
            logger.error('********** Failed to activate task function **********')
            logger.error('********** Step 6 of 7 failed **********')
            logger.error(e)
            raise Exception
        
    elif function_payload['vmx_data']['vmx3_mode'] == 'email':

        try:
            write_vm = sub_ses_email.vmx3_to_ses_email(function_payload)

        except Exception as e:
            logger.error('********** Failed to complete email function **********')
            logger.error('********** Step 6 of 7 failed **********')
            logger.error(e)
            raise Exception
        
    elif function_payload['vmx_data']['vmx3_mode'] == 'guided_task':

        try:
            write_vm = sub_connect_guided_task.vmx3_to_connect_guided_task(function_payload)

        except Exception as e:
            logger.error('********** Failed to complete guided task function **********')
            logger.error('********** Step 6 of 7 failed **********')
            logger.error(e)
            raise Exception

    else:
        logger.error('********** Invalid mode selection **********')
        logger.error('********** Step 6 of 7 failed **********')
        return {'status':'complete','result':'ERROR','reason':'Invalid mode selection'}

    if write_vm['result'] == 'success':
        logger.info('********** VM successfully written **********')

    else:
        logger.error('********** VM failed to write **********')
        logger.error('********** Step 6 of 7 failed **********')
        return {'status':'complete','result':'ERROR','reason':'Record VM failed to write'}
    
    logger.debug('********** Step 6 of 7 complete **********')

    # 7. Do cleanup
    # Delete the transcription job
    try:
        
        transcribe_client.delete_transcription_job(
            TranscriptionJobName='vmx3_' + function_payload['function_data']['contact_id']
        )
        logger.debug('********** Transcribe Job Deleted **********')

    except Exception as e:
        logger.error('********** Record Failed to delete transcription job **********')
        logger.error(e)

    # Clear the vmx_flag for this contact
    try:
        connect_client.update_contact_attributes(
            InitialContactId=function_payload['function_data']['contact_id'],
            InstanceId=function_payload['function_data']['instance_id'],
            Attributes={
                'vmx3_flag': '0'
            }
        )
        logger.debug('********** vmx_3_flag cleared for contact **********')

    except Exception as e:
        logger.error('********** Failed to clear vmx3_flag **********')
        logger.error(e)

    logger.debug('********** Step 7 of 7 complete **********')

    function_response.update({'status':'complete','result':'success'})
    return function_response