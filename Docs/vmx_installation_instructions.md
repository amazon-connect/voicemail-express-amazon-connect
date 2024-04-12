# Installing Voicemail Express
This document will walk you through the steps required to deploy the Voicemail Express in your AWS account. 

In order to deploy this template, you must first complete the [installation prerequisites](vmx_prerequistes.md). Once those are complete, you can continue with the process below.

## Gather Required Information
Voicemail Express is deployed via AWS CloudFormation. In order to launch the template, you will need the following information:
- ARN for the Amazon Kinesis data stream used for streaming your CTRs from the [Amazon Kinesis Data streams console](https://console.aws.amazon.com/kinesis/home)
  - **IMPORTANT NOTE:** This solution is designed to receive CTRs via Kinesis Data Streams only, not Kinesis Firehose. It WILL NOT work with a Kinesis firehose.
- Amazon Connect Instance Alias from the [Amazon Connect console](https://console.aws.amazon.com/connect/home)
- Amazon Connect Instance ARN from the [Amazon Connect console](https://console.aws.amazon.com/connect/home)
- Default agent ID to use for testing
- Default queue ARN to use for testing

Once you have the required information, you are ready to continue with the deployment.

## Delploy the Cloudformation Template
The next step is to deploy the CloudFormation template. This template builds all of the AWS resources required to make Voicemail Express work.
1.  Open this link in a new tab: [Voicemail Express CloudFormation template](../CloudFormation/vmx3.yaml). In the new tab right-click/control-click the **raw** button and save the template locally.
1.  Log into the [AWS console](https://console.aws.amazon.com/console/home)
1.  Navigate to the [AWS CloudFormation console](https://console.aws.amazon.com/cloudformation/home)
1.  Choose **Create stack**
1.  In the **Specify template** section, select **Upload a Template file**
1.  Select **Choose file**
1.  Navigate to the **vmx3.yaml** file that you downloaded previously and choose **Open**
1.  Wait a moment for the S3 URL to update, then select **Next**
1.  Provide a name for the stack, such as `VMX-MyInstanceName`
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

## Test Voicemail
Now that the Voicemail Express has been deployed, you are ready to test.
1.  **Dial** the phone number you configured for the Voicemail Test Line
1.  At the next menu, **press 1** to leave a voicemail for an agent or **press 2** to leave a voicemail for a queue
1.  When you hear the tone, **record your voicemail**. Hang up at any time after recording a message.
    - **NOTE:** If you have just enabled KVS on your instance for the first time, you may hear an error message. Simply hang up and try again. It should work the second time. KVS streams are not created until first use, which will throw an error in your contact flow.
1.  Once you have completed the recording, **wait approximately 2 minutes**.
1.  Log the appropriate agent in and put them into the available state. The Task should arrive shortly.

**Voicemail Validation is complete!**