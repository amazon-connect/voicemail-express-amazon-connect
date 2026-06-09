# Voicemail Email Delivery with .wav File Attachment

## Overview
This modification changes the email delivery mode to attach the voicemail recording as a .wav file directly to the email, instead of including a presigned S3 URL link. This ensures agents can always access the recording regardless of URL expiration.

## What Changed

### 1. Modified File: `Code/sub_ses_email.py`

**Before:** Used SES template-based `send_email` with a presigned URL link in the email body.

**After:** Uses SES raw email (`send_email` with `Raw` content) to construct a MIME multipart message with the .wav file attached.

Key changes:
- Added `email.mime` imports for building MIME messages
- Added S3 client to download the recording
- Builds HTML email body inline (no longer uses SES templates)
- Attaches the .wav file as `audio/wav`
- Sends via SES raw email API

### 2. IAM Policy Update

The Lambda execution role (`VMX3_Packager_Role_<instance>`) needs `ses:SendRawEmail` permission added to its SES policy statement.

**Before:**
```json
{
    "Action": [
        "ses:SendEmail",
        "ses:SendTemplatedEmail"
    ],
    "Resource": "*",
    "Effect": "Allow"
}
```

**After:**
```json
{
    "Action": [
        "ses:SendEmail",
        "ses:SendTemplatedEmail",
        "ses:SendRawEmail"
    ],
    "Resource": "*",
    "Effect": "Allow"
}
```

## Modified Code

```python
current_version = '2025.09.13-modified'

# Import required modules
import boto3
import json
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

logger = logging.getLogger()

def vmx3_to_ses_email(function_payload):

    logger.debug('********** Beginning Sub: Voicemail Email Delivery (with attachment) **********')
    logger.debug(function_payload)

    function_response = {}

    # 1. Establish clients
    try:
        ses_client = boto3.client('sesv2')
        s3_client = boto3.client('s3')
        logger.debug('********** Clients initialized **********')
    except Exception as e:
        logger.error('********** VMX Initialization Error: Could not establish needed clients **********')
        logger.error(e)
        raise Exception

    email_working_data = function_payload['vmx_data']
    logger.debug('********** Sub: Voicemail Email Delivery Step 1 of 4 Complete **********')

    # 2. Resolve FROM/TO addresses
    if 'vmx3_email_from' in email_working_data:
        if email_working_data['vmx3_email_from']:
            vmx3_email_from_address = email_working_data['vmx3_email_from']
    else:
        vmx3_email_from_address = os.environ['default_email_from']

    if 'vmx3_email_to' in email_working_data:
        if email_working_data['vmx3_email_to']:
            vmx3_email_target_address = email_working_data['vmx3_email_to']
    else:
        vmx3_email_target_address = os.environ['default_email_target']

    if '@' not in vmx3_email_target_address:
        vmx3_email_target_address = os.environ['default_email_target']

    # Truncate transcript if needed
    vmx3_transcript = email_working_data['vmx3_transcript_contents']
    if len(vmx3_transcript) > 2048:
        vmx3_short_transcript = vmx3_transcript[:2048] + ' ...(truncated)'
    else:
        vmx3_short_transcript = vmx3_transcript

    logger.debug('********** Sub: Voicemail Email Delivery Step 2 of 4 Complete **********')

    # 3. Download .wav from S3
    try:
        recording_bucket = function_payload['function_data']['recording_bucket']
        recording_key = function_payload['function_data']['recording_key']

        recording_obj = s3_client.get_object(Bucket=recording_bucket, Key=recording_key)
        audio_data = recording_obj['Body'].read()

        recording_filename = recording_key.rsplit('/', 1)[-1] if '/' in recording_key else recording_key
        logger.debug('********** Recording downloaded from S3: ' + recording_key + ' **********')
        logger.debug('********** Sub: Voicemail Email Delivery Step 3 of 4 Complete **********')
    except Exception as e:
        logger.error('********** Failed to download recording from S3 **********')
        logger.error(e)
        raise Exception

    # 4. Build MIME email with attachment and send
    try:
        msg = MIMEMultipart('mixed')
        msg['Subject'] = 'Amazon Connect Voicemail from ' + email_working_data.get('vmx3_from', 'Unknown')
        msg['From'] = vmx3_email_from_address
        msg['To'] = vmx3_email_target_address

        # HTML body
        genai_summary = email_working_data.get('vmx3_genai_summary', 'Not enabled')
        queue_name = email_working_data.get('vmx3_queue_name', 'Unknown')
        caller_number = email_working_data.get('vmx3_from', 'Unknown')
        datetime_received = email_working_data.get('vmx3_datetime', 'Unknown')

        html_body = (
            '<div style="width:100%; height:80px; background-color:#415266; display:flex; '
            'align-items:center; padding-left:15px; font-family:sans-serif;">'
            '<h2 style="color:white; margin-left:10px;">Amazon Connect Voicemail</h2></div>'
            '<div style="font-family:sans-serif; padding:15px;">'
            '<p><strong>From:</strong> ' + caller_number + '</p>'
            '<p><strong>Queue:</strong> ' + queue_name + '</p>'
            '<p><strong>Date/Time:</strong> ' + datetime_received + '</p>'
            '<h3>GenAI Summary:</h3><p>' + genai_summary + '</p>'
            '<h3>Transcript:</h3><p>' + vmx3_short_transcript + '</p>'
            '<p><em>The voicemail recording is attached as a .wav file.</em></p>'
            '</div>'
        )

        body_part = MIMEText(html_body, 'html')
        msg.attach(body_part)

        # Attach .wav
        attachment = MIMEApplication(audio_data)
        attachment.add_header('Content-Disposition', 'attachment', filename=recording_filename)
        attachment.add_header('Content-Type', 'audio/wav')
        msg.attach(attachment)

        # Send raw email
        send_email = ses_client.send_email(
            Content={
                'Raw': {
                    'Data': msg.as_string()
                }
            }
        )

        logger.debug('********** Email with attachment sent **********')
        logger.debug('********** Sub: Voicemail Email Delivery Step 4 of 4 Complete **********')

        function_response.update({'result':'success','email': send_email})
        return function_response

    except Exception as e:
        logger.error('********** Failed to send email with attachment **********')
        logger.error(e)
        raise Exception
```

## Deployment Steps

1. Download the current Packager Lambda code package
2. Replace `sub_ses_email.py` with the modified version above
3. Re-zip and upload to the Lambda function (`VMX3-Packager-<instance>`)
4. Add `ses:SendRawEmail` to the Packager role's IAM policy

## Considerations

- SES has a 40MB raw message size limit — most voicemails are well under this
- Lambda has 128MB default memory — for very long recordings, you may need to increase Lambda memory
- SES templates are no longer used for email delivery — the HTML body is built in code
- This does not affect Task or Guided Task delivery modes
- The presigned URL is still generated (by the packager flow) but is no longer included in the email body
