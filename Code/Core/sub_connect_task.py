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

# Import the necessary modules for this flow to work
import json
import os
import logging
import boto3

# Establish logging configuration
logger = logging.getLogger()

def vmx3_to_connect_task(writer_payload):

    # Debug lines for troubleshooting
    logger.debug('Code Version: ' + current_version)
    logger.debug('VMX3 Package Version: ' + os.environ['package_version'])
    logger.debug(writer_payload)

    # Establish needed clients and resources
    try:
        connect_client = boto3.client('connect')
        logger.debug('********** Clients initialized **********')
    
    except Exception as e:
        logger.error('********** VMX Initialization Error: Could not establish needed clients **********')
        logger.error(e)
        raise Exception

    logger.debug('Beginning Voicemail to Task')

    # Make sure transcript fits in field and truncate if it does not.
    transcript = writer_payload['json_attributes']['transcript_contents']
    if len(transcript) > 4096:
        transcript = transcript[:4092] + ' ...'
    
    # Check for a task flow to use, if not, use default
    if 'vmx3_task_flow' in writer_payload['json_attributes']:
        if writer_payload['json_attributes']['vmx3_task_flow']:
            contact_flow = writer_payload['json_attributes']['vmx3_task_flow']
        else:
            writer_payload.update({'vmx3_task_flow':os.environ['default_task_flow']})
            contact_flow = os.environ['default_task_flow']

    else:
        contact_flow = os.environ['default_task_flow']

    # Check if GenAI summary was selected and modify the references/description accordingly.
    if writer_payload['json_attributes']['vmx3_do_genai_summary'] == 'true':
        task_references = {
            'Date Voicemail Received': {
                'Value': writer_payload['json_attributes']['vmx3_dateTime'],
                'Type': 'STRING'
            },
            'Original Queue': {
                'Value': writer_payload['json_attributes']['entity_name'],
                'Type':'STRING'
            },
            'Voicemail Transcript': {
                'Value': transcript,
                'Type':'STRING'
            }
        }
        task_description = writer_payload['json_attributes']['vmx3_genai_summary']
    
    else: 
        task_references = {
            'Date Voicemail Received': {
                'Value': writer_payload['json_attributes']['vmx3_dateTime'],
                'Type': 'STRING'
            },
            'Original Queue': {
                'Value': writer_payload['json_attributes']['entity_name'],
                'Type':'STRING'
            }
        }
        task_description = transcript

    # Create the task
    try:
        create_task = connect_client.start_task_contact(
            InstanceId=writer_payload['instance_id'],
            ContactFlowId=contact_flow,
            PreviousContactId=writer_payload['contact_id'],
            Attributes={
                'Callback_Number': writer_payload['json_attributes']['callback_number']
            },
            Name='Voicemail for ' + writer_payload['json_attributes']['entity_name'],
            References=task_references,
            Description=task_description,
            ClientToken=writer_payload['contact_id']
        )
        logger.debug('********** Task Created **********')
        logger.debug(create_task)

        return create_task

    except Exception as e:
        logger.error('********** Failed to create task **********')
        logger.error(e)
        raise Exception