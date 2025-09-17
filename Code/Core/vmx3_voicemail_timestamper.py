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

# Import the necessary modules for this function
import logging
import datetime

# Establish logging configuration
logger = logging.getLogger()

def lambda_handler(event, context):

    try:
        # Get the current time in UTC
        now_utc = datetime.datetime.now(datetime.timezone.utc)

        # Format the datetime object to ISO string format
        iso_format = now_utc.isoformat()

        # Truncate microseconds and replace the UTC offset '+00:00' with 'Z' to match Amazon Connect formatting
        vmx3_timestamp = now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

        return {
            'vmx3_timestamp':vmx3_timestamp
        }
    
    except Exception as e:
        logger.error('********** Could not get current timestamp **********')
        logger.error(e)
        raise Exception