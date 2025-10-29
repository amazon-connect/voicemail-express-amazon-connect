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

def vmx3_to_connect_guided_task(function_payload):

    # Debug lines for troubleshooting
    logger.debug('********** Beginning Sub: Voicemail to Guided Task **********')
    logger.debug(function_payload)

    # Establish an empty container
    function_response = {}

    # 1. Establish clients
    try:
        connect_client = boto3.client('connect')
        logger.debug('********** Clients initialized **********')
    
    except Exception as e:
        logger.error('********** Could not establish needed clients **********')
        logger.error(e)
        raise Exception
    
    logger.debug('********** Sub: Voicemail to Guided Task Step 1 of 3 Complete **********')

    # 2. Set parameters
    # Make sure transcript fits in a task field and truncate if it does not.
    # Make sure transcript fits in field and truncate if it does not.
    vmx3_transcript = function_payload['vmx_data']['vmx3_transcript_contents']
    if len(vmx3_transcript) > 2048:
        vmx3_short_transcript = vmx3_transcript[:2048] + ' ...(truncated)'
        logger.debug('********** Transcript truncated **********')
    else:
        logger.debug('********** Transcript within limits **********')
        vmx3_short_transcript = vmx3_transcript

    # Check for a task flow to use, if not, use default
    if 'vmx3_guided_task_flow' in function_payload['vmx_data']:
        if function_payload['vmx_data']['vmx3_guided_task_flow']:
            contact_flow = function_payload['vmx_data']['vmx3_guided_task_flow']
        else:
            contact_flow = os.environ['default_guided_task_flow']

    else:
        contact_flow = os.environ['default_guided_task_flow']

    # Check if GenAI summary was selected and modify the references/description accordingly.
    if function_payload['vmx_data']['vmx3_do_genai_summary'] == 'true':
        logger.debug('********** GenAI Summary Enabled **********')
        task_references = {
            'Date Voicemail Received': {
                'Value': function_payload['vmx_data']['vmx3_datetime'],
                'Type':'STRING'
            },
            'Original Queue': {
                'Value': function_payload['vmx_data']['vmx3_queue_name'],
                'Type':'STRING'
            },
            'GenAI Summary': {
                'Value': function_payload['vmx_data']['vmx3_genai_summary'],
                'Type':'STRING'
            },
            'Voicemail Transcript': {
                'Value': vmx3_short_transcript,
                'Type':'STRING'
            }
        }
    
    else:
        logger.debug('********** GenAI Summary Disabled **********')
        task_references = {
            'Date Received': {
                'Value': function_payload['vmx_data']['vmx3_datetime'],
                'Type':'STRING'
            },
            'Source Queue': {
                'Value': function_payload['vmx_data']['vmx3_queue_name'],
                'Type':'STRING'
            },
            'Voicemail Transcript': {
                'Value': vmx3_short_transcript,
                'Type':'STRING'
            },
            'GenAI Summary': {
                'Value': 'Not enabled for this voicemail.',
                'Type':'STRING'
            },
        }
    logger.debug('********** Sub: Voicemail to Guided Task Step 2 of 3 Complete **********')

    # Step 3. Create the Task
    try:
        create_task = connect_client.start_task_contact(
            InstanceId=function_payload['function_data']['instance_id'],
            ContactFlowId=contact_flow,
            PreviousContactId=function_payload['function_data']['contact_id'],
            Attributes={
                'vmx3_callback_number': function_payload['vmx_data']['vmx3_from'],
                'vmx3_recording_key': function_payload['vmx_data']['vmx3_recording_key'],
                'vmx3_genai_summary': function_payload['vmx_data']['vmx3_genai_summary'],
                'vmx3_timestamp': function_payload['vmx_data']['vmx3_datetime'],
                'vmx3_source_queue': function_payload['vmx_data']['vmx3_queue_name'],
                'vmx3_transcript': vmx3_transcript,
                'vmx3_preferred_agent_id': function_payload['vmx_data']['vmx3_preferred_agent_id']
            },
            Name='Amazon Connect Voicemail',
            References=task_references,
            Description='Amazon Connect Voicemail',
            ClientToken=function_payload['function_data']['contact_id']
        )
        logger.debug(create_task)
        logger.debug('********** Voicemail Guided Task Created **********')
        logger.debug('********** Sub Guided Task Step 3 of 3 Complete **********')

        function_response.update({'result':'success','task': create_task})
        return function_response

    except Exception as e:
        logger.error('********** Failed to create task **********')
        logger.error(e)
        raise Exception