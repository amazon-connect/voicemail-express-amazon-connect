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
import os

# Establish logging configuration
logger = logging.getLogger()

def lambda_handler(event, context):
    # Debug lines for troubleshooting
    logger.debug('Code Version: ' + current_version)
    logger.debug('VMX3 Package Version: ' + os.environ['package_version'])
    logger.debug(event)

    # Establish needed clients and resources
    try:
        ses_client = boto3.client('sesv2')
        logger.debug('********** Clients initialized **********')
    
    except Exception as e:
        logger.error('********** VMX Initialization Error: Could not establish needed clients **********')
        logger.error(e)

        return {'status':'complete','result':'ERROR','reason':'Failed to Initialize clients'}

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
            logger.debug('********** Template Created **********')
            logger.debug(create_template)

            return 'Template creation succeeded'

        except Exception as e:
            logger.error('Template creation failed')
            logger.error(e)

            return 'Template creation failed'

    elif event['mode'] == 'get':
        try:
            # Retrieves the template using the test data
            get_template = ses_client.get_email_template(TemplateName=event['template_name'])
            logger.debug('********** Template retrieved **********')
            logger.debug(get_template)

            #  Removes the API response header
            get_template.pop('ResponseMetadata')

            # Returns the template as a string value
            return(str(get_template))

        except Exception as e:
            logger.error('********** Template retrieval failed **********')
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
            logger.debug('********** Template updated **********')
            logger.debug(create_template)

            return 'Template update succeeded'

        except Exception as e:
            logger.error('********** Template update failed **********')
            logger.error(e)

            return 'Template update failed'


    elif event['mode'] == 'delete':
        # Deletes the template using the provided name
        try:
            template_delete = ses_client.delete_email_template(
                TemplateName = event['template_name']
            )
            logger.debug('********** Template deleted **********')
            logger.debug(template_delete)

            return event['template_name'] + ' template deleted.'

        except Exception as e:
            logger.error('********** Template failed to delete **********')
            logger.error(e)
            return 'Template delete failed'
