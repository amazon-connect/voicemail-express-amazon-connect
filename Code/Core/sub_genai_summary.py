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
import json
import boto3
import logging
import os

# Establish logging configuration
logger = logging.getLogger()

def genai_summarizer(event, context): 
    # Log incoming event
    logger.debug(event)

    # Extract transcript
    transcript = event['transcript_contents']

    # Establish Client and set model parameters
    nova_model = os.environ['inference_model']
    aws_region = os.environ['aws_region']
    bedrock = boto3.client('bedrock-runtime',aws_region)

    summary_prompt = 'You summarize voicemail messages left by callers. You are provided with a transcript of the voicemail. Read the transcript and summarize the content into 2-3 sentences if possible. Begin the summary with who the caller is, if that can be determined from the message. Also, make sure to provide the callback number, if left in the voicemail. Your summary will not be read by customers. Be as concise as possible while still clearly articulating the key points of the message. Provide the summary in the same language as the voicemail. Here is the transcript of the voicemail: ' 

    conversation = [
        {
            'role': 'user',
            'content': [
                {
                    'text': summary_prompt
                },
                {
                    'text': transcript
                }
            ],
        }
    ]

    nova_config = {
        'temperature': 0.5,
        'topP': 0.9
    }

    # Do the summarization
    try:
        summarization_response = bedrock.converse(
            modelId=nova_model,
            messages=conversation,
            inferenceConfig=nova_config
        )
        logger.debug(summarization_response)

        genai_summary = {'genai_summary':summarization_response['output']['message']['content'][0]['text']}
        logger.debug('********** Summarization complete **********')

        return genai_summary
    
    except Exception as e:
        logger.error('********** Record Result: Failed to generate GenAI summary **********')
        logger.error(e)
        raise Exception