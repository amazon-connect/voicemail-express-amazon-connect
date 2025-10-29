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

def genai_summarizer(function_payload):

    # Debug lines for troubleshooting
    logger.debug('********** Beginning Sub: GenAI Summarizer **********')
    logger.debug(function_payload)

    # Establish empty container
    sub_response = {} # for the response

    # 1. Extract the transcript and set the parameters for the Generative AI Summarization
    # Extract transcript
    vmx3_transcript = function_payload['vmx3_transcript_contents']

    # Establish Client and set model parameters
    nova_model = os.environ['inference_model']
    inference_region = os.environ['inference_region']
    bedrock = boto3.client('bedrock-runtime',inference_region)

    summary_prompt = 'You summarize voicemail messages left by callers. You are provided with a transcript of the voicemail. Read the transcript and summarize the content into 4-5 sentences at most. Begin the summary with who the caller is, if that can be determined from the message. Also, make sure to provide the callback number, if left in the voicemail. Your summary will not be read by customers. Be as concise as possible while still clearly articulating the key topic of the message. Your entire response should never exceed 500 characters. Here is the transcript of the voicemail: '

    conversation = [
        {
            'role': 'user',
            'content': [
                {
                    'text': summary_prompt
                },
                {
                    'text': vmx3_transcript
                }
            ],
        }
    ]

    nova_config = {
        'temperature': 0.5,
        'topP': 0.9
    }
    logger.debug('********** Sub: GenAI Summarizer Step 1 of 2 complete **********')

    # 2. Send the summarization request
    # Send the request
    try:
        summarization_response = bedrock.converse(
            modelId=nova_model,
            messages=conversation,
            inferenceConfig=nova_config
        )
        logger.debug(summarization_response)
        logger.debug('********** Summarization complete **********')
    
    except Exception as e:
        logger.error('********** Record Result: Failed to generate GenAI summary **********')
        logger.error(e)
        raise Exception
    
    # Send the result
    sub_response.update({'vmx3_genai_summary':summarization_response['output']['message']['content'][0]['text']})
    logger.debug('********** Sub: GenAI Summarizer Step 2 of 2 complete **********')

    return sub_response