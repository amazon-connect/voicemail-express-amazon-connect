# Voicemail Express 3 Changelog

## 2024.10.24
- Removed IAM user creation in preference of provided the appropriate policy to the presigner lambda

## 2024.09.01
-  Added guided task option, visualizing a player, and obfuscating short lived URL
-  IAM Roles and policies by function instead of one central role/policy
-  Updated Email process to allow users to select the User field which contains the agent email
-  Fixed an issue with email templates that prevented dynamic template selection

## 2024.08.01
-  Rewrote KVStoS3 function in Python, completing conversion of code to Python 3.12
-  Switched to the GetMediaForFragmentList API for Kinesis Video Streams Archived Media to extract the audio from KVS.
-  Adopted native Lambda logging in all functions and improved logging
-  Improved error handling in all functions
-  Removed the Node common layer
-  Load-tested 1,000s of voicemails
-  Improved [Troubleshooting](Docs/vmx_troubleshooting.md) section
-  Added [Getting Support](Docs/vmx_support.md)
-  Added [Changelog](Docs/vmx_changelog.md)

## 2024.07.03
-  Updated KVS to S3 function to reduce error conditions in environments with heavy KVS use or long retention windows.
-  Updated all Lambda functions to use the native Lambda logging configuration
-  Changed code/template buckets to further seperate from VMX2

## 2024.07.02
-  Improved CR filtering to reduce non-vmx records
-  Changed trigger configuration to reduce errors blocking subsequent records

## 2024.07.01
-  Added support for voicemail delivery via Amazon Simple Email Service

## 2024.06.01
-  Improved performance of the KVStoS3 function
-  Kinesis Data Stream filtering for records to reduce Lambda invocations
-  Added Voicemail date/time info to the task (based on work by [DanBloy](https://github.com/DanBloy))
-  Updated flow naming for consistency
-  Additional load testing

## 2024.05.01
-  Resolved an edge case that could allow a voicemail task to be duplicated
-  Resolved an issue where corrupted or invalid audio files would cause the transcription to fail, resulting in a lost voicemail
-  Added new messaging to identify KVS startup issues on first run, and to hopefully resolve them
-  Upgraded all Python functions to 3.12
-  Reduced the layer size for the Python layer

## 2024.03.20
-  Simplified deployment process.
-  Removed Salesforce-centric deployment options.
-  All voicemails are delivered as Amazon Connect tasks. The option to add other deliver modes will come in a future release. 
-  An Amazon Connect flow module named **VMX3VoicemailCoreModule** is provided. This provides a standard voicemail experience, sets all required attributes, and records the voicemail. You can use this module in any standard Amazon Connect inbound contact flow to provide the voicemail experience without needing to create a custom flow.
-  The VMX3TestFlow has been modified to use the **VMX3VoicemailCoreModule**.
-  Modified transcribe job name to eliminate conflicts.