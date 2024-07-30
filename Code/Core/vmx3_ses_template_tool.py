"""
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
"""
import json
import boto3
import logging
import os

ses_client = boto3.client('sesv2')
logger = logging.getLogger()

def lambda_handler(event, context):
    logger.debug('VMX3 Version: ' + os.environ['package_version'])
    if event['mode'] == 'create':
        # Creates the template using the provided values
        try:
            create_template = ses_client.create_email_template(
                TemplateName = event['template_name'],
                TemplateContent = {
                    'Subject': event['template_subject'],
                    'Text': event['template_text'],
                    'Html': event['template_html']
                }
            )

            return 'Template creation succeeded'

        except Exception as e:
            logger.error(e)

            return 'Template creation failed'

    elif event['mode'] == 'get':
        try:
            # Retrieves the template using the test data
            get_template = ses_client.get_email_template(TemplateName=event['template_name'])

            #  Removes the API response header
            get_template.pop('ResponseMetadata')

            # Returns the template as a string value
            return(str(get_template))

        except Exception as e:
            logger.error(e)

            return 'Template retrieval failed'

    elif event['mode'] == 'update':
        # Updates the template using the provided values
        try:
            create_template = ses_client.update_email_template(
                TemplateName=event['template_name'],
                TemplateContent={
                    'Subject': event['template_subject'],
                    'Text': event['template_text'],
                    'Html': event['template_html']
                }
            )

            return 'Template update succeeded'

        except Exception as e:
            logger.error(e)

            return 'Template update failed'


    elif event['mode'] == 'delete':
        # Deletes the template using the provided name
        try:
            template_delete = ses_client.delete_email_template(
                TemplateName = event['template_name']
            )
            return event['template_name'] + ' template deleted.'

        except Exception as e:
            logger.error(e)
            return 'Template delete failed'
