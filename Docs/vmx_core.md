# High-level overview of Voicemail Express
Voicemail Express provides basic voicemail functionality for Amazon Connect Customers. It has been designed to be easy to deploy and maintain. As such, there is a limited feature stack, and few administrative options, however all of the code is open and customizable to fit different customer needs. This page will provide a foundational understanding of how it works.

## High-Level Flow
Voicemails are captured in the Amazon Connect contact flow, processed post-call, and delivered as Amazon Connect Tasks or as emails (depending on your configuration). Here is a quick overview of the basic steps in the process:
1.  Customer calls in, is provided the option to leave a voicemail (for whatever reason), and decides to do so.
1.  Specific contact attributes are set to mark the contact as having a voicemail
1.  An Amazon Kinesis Video Stream (KVS) is initialized to record the audio from the customer
1.  Customer completes the message and ends the call
1.  A contact trace record (CTR) is emitted for the contact via Amazon Kinesis Data Stream
1.  That CTR triggers the VMX3KVStoS3 AWS Lambda function. This function:
    1.  Identifies that the contact is a voicemail
    1.  Retrieves some key data about the contact
    1.  Extracts the voicemail recording from the KVS stream
    1.  Writes the voicemail recording to an Amazon Simple Storage Service (S3) bucket, using the extracted data as metadata
1.  The creation of the recording object in S3 triggers the next Lambda function, VMX3Transcriber. This function:
    1.  Retrieves the recording file from S3
    1.  Uses the metadata to create a new transcription job
    1.  The transcription job writes the completed transcription to a different S3 bucket
1.  The creation of the transcription object in S3 triggers the next Lambda function, VMX3Packager. This function:
    1.  Retrieves the transcript file from S3
    1.  Uses the data in the transcript file identify the contact and find the recording
    1.  Retrieves the metadata from the recording file
    1.  Invokes the VMX3-Presigner function to generate a presigned URL for the recording
    1.  Determines queue/agent information, destination, etc
    1.  Invokes the sub-function for the delivery mode
    1.  Once delivery is successful, it deletes the existing transcription job
    1.  Finally, the contact attributes are updated to remove the voicemail flag so future instances of this CTR do not generate new voicemails.

## Required Contact Attributes
In order for the voicemail system to work, contacts must have certain contact attributes set. The following attributes are used:
-  **vmx3_flag (Required)**: (0,1) this attribute flags the call as requiring processing by the Voicemail Express. All new voicemails should have this value set to `1`. When the packager function completes, it will update the value to `0`. If this value is set to anything other than `1` or is missing altogether, the voicemail system will ignore the CTR and voicemail processing WILL NOT HAPPEN.
    -  Example: 'vmx3_flag':'1'
-  **vmx3_from (Required)**: (customer phone in E.164 format) this attribute indicates the phone number of the customer. This should be set using the System attribute of `Customer number` ($.CustomerEndpoint.Address) or set this to a phone number provided by the customer. It should always be in E.164 format.
    -  Example: 'vmx3_from':'+15555551212'
-  **vmx3_queue_arn (Required)**: (ARN) the Amazon Resource Number of the queue that this voicemail should belong to. In most cases, it makes most practical sense to first set the appropriate queue as the working queue, then to set this attribute using the System attribute of `Queue ARN` ($.Queue.ARN). This is critical as the Lambda functions use the queue ARN to determine the target queue, instance ID, queue mode (agent vs queue), etc.
    -  Example: 'vmx3_queue_arn':'arn:aws:connect:us-east-1:YOURACCOUNTNUMBER:instance/YOURINSTANCEID/queue/YOURQUEUEID'
-  **vmx3_lang (Required)**: (Language code) the language code that Amazon Transcribe should use when transcribing the call. The list of supported languages and their language codes can be found in the [Amazon Transcribe Developer Guide](https://docs.aws.amazon.com/transcribe/latest/dg/supported-languages.html). **DEFAULT: en-US**
    -  Example: 'vmx3_lang':'en-US'
-  **vmx3_mode (Required)**: (task) which delivery mode should be used for this voicemail. In this version of Voicemail Express, all voicemails are delivered as Amazon Connect Tasks. If nothing is provided, the voicemail will be delivered via the default mode selected during implementation. Options: `email, task, guided_task` **DEFAULT: guided_task**
    -  Example: 'vmx3_mode':'task'

### When to set the voicemail contact attributes
The voicemail system was designed to allow customers to interact with it as they would most other voicemail systems, allowing them to simply hang up when they have left their message instead of waiting for a tone or message. As such, it is best to set these attributes just before you begin recording the customer voice. You should not, however, set them too early as the customer could change their mind and just hang up before leaving a message, leading to errors in code execution. Technically speaking, the only attribute that should not be set until the customer is getting ready to record is the `vmx3_flag` attribute, since it is the key that triggers the entire voicemail process. The example contact flow provided with the installation, VMXCoreFlow-InstanceName, shows the `vmx3_flag` attribute being set just after media streaming begins, with the other attributes being set in a prior flow.

## Recording the customer audio
Voicemail Express uses the Kinesis Video Streams integration of Amazon Connect to capture the customer audio. Since we are trying to capture the customer audio for a voicemail, when no other parties should be on the phone, we are only expecting audio from the customer in the stream. When configuring your contact flow, please follow the example provided in VMX3CoreFlow-InstanceName and **only initialize** the audio `From the customer`. If you select only `To the customer`, you will not get the customer's voicemail at all. If you select both options, the audio will be garbled.

## Setting the max voicemail time
By default, the max voicemail length is 1 minute. If you want to increase or decrease this, you will need to change the timeout on the **Get customer input** block in the VMX3-CoreFlowModule-InstanceName contact flow (or whichever custom flow you are using to capture voicemails). If you are INCREASING this number, you may also want to edit the Kinesis trigger on your VMX3-KVStoS3 function, reducing the batch size. This is important because the audio capture from KVS does take a little bit of time and since all Lambda functions have a 15 minute timeout, you could run into an issue.

## Additional Notes
1.  **Calls in Queue**: If you are providing the voicemail option after you have already queued the call, be aware that the voicemail process can be completely interrupted if an agent in the assigned queue becomes available. While connecting a caller to an agent is not a bad thing, there are a few things to consider:
    1.  The caller will suddenly switch from leaving a voicemail to hearing a whisper flow (if configured), then connect to an agent. They may not understand what is happening and hang up.
    1.  If the call connects while the customer was leaving the voicemail, the CTR still likely contains the `vmx3_flag` setting to 1. This means that Voicemail Express will still do the voicemail process and, most likely, will transcribe the entire conversation from the customer's perspective. To correct this, part of the customer or agent whisper should be to check for the presence of the flag and, if it exists, set it to 0, then stop KVS streaming.
1.  **Voicemail Delivery Time**: The voicemail process is triggered by CTR generation. Until the CTR is sent out of the Kinesis stream, there is no processing. This is critical to understand for a few reasons:
    1.  If you are encountering an error on the phone, during testing, that causes the contact flow to end or streaming to fail for some reason, the issue is not with the voicemail Lambda functions or configuration, it has to do with contact flows or KVS setup. For voicemail specifically, no Lambda functions are invoked while the call is in progress.
    1.  There can be a delay in Contact Trace Record creation. This can vary from a few seconds up to a couple minutes. This, in turn, means that delivery of voicemail can be delayed as well. This expectation should be set with users. For delivery via email, you will also have the added time for email routing and delivery.