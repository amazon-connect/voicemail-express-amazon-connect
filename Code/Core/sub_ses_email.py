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

# Establish logging configuration
logger = logging.getLogger()

def vmx3_to_ses_email(function_payload):

    # Debug lines for troubleshooting
    logger.debug('Function Name: ' + os.environ['AWS_LAMBDA_FUNCTION_NAME'])
    logger.debug('Code Version: ' + current_version)
    logger.debug('VMX3 Package Version: ' + os.environ['package_version'])
    logger.debug('********** Beginning Voicemail Email Delivery **********')
    logger.debug(function_payload)

    # Establish an empty container
    function_response = {}

    # 1. Establish clients and baseline data
    logger.debug('Beginning Voicemail to email')
    # Load clients
    try:
        ses_client = boto3.client('sesv2')
        logger.debug('********** Client initialized **********')
    
    except Exception as e:
        logger.error('********** VMX Initialization Error: Could not establish needed clients **********')
        logger.error(e)
        raise Exception
    
    # Get baseline data
    email_working_data = function_payload['vmx_data']
    logger.debug('********** Base data initialized **********')
    logger.debug('********** Step 1 of 3 Complete **********')

    # 2. Do mode and address checks. Pull in defaults where necessary
    # Identify the proper address to send the email FROM
    if 'vmx3_email_from' in email_working_data:
        if email_working_data['vmx3_email_from']:
            vmx3_email_from_address = email_working_data['vmx3_email_from']
    else:
        vmx3_email_from_address = os.environ['default_email_from']

    logger.debug('FROM ADDRESS: ' + vmx3_email_from_address)

    # Identify the proper address to send the email TO
    if 'vmx3_email_target_address' in email_working_data:
        if email_working_data['vmx3_email_target_address']:
            vmx3_email_target_address = email_working_data['vmx3_email_target_address']
    else:
        vmx3_email_target_address = os.environ['default_email_target']

    if '@' in vmx3_email_target_address:
        logger.info('Valid email address format')

    else:
        vmx3_email_target_address = os.environ['default_email_target']

    logger.debug('TO ADDRESS: ' + vmx3_email_target_address)

    # Identify the template to use
    if 'vmx3_email_template' in email_working_data:
        if email_working_data['vmx3_email_template']:
            vmx3_email_template = email_working_data['vmx3_email_template']

    else:
        if email_working_data['vmx3_target'] == 'agent':
            vmx3_email_template = os.environ['default_agent_email_template']

        else:
            vmx3_email_template = os.environ['default_queue_email_template']

    logger.debug('TEMPLATE: ' + vmx3_email_template)

    # Make sure transcript fits in field and truncate if it does not.
    vmx3_transcript = email_working_data['vmx3_transcript_contents']
    if len(vmx3_transcript) > 2048:
        vmx3_short_transcript = vmx3_transcript[:2048] + ' ...(truncated)'
        logger.debug('********** Transcript truncated **********')
    else:
        logger.debug('********** Transcript within limits **********')
        vmx3_short_transcript = vmx3_transcript

    email_working_data.update({'vmx3_transcript_contents':vmx3_short_transcript})

    # Dump data to text for inclusion in SES template
    vmx3_email_data = json.dumps(email_working_data)

    logger.debug('********** Step 2 of 3 Complete **********')
    
    # 3. Send the email using SES
    try:    
        send_email = ses_client.send_email(
            FromEmailAddress=vmx3_email_from_address,
            Destination={
                'ToAddresses': [
                    vmx3_email_target_address,
                ],
            },
            Content={
                'Template': {
                    'TemplateName': vmx3_email_template,
                    'TemplateData': vmx3_email_data
                }
            }
        )
        logger.debug('********** Email request sent **********')
        logger.debug(send_email)
        logger.debug('********** Step 3 of 3 Complete **********')

        function_response.update({'result':'success','email': send_email})
        return function_response

    except Exception as e:
        logger.error('********** Failed to send email **********')
        logger.error(e)
        raise Exception