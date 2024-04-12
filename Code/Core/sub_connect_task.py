# Version: 2024.03.20
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

# Import the necessary modules for this flow to work
import json
import os
import logging
import boto3

# Establish logging configuration
logger = logging.getLogger()
logger.setLevel(logging.getLevelName(os.getenv('lambda_logging_level', 'DEBUG')))

connect_client = boto3.client('connect')

def vmx_to_connect_task(writer_payload):

    logger.info('Beginning Voicemail to Task')
    logger.debug(writer_payload)

    # Check for a task flow to use, if not, use default
    if 'vmx_task_flow' in writer_payload['json_attributes']:
        if writer_payload['json_attributes']['vmx_task_flow']:
            contact_flow = writer_payload['json_attributes']['vmx_task_flow']
        else:
            writer_payload.update({'task_flow':os.environ['default_task_flow']})

    else:
        contact_flow = os.environ['default_task_flow']

    try:
        create_task = connect_client.start_task_contact(
            InstanceId=writer_payload['instance_id'],
            PreviousContactId=writer_payload['contact_id'],
            ContactFlowId=contact_flow,
            Attributes=writer_payload['json_attributes'],
            Name='Voicemail for ' + writer_payload['json_attributes']['entity_name'],
            References={
                'Click link below to play voicemail': {
                    'Value': writer_payload['json_attributes']['presigned_url'],
                    'Type': 'URL'
                }
            },
            Description=writer_payload['json_attributes']['transcript_contents']
        )

        return 'success'

    except Exception as e:
        logger.error(e)
        logger.error('Failed to create task.')

        return 'fail'
