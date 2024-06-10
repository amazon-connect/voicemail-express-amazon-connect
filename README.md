# Voicemail Express V3
Voicemail Express is designed to provide basic voicemail functionality to Amazon Connect. It has been designed to work seamlessly behind the scenes, providing voicemail options for all agents and queues by default. It is an evolution of the Voicemail Express solution that was created specifically for Service Cloud Voice customers by the AWS team that worked with Salesforce to develop Service Cloud Voice. That solution has been cloned and included with Service Cloud Voice, and is now used at scale by customers on that offering. This version removes the Salesforce-centric options, providing the same easy-to-deploy-and-use voicemail option for standard Amazon Connect customers. Typically speaking, Voicemail Express can be deployed and validated in less than 15 minutes. 

![Voicemail Express Architecture](Docs/Img/VMX3.png)

## What's new in VMX3 (2024.06.01)
-  Improved performance of the KVStoS3 function
-  Kinesis Data Stream filtering for records to reduce Lambda invocations
-  Added Voicemail date/time info to the task (based on work by [DanBloy](https://github.com/DanBloy))
-  Updated flow naming for consistency
-  Additional load testing completed

### How it works
With Voicemail Express, customers can have the option to leave a voicemail for an agent or queue. Once the voicemail is recorded, a series of processes take place in the following order:
1. Voicemail stored in S3 as a .wav file
2. Transcription of the voicemail
3. Presigned URL that provides access to the voicemail without the need for authentication into the AWS account hosting Amazon Connect.
4. Voicemail is packaged for delivery, including the transcription, presigned URL, and contact data. It is then delivered as an Amazon Connect Task.

Voicemails are configured for a retention period of up to 7 days. After 7 days, the recordings are the presigned URL is no longer valid, and the recordings are lifecycled. During deployment, you have the option to configre the lifecycle window, if desired. Additionally, you have the option to keep, archive, or delete voicemail recordings. 

### How to deploy
To deploy Voicemail Express, you will need to complete the following:
1. Complete the [Voicemail Express Prerequisites](Docs/vmx_prerequistes.md)
1. Complete the [Voicemail Express Installation](Docs/vmx_installation_instructions.md)

### How to upgrade
To upgrade Voicemail Express, follow the [Upgrade Your Installation](Docs/vmx_upgrade.md) instructions.

### About Voicemail Express
Once Voicemail Express has been deployed, you can learn more about it by reading the [High-level overview of the Voicemail Express solution](Docs/vmx_core.md).

### How to uninstall
To remove Voicemail Express follow the instructions below:
1.  [Removing/Uninstalling Voicemail Express](Docs/vmx_uninstall.md)

Finally, some basic troubleshooting steps can be found on the [Troubleshooting Common Voicemail Issues](Docs/vmx_troubleshooting.md) page.

## Roadmap
The following items are currently planned for future releases. Changes to roadmap depend on feedback, however one overarching tenent of VocieMail Express is to keep the solution lightweight, with a minimal number of required services and administration. 
-  **1H2024**
   -  Optional delivery mode add-ins: Allows you to add additional delivery modes as desired. The first batch of delivery modes will be:
      -  Email via SES
      -  Salesforce Case
      -  Salesforce custom objects
   -  Update KVStoS3 function to Python
   -  Example flows
   -  Notification Option
-  **2h2024**
   -  Reduce layer size for default deployments
   -  Reduce complexity and number of functions
   -  GenAI summary option
   -  Support for GitHub sync
      

**Current Published Version:** 2024.06.01
Current published version is the version of the code and templates that has been deployed to our S3 buckets
