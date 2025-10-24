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

def build_data_payload(function_payload):

    # Debug lines for troubleshooting
    logger.debug('Function Name: ' + os.environ['AWS_LAMBDA_FUNCTION_NAME'])
    logger.debug('Code Version: ' + current_version)
    logger.debug('VMX3 Package Version: ' + os.environ['package_version'])
    logger.info('********** Beginning Sub:Build Data Payload **********')
    logger.debug(function_payload)

    # Establish an empty container
    sub_response = {}

    # Set VMX delivery mode
    try:
        if 'vmx3_mode' in function_payload['vmx_data']:
            if function_payload['vmx_data']['vmx3_mode']:
                vmx3_mode = function_payload['vmx_data']['vmx3_mode']
        else:
            vmx3_mode = os.environ['default_vmx_mode']

        sub_response.update({'vmx3_mode':vmx3_mode})
        logger.debug('********** VM Mode set to ' + vmx3_mode + ' **********')
    
    except Exception as e:
        logger.error('********** Failed to set VM Mode **********')
        logger.error(e)
        raise Exception

    # Determine target type and set entity vars
    connect_client = boto3.client('connect')

    # Find and set agent-specific attributes
    if function_payload['vmx_data']['vmx3_target'] == 'agent':
        logger.debug('********** Preferred agent routing **********')

        try:          
            # Set the Agent Username
            agent_username = function_payload['vmx_data']['vmx3_preferred_agent']
            # Find the agent ID
            find_agent = connect_client.search_users(
                InstanceId = function_payload['function_data']['instance_id'],
                MaxResults=1,
                SearchCriteria={
                    'OrConditions':[
                        {
                            'StringCondition':{
                                'FieldName':'Username',
                                'Value':agent_username,
                                'ComparisonType':'EXACT'
                            }
                        }
                    ]
                }
            )
            # Set the agent ID
            agent_id = find_agent['Users'][0]['Id']
            sub_response.update({'vmx3_preferred_agent_id':agent_id})

            # Get the agent info
            get_agent = connect_client.describe_user(
                UserId = agent_id,
                InstanceId = function_payload['function_data']['instance_id']
            )

            # Set the Agent Name
            vmx3_agent_name = get_agent['User']['IdentityInfo']['FirstName'] + ' ' + get_agent['User']['IdentityInfo']['LastName']
            sub_response.update({'vmx3_agent_name':vmx3_agent_name})
            logger.debug('Targeted Agent: ' + vmx3_agent_name)

            # Set the email for agent
            if vmx3_mode == 'email':
                try:
                    identity_type = os.environ['agent_email_key']
                    if identity_type == 'Username':
                        vmx3_email_to = get_agent['User'][identity_type]
                    else:
                        vmx3_email_to = get_agent['User']['IdentityInfo'][identity_type]
                except: 
                    vmx3_email_to = os.environ['default_email_target']
                
                sub_response.update({'vmx3_email_to':vmx3_email_to})

        except Exception as e:
            logger.error('********** Record Result: Failed to find agent **********')
            logger.error(e)
    else:
        sub_response.update({'vmx3_preferred_agent_id':'NONE'})

        try:
            logger.debug('********** Queue routing **********')
            # Grab Queue info
            get_queue_details = connect_client.describe_queue(
                InstanceId=function_payload['function_data']['instance_id'],
                QueueId=function_payload['function_data']['queue_id']
            )

            vmx3_queue_name = get_queue_details['Queue']['Name']
            vmx3_queue_arn = get_queue_details['Queue']['QueueArn']
            sub_response.update({'vmx3_queue_name':vmx3_queue_name,'vmx3_queue_arn':vmx3_queue_arn})
            
            if vmx3_mode == 'email':
                try:
                    vmx3_email_to = get_queue_details['Queue']['Tags']['vmx3_queue_email']
                except: 
                    vmx3_email_to = os.environ['default_email_target']
                
                sub_response.update({'vmx3_email_to':vmx3_email_to})

            logger.debug('Targeted Queue: ' + vmx3_queue_name)
            
        except Exception as e:
            logger.error('********** Record Result: Failed to extract queue details **********')
            logger.error(e)
            
            entity_name = 'UNKNOWN'

    logger.info('********** Sub:Build Data Payload Complete **********')
    logger.debug(sub_response)
    return sub_response