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
1.  Log into the [AWS console](https://console.aws.amazon.com/console/home). Be sure to set your region to match the region you have deployed Amazon Connect to, then return here.
1.  Select the link below that matches your region to launch the template:
    - us-east-1 [<img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png">](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=VMX3&templateURL=https://connectbd-sc-us-east-1.s3.us-east-1.amazonaws.com/vmx3/2024.06.01/cloudformation/vmx3.yaml)
    - us-west-2 [<img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png">](https://console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/new?stackName=VMX3&templateURL=https://connectbd-sc-us-west-2.s3.us-west-2.amazonaws.com/vmx3/2024.06.01/cloudformation/vmx3.yaml)
    - af-south-1 [<img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png">](https://console.aws.amazon.com/cloudformation/home?region=af-south-1#/stacks/new?stackName=VMX3&templateURL=https://connectbd-sc-af-south-1.s3.af-south-1.amazonaws.com/vmx3/2024.06.01/cloudformation/vmx3.yaml)
    - ap-southeast-1 [<img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png">](https://console.aws.amazon.com/cloudformation/home?region=ap-southeast-1#/stacks/new?stackName=VMX3&templateURL=https://connectbd-sc-ap-southeast-1.s3.ap-southeast-1.amazonaws.com/vmx3/2024.06.01/cloudformation/vmx3.yaml)
    - ap-southeast-2 [<img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png">](https://console.aws.amazon.com/cloudformation/home?region=ap-southeast-2#/stacks/new?stackName=VMX3&templateURL=https://connectbd-sc-ap-southeast-2.s3.ap-southeast-2.amazonaws.com/vmx3/2024.06.01/cloudformation/vmx3.yaml)
    - ap-northeast-1 [<img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png">](https://console.aws.amazon.com/cloudformation/home?region=ap-northeast-1#/stacks/new?stackName=VMX3&templateURL=https://connectbd-sc-ap-northeast-1.s3.ap-northeast-1.amazonaws.com/vmx3/2024.06.01/cloudformation/vmx3.yaml)
    - ap-northeast-2 [<img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png">](https://console.aws.amazon.com/cloudformation/home?region=ap-northeast-2#/stacks/new?stackName=VMX3&templateURL=https://connectbd-sc-ap-northeast-2.s3.ap-northeast-2.amazonaws.com/vmx3/2024.06.01/cloudformation/vmx3.yaml)
    - ca-central-1 [<img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png">](https://console.aws.amazon.com/cloudformation/home?region=ca-central-1#/stacks/new?stackName=VMX3&templateURL=https://connectbd-sc-ca-central-1.s3.ca-central-1.amazonaws.com/vmx3/2024.06.01/cloudformation/vmx3.yaml)
    - eu-central-1 [<img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png">](https://console.aws.amazon.com/cloudformation/home?region=eu-central-1#/stacks/new?stackName=VMX3&templateURL=https://connectbd-sc-eu-central-1.s3.eu-central-1.amazonaws.com/vmx3/2024.06.01/cloudformation/vmx3.yaml)
    - eu-west-2 [<img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png">](https://console.aws.amazon.com/cloudformation/home?region=eu-west-2#/stacks/new?stackName=VMX3&templateURL=https://connectbd-sc-eu-west-2.s3.eu-west-2.amazonaws.com/vmx3/2024.06.01/cloudformation/vmx3.yaml)
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

## Test Voicemail
Now that the Voicemail Express has been deployed, you are ready to test.
1.  **Dial** the phone number you configured for the Voicemail Test Line
1.  At the next menu, **press 1** to leave a voicemail for an agent or **press 2** to leave a voicemail for a queue
1.  When you hear the tone, **record your voicemail**. Hang up at any time after recording a message.
    - **NOTE:** If you have just enabled KVS on your instance for the first time, you may hear an error message. Simply hang up and try again. It should work the second time. KVS streams are not created until first use, which will throw an error in your contact flow.
1.  Once you have completed the recording, **wait approximately 2 minutes**.
1.  Log the appropriate agent in and put them into the available state. The Task should arrive shortly.

**Voicemail Validation is complete!**