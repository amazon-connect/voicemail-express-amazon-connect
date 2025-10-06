# Installing Voicemail Express
This document will walk you through the steps required to deploy the Voicemail Express in your AWS account. 

In order to deploy this template, you must first complete the [installation prerequisites](vmx_prerequistes.md). Once those are complete, you can continue with the process below.

## Gather Required Information (All deployments)
Voicemail Express is deployed via AWS CloudFormation. In order to launch the template, you will need the following information:
-  ARN for the Amazon Kinesis data stream used for streaming your CTRs from the [Amazon Kinesis Data streams console](https://console.aws.amazon.com/kinesis/home)

> [!Important] 
> This solution is designed to receive CTRs via Kinesis Data Streams only, not Kinesis Firehose. It WILL NOT work with a Kinesis firehose.

-  Amazon Connect Instance Alias from the [Amazon Connect console](https://console.aws.amazon.com/connect/home)
-  Amazon Connect Instance ARN from the [Amazon Connect console](https://console.aws.amazon.com/connect/home)
-  Amazon Connect Call Recordings bucket ARN
-  Default agent ID to use for testing
-  Default queue ARN to use for testing

## Gather Required Information (Email deployments **ONLY**)
-  Default FROM email address. This will be the default address used to send emails FROM if no other address is configured or provided.
-  Default TO email address. This will be the default address used to send emails TO if no other address is configured or provided. 

Once you have the required information, you are ready to continue with the deployment.

## Delploy the Cloudformation Template
The next step is to deploy the CloudFormation template. This template builds all of the AWS resources required to make Voicemail Express work.
1.  Open a new browser tab and then log into the [AWS console](https://console.aws.amazon.com/console/home). Be sure to set your region to match the region you have deployed Amazon Connect to, then return here.
1.  Select the link below that matches your region to launch the template:
    - us-east-1 [<img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png">](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=VMX3&templateURL=https://vmx-source-us-east-1.s3.us-east-1.amazonaws.com/vmx3/2025.09.12/cloudformation/vmx3.yaml)
    - us-west-2 [<img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png">](https://console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/new?stackName=VMX3&templateURL=https://vmx-source-us-west-2.s3.us-west-2.amazonaws.com/vmx3/2025.09.12/cloudformation/vmx3.yaml)
    - af-south-1 [<img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png">](https://console.aws.amazon.com/cloudformation/home?region=af-south-1#/stacks/new?stackName=VMX3&templateURL=https://vmx-source-af-south-1.s3.af-south-1.amazonaws.com/vmx3/2025.09.12/cloudformation/vmx3.yaml)
    - ap-southeast-1 [<img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png">](https://console.aws.amazon.com/cloudformation/home?region=ap-southeast-1#/stacks/new?stackName=VMX3&templateURL=https://vmx-source-ap-southeast-1.s3.ap-southeast-1.amazonaws.com/vmx3/2025.09.12/cloudformation/vmx3.yaml)
    - ap-southeast-2 [<img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png">](https://console.aws.amazon.com/cloudformation/home?region=ap-southeast-2#/stacks/new?stackName=VMX3&templateURL=https://vmx-source-ap-southeast-2.s3.ap-southeast-2.amazonaws.com/vmx3/2025.09.12/cloudformation/vmx3.yaml)
    - ap-northeast-1 [<img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png">](https://console.aws.amazon.com/cloudformation/home?region=ap-northeast-1#/stacks/new?stackName=VMX3&templateURL=https://vmx-source-ap-northeast-1.s3.ap-northeast-1.amazonaws.com/vmx3/2025.09.12/cloudformation/vmx3.yaml)
    - ap-northeast-2 [<img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png">](https://console.aws.amazon.com/cloudformation/home?region=ap-northeast-2#/stacks/new?stackName=VMX3&templateURL=https://vmx-source-ap-northeast-2.s3.ap-northeast-2.amazonaws.com/vmx3/2025.09.12/cloudformation/vmx3.yaml)
    - ca-central-1 [<img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png">](https://console.aws.amazon.com/cloudformation/home?region=ca-central-1#/stacks/new?stackName=VMX3&templateURL=https://vmx-source-ca-central-1.s3.ca-central-1.amazonaws.com/vmx3/2025.09.12/cloudformation/vmx3.yaml)
    - eu-central-1 [<img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png">](https://console.aws.amazon.com/cloudformation/home?region=eu-central-1#/stacks/new?stackName=VMX3&templateURL=https://vmx-source-eu-central-1.s3.eu-central-1.amazonaws.com/vmx3/2025.09.12/cloudformation/vmx3.yaml)
    - eu-west-2 [<img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png">](https://console.aws.amazon.com/cloudformation/home?region=eu-west-2#/stacks/new?stackName=VMX3&templateURL=https://vmx-source-eu-west-2.s3.eu-west-2.amazonaws.com/vmx3/2025.09.12/cloudformation/vmx3.yaml)
> [!IMPORTANT]
> For GovCloud deployments, please follow the [GovCloud Deployment Instructions](/Docs/vmx_govcloud_deployments.md).
1.  Verify that the **Amazon S3 URL** is for the same region you are deploying to, then select **Next**
1.  Update the stack name to include your instance alias, for example such as `VMX3-MyInstanceName`
1.  **Complete the parameters** using the information that you have gathered.
1.  Once the parameters are complete, choose **Next**
1. 	Scroll to the bottom and select **Next**
1. 	Scroll to the bottom, select the boxes to **acknowledge that IAM resources will be created**
1.  Select **Submit**
1.  The deployment will take 3-5 minutes. During this time, multiple nested stacks will be deployed. Once the main stack shows **CREATE_COMPLETE**, you are ready to proceed.

## Assign a test number
1.  Login to the Amazon Connect administration interface
1.  Select **Channels** from the navigation menu, then choose **Phone numbers**
1.  Either select an existing number, or claim a new number
1.  Set the contact flow for the number to **VMX3-AWSTestFlow-YOURINSTANCE**.
1.  Select **Save**

## Test Voicemail Delivery as an Amazon Connect Guided Task
If you have deployed Voicemail Express with the Amazon Connect Guided Tasks delivery option, you can validate functionality by performing the following test.
1.  **Dial** the phone number you configured for the Voicemail Test Line.
1.  At the first menu, **press 2** to select Task delivery.
1.  At the next menu, **press 1** to leave a voicemail for an agent or **press 2** to leave a voicemail for a queue.
1.  Select the appropiate option to enable the generative AI summary, if desired.
1.  When you hear the tone, **record your voicemail**. Hang up at any time after recording a message.
1.  Once you have completed the recording, **wait approximately 2 minutes**.
1.  Log the appropriate agent in **to the agent workspace or a custom CCP with guides enabled** and put them into the available state. The Guided Task should arrive shortly.

## Test Voicemail Delivery as an Amazon Connect Task
If you have deployed Voicemail Express with the Amazon Connect Tasks delivery option, you can validate functionality by performing the following test.
1.  **Dial** the phone number you configured for the Voicemail Test Line.
1.  At the first menu, **press 1** to select Task delivery.
1.  At the next menu, **press 1** to leave a voicemail for an agent or **press 2** to leave a voicemail for a queue.
1.  Select the appropiate option to enable the generative AI summary, if desired.
1.  When you hear the tone, **record your voicemail**. Hang up at any time after recording a message.
1.  Once you have completed the recording, **wait approximately 2 minutes**.
1.  Log the appropriate agent in and put them into the available state. The Task should arrive shortly.

## Test Voicemail Delivery as an Email using Amazon Simple Email Service (SES)
If you have deployed Voicemail Express with the email delivery option, you can validate functionality by performing the following test.
1.  **Dial** the phone number you configured for the Voicemail Test Line.
1.  At the first menu, **press 3** to select email delivery.
1.  At the next menu, **press 1** to leave a voicemail for an agent or **press 2** to leave a voicemail for a queue.
1.  Select the appropiate option to enable the generative AI summary, if desired.
1.  When you hear the tone, **record your voicemail**. Hang up at any time after recording a message.
1.  Once you have completed the recording, **wait approximately 2 minutes**.
1.  Access the appropriate email box to verify delivery of the voicemail.

## Test Voicemail Delivery as an Amazon Connect Task with the In Queue Voicemail
If you have deployed Voicemail Express with the Amazon Connect Tasks delivery option, you can validate the In-Queue experience by performing the following test.
1.  **Dial** the phone number you configured for the Voicemail Test Line.
1.  At the first menu, **press 4** to select Task delivery.
1.  At the next menu, **press 1** to leave a voicemail.
1.  Select the appropiate option to enable the generative AI summary, if desired.
1.  When you hear the tone, **record your voicemail**. Hang up at any time after recording a message.
1.  Once you have completed the recording, **wait approximately 2 minutes**.
1.  Log the appropriate agent in and put them into the available state. The Task should arrive shortly.

**Voicemail Validation is complete!**