# Voicemail Express V3
Voicemail Express is designed to provide basic voicemail functionality to Amazon Connect. It has been designed to work seamlessly behind the scenes, providing voicemail options for all agents and queues by default. It is an evolution of the Voicemail Express solution that was created specifically for Service Cloud Voice customers by the AWS team that worked with Salesforce to develop Service Cloud Voice. That solution has been cloned and included with Service Cloud Voice, and is now used at scale by customers on that offering. This version removes the Salesforce-centric options, providing the same easy-to-deploy-and-use voicemail option for standard Amazon Connect customers. Typically speaking, Voicemail Express can be deployed and validated in less than 15 minutes. 

![Voicemail Express Architecture](Docs/Img/VMX3.png)

## What's new in VMX3 (2024.08.01)
-  **Code Simplification:** Rewrote the last remaining JavaScript AWS Lambda function in Python 3.12, completing the migration of the Lambda code to Python. This also allowed us to remove the Node common layer for Lambda.
-  **Kinesis Video Stream Process improvements:** Updated the KVStoS3 Lambda function to use the GetMediaForFragmentList API for Kinesis Video Streams Archived Media to extract the audio from KVS. This greatly improves the speed and stability of the Lambda function, especially in environments with a high KVS load or long retention rate.
-  **Improved Logging:** Adopted native AWS Lambda logging in all functions, allowing for better control over logging sensitivity. Also improved the logging elements in code to provide better logging for troubleshooting. Also improved error handling in all functions
-  **Performance Validation:** Load tested 1,000s of voicemails in an environment that included >400 concurrent connections, all with KVS streaming enabled to validate performance.
-  **Documentation Improvements:** Improved existing documentation with additional clarity and test steps. Also created new documents to as described below:
   -  [Getting Support](Docs/vmx_support.md) details how to get support for Voicemail Express and what the limitations are. 
   -  [Changelog](Docs/vmx_changelog.md) provides high level changelog information

## How it works
With Voicemail Express, customers can have the option to leave a voicemail for an individual agent or an Amazon Connect Queue. Once the voicemail is recorded, a series of processes take place in the following order:
1. Voicemail recording is extracted and stored in S3 as a .wav file
1. The recording is transcribed using Amazon Transcribe
1. A presigned URL is geenrated that provides access to the voicemail recording without the need for further authentication
1. The voicemail is packaged for delivery, including the transcription, presigned URL, and contact data. It is then delivered as an Amazon Connect Task or via email using Amazon Simple Email Service (SES), depending on your configuration.

Voicemails are configured for a retention period of up to 7 days. After 7 days, the recordings are the presigned URL is no longer valid, and the recordings are lifecycled. During deployment, you have the option to configure the lifecycle window, if desired. Additionally, you have the option to keep, archive, or delete voicemail recordings. 

## Deyployment and Management
### How to deploy
To deploy Voicemail Express, you will need to complete the following:
1. Complete the [Voicemail Express Prerequisites](Docs/vmx_prerequistes.md)
1. Complete the [Voicemail Express Installation](Docs/vmx_installation_instructions.md)

### How to upgrade
To upgrade Voicemail Express, follow the [Upgrade Your Installation](Docs/vmx_upgrade.md) instructions.

### How to uninstall
To remove Voicemail Express follow the instructions below:
1.  [Removing/Uninstalling Voicemail Express](Docs/vmx_uninstall.md)

## Using Voicemail Express
Once Voicemail Express has been deployed, you can learn more about it by reading the [High-level overview of the Voicemail Express solution](Docs/vmx_core.md). 

If your primary delivery model is Amazon Connect Tasks, you can learn more about that model [here](Docs/vmx_tasks.md). 

If your deployment model is email, you can learn more about that model [here](Docs/vmx_email.md).

Basic troubleshooting steps can be found on the [Troubleshooting Common Voicemail Issues](Docs/vmx_troubleshooting.md) page.

You can also read about the available [support options](Docs/vmx_support.md).

Finally, a list of recent changes be found on the [Changelog](Docs/vmx_changelog.md) page.

## Roadmap
The following items are currently planned for future releases. Changes to roadmap depend on feedback, however one overarching tenet of Vociemail Express is to keep the solution lightweight, with a minimal number of required services and administration, and to replace functionality with native Amazon Connect features as soon as they become available. 
-  **Jul-Sep 2024**
   -  Update KVStoS3 function to Python **Delivered**
   -  Example flows
   -  Notification Option
   -  GenAI summary option
   -  Lambda VPC Option
-  **Sep-Dec 2024**
   -  Optional delivery mode add-ins: Allows you to add additional delivery modes as desired. The next batch of delivery modes will be:
      -  Salesforce Case
      -  Salesforce custom objects
   -  Reduce layer size for default deployments **Delivered**
   -  Reduce complexity and number of functions
   -  Support for GitHub sync

**Current Published Version:** 2024.08.01
Current published version is the version of the code and templates that has been deployed to our S3 buckets