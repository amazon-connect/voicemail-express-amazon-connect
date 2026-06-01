current_version = '2025.09.14'
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
import html
import json
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Establish logging configuration
logger = logging.getLogger()

# WAV file magic bytes (RIFF header)
WAV_MAGIC_BYTES = b'RIFF'
WAV_FORMAT_MARKER = b'WAVE'


def _mask_pii(value, visible_chars=4):
    """Mask PII values, showing only the last few characters."""
    if not value or len(value) <= visible_chars:
        return '***'
    return '***' + value[-visible_chars:]


def _validate_email_domain(email_address):
    """Validate that the email target is in an allowed domain."""
    allowed_domains = os.environ.get('allowed_email_domains', '').split(',')
    allowed_domains = [d.strip().lower() for d in allowed_domains if d.strip()]

    if not allowed_domains:
        # If no allowlist configured, allow all (backward compatible)
        return True

    domain = email_address.split('@')[-1].lower()
    return domain in allowed_domains


def _validate_wav_file(audio_data):
    """Validate that the audio data has valid WAV file magic bytes."""
    if len(audio_data) < 12:
        return False
    # WAV files start with 'RIFF' and have 'WAVE' at offset 8
    return audio_data[:4] == WAV_MAGIC_BYTES and audio_data[8:12] == WAV_FORMAT_MARKER

def vmx3_to_ses_email(function_payload):

    # Debug lines for troubleshooting
    logger.debug('********** Beginning Sub: Voicemail Email Delivery (with attachment) **********')
    logger.debug('Payload keys: %s', list(function_payload.keys()))

    # Establish an empty container
    function_response = {}

    # 1. Establish clients and baseline data
    logger.debug('Beginning Voicemail to email')
    try:
        ses_client = boto3.client('sesv2')
        s3_client = boto3.client('s3')
        logger.debug('********** Clients initialized **********')
    
    except Exception as e:
        logger.error('********** VMX Initialization Error: Could not establish needed clients **********')
        logger.error(e)
        raise RuntimeError('Failed to initialize AWS clients') from e
    
    # Get baseline data
    email_working_data = function_payload['vmx_data']
    logger.debug('********** Base data initialized **********')
    logger.debug('********** Sub: Voicemail Email Delivery Step 1 of 4 Complete **********')

    # 2. Do mode and address checks. Pull in defaults where necessary
    # Identify the proper address to send the email FROM
    if 'vmx3_email_from' in email_working_data:
        if email_working_data['vmx3_email_from']:
            vmx3_email_from_address = email_working_data['vmx3_email_from']
    else:
        vmx3_email_from_address = os.environ['default_email_from']

    logger.debug('FROM ADDRESS: %s', _mask_pii(vmx3_email_from_address))

    # Identify the proper address to send the email TO
    if 'vmx3_email_to' in email_working_data:
        if email_working_data['vmx3_email_to']:
            vmx3_email_target_address = email_working_data['vmx3_email_to']
    else:
        vmx3_email_target_address = os.environ['default_email_target']

    if '@' in vmx3_email_target_address:
        logger.info('Valid email address format')
    else:
        vmx3_email_target_address = os.environ['default_email_target']

    # Validate email target against domain allowlist
    if not _validate_email_domain(vmx3_email_target_address):
        logger.error('Email target domain not in allowlist: %s', vmx3_email_target_address.split('@')[-1])
        raise RuntimeError('Email target domain not permitted by allowlist')

    logger.debug('TO ADDRESS: %s', _mask_pii(vmx3_email_target_address))

    # Make sure transcript fits in field and truncate if it does not.
    vmx3_transcript = email_working_data['vmx3_transcript_contents']
    if len(vmx3_transcript) > 2048:
        vmx3_short_transcript = vmx3_transcript[:2048] + ' ...(truncated)'
        logger.debug('********** Transcript truncated **********')
    else:
        logger.debug('********** Transcript within limits **********')
        vmx3_short_transcript = vmx3_transcript

    logger.debug('********** Sub: Voicemail Email Delivery Step 2 of 4 Complete **********')

    # 3. Download the .wav recording from S3
    try:
        recording_bucket = function_payload['function_data']['recording_bucket']
        recording_key = function_payload['function_data']['recording_key']
        
        recording_obj = s3_client.get_object(Bucket=recording_bucket, Key=recording_key)
        audio_data = recording_obj['Body'].read()
        
        # Validate WAV file magic bytes
        if not _validate_wav_file(audio_data):
            logger.error('********** S3 object is not a valid WAV file **********')
            raise RuntimeError('Downloaded file does not have valid WAV headers')

        # Extract filename from key
        recording_filename = recording_key.rsplit('/', 1)[-1] if '/' in recording_key else recording_key
        
        logger.debug('********** Recording downloaded from S3 (size: %d bytes) **********', len(audio_data))
        logger.debug('********** Sub: Voicemail Email Delivery Step 3 of 4 Complete **********')

    except RuntimeError:
        raise
    except Exception as e:
        logger.error('********** Failed to download recording from S3 **********')
        logger.error(e)
        raise RuntimeError('Failed to download recording from S3') from e

    # 4. Build MIME email with .wav attachment and send via SES raw email
    try:
        # Build the MIME message
        msg = MIMEMultipart('mixed')
        msg['Subject'] = 'Amazon Connect Voicemail from ' + html.escape(email_working_data.get('vmx3_from', 'Unknown'))
        msg['From'] = vmx3_email_from_address
        msg['To'] = vmx3_email_target_address

        # Sanitize all user-controlled variables before HTML insertion
        genai_summary = html.escape(email_working_data.get('vmx3_genai_summary', 'Not enabled'))
        queue_name = html.escape(email_working_data.get('vmx3_queue_name', 'Unknown'))
        caller_number = html.escape(email_working_data.get('vmx3_from', 'Unknown'))
        datetime_received = html.escape(email_working_data.get('vmx3_datetime', 'Unknown'))
        safe_transcript = html.escape(vmx3_short_transcript)

        html_body = (
            '<div style="width:100%; height:80px; background-color:#415266; display:flex; '
            'align-items:center; padding-left:15px; font-family:sans-serif;">'
            '<h2 style="color:white; margin-left:10px;">Amazon Connect Voicemail</h2></div>'
            '<div style="font-family:sans-serif; padding:15px;">'
            '<p><strong>From:</strong> ' + caller_number + '</p>'
            '<p><strong>Queue:</strong> ' + queue_name + '</p>'
            '<p><strong>Date/Time:</strong> ' + datetime_received + '</p>'
            '<h3>GenAI Summary:</h3><p>' + genai_summary + '</p>'
            '<h3>Transcript:</h3><p>' + safe_transcript + '</p>'
            '<p><em>The voicemail recording is attached as a .wav file.</em></p>'
            '</div>'
        )

        # Attach HTML body
        body_part = MIMEText(html_body, 'html')
        msg.attach(body_part)

        # Attach the .wav file
        attachment = MIMEApplication(audio_data)
        attachment.add_header('Content-Disposition', 'attachment', filename=recording_filename)
        attachment.add_header('Content-Type', 'audio/wav')
        msg.attach(attachment)

        # Send raw email via SES
        send_email = ses_client.send_email(
            Content={
                'Raw': {
                    'Data': msg.as_string()
                }
            }
        )

        logger.debug('********** Email with attachment sent **********')
        logger.debug('SES MessageId: %s', send_email.get('MessageId', 'N/A'))
        logger.debug('********** Sub: Voicemail Email Delivery Step 4 of 4 Complete **********')

        function_response.update({'result':'success','email': send_email})
        return function_response

    except Exception as e:
        logger.error('********** Failed to send email with attachment **********')
        logger.error(e)
        raise RuntimeError('Failed to send email with attachment') from e
