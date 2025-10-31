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
from botocore.client import Config

# Establish logging configuration
logger = logging.getLogger()

def lambda_handler(event, context):
    
    # Debug lines for troubleshooting
    logger.debug('Code Version: ' + current_version)
    logger.debug('VMX3 Package Version: ' + os.environ['package_version'])
    logger.debug(event)

    # Establish an empty response
    response = {}

    # Set the default result to success
    response.update({'result':'success'})

    # Retrieve credentials from AWS Secrets Manager
    try:
        use_keys = get_secret()
        logger.debug('********** Successfully retrieved keys **********')

    except Exception as e:
        logger.error('********** Key retrieval failed **********')
        logger.error(e)
        
        raise Exception

    # Configure the environment for the URL generation and initialize s3 client
    try:
        # Set the region to match the recording location
        use_region = os.environ['aws_region']
        logger.debug('Using region: ' + use_region)

        # Set the sig version and config options
        my_config = Config(
            region_name = use_region,
            signature_version = 's3v4',
            retries = {
                'max_attempts': 10,
                'mode': 'standard'
            }
        )

        s3_client = boto3.client(
            's3',
            endpoint_url = 'https://s3.' + use_region + '.amazonaws.com',
            aws_access_key_id = use_keys['vmx_iam_key_id'],
            aws_secret_access_key = use_keys['vmx_iam_key_secret'],
            config=my_config
        )

        logger.debug('********** S3 client initialized with localiation and parameters **********')

    except Exception as e:
        logger.error('********** S3 client failed to initialize **********')
        logger.error(e)
        raise Exception

    # Generate the presigned URL and return
    try:
        
        vmx3_mode = event['vmx3_mode']
        if vmx3_mode == 'task':
            expires_in = int(os.environ['tasks_url_expire'])*86400

        elif vmx3_mode == 'email':
            expires_in = int(os.environ['email_url_expire'])*86400

        else:
            expires_in = 7*86400

        presigned_url = s3_client.generate_presigned_url('get_object',
            Params = {'Bucket': event['recording_bucket'],
                    'Key': event['recording_key']},
            ExpiresIn = expires_in
        )

        logger.debug('********** Presigned URL Generated successfully **********')
        logger.debug('Presigned URL: ' + presigned_url)
        response.update({'presigned_url': presigned_url})

        return response

    except Exception as e:
        logger.error('********** Presigned URL Failed to generate **********')
        logger.error(e)
        raise Exception

# Sub to retrieve the secrets from Secrets Manager
def get_secret():
    # Set response container
    secret_response = {}

    # Set secrets environment
    try:
        secret_name = os.environ['secrets_key_id']
        region_name = os.environ['aws_region']
        logger.debug('********** Secrets environment vars set **********')

    except Exception as e:
        logger.error('********** Secrets environment vars failed to set **********')
        logger.error(e)
        raise Exception

    # Create a Secrets Manager session
    try:
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )

        logger.debug('********* Secrets session initialized **********')

    except Exception as e:
        logger.error('********** Secrets session failed to initialize **********')
        logger.error(e)
        raise Exception

    # Get the secrets
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        secret = get_secret_value_response['SecretString']
        secret_response.update(json.loads(secret))

        logger.debug('********** Successfully retrieved secrets **********')

        return secret_response

    except Exception as e:
        logger.error('********** Failed to get secrets **********')
        logger.error(e)
        raise Exception