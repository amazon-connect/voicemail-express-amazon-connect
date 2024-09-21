current_version = '2024.09.01'
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
import boto3
import logging
from botocore.client import Config
import base64
import os

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
        logger.debug(my_config)

        s3_client = boto3.client(
            's3',
            endpoint_url = 'https://s3.' + use_region + '.amazonaws.com',
            config=my_config
        )

        logger.debug('********** S3 client initialized with localiation and parameters **********')

    except Exception as e:
        logger.error('********** S3 client failed to initialize **********')
        logger.error(e)
        response.update({'status':'complete','result':'ERROR','reason':'s3 client init failed'})

        return response

    # Generate the presigned URL and return
    try:
        use_bucket = os.environ['s3_recordings_bucket']
        logger.debug(use_bucket)
        vm_key = event['Details']['ContactData']['Attributes']['contact_id'] + '.wav'
        logger.debug(vm_key)
        
        presigned_url = s3_client.generate_presigned_url('get_object',
            Params = {'Bucket': use_bucket,
                    'Key': vm_key},
            ExpiresIn = 600
        )

        logger.debug('********** Presigned URL Generated successfully **********')
        logger.debug('Presigned URL: ' + presigned_url)
        response.update({'presigned_url': presigned_url})

    except Exception as e:
        logger.error('********** Presigned URL Failed to generate **********')
        logger.error(e)
        response.update({'status':'complete','result':'ERROR','reason':'presigned url generation failed'})
        return response

    return response