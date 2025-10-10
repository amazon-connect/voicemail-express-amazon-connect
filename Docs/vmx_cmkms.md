# Using Customer-managed KMS Keys for Data Streams and S3 Buckets
### Based on feedback and input from [Kgopelo](https://github.com/kgopelom)
If you wish to use customer-managed KMS keys for either the Kinesis Data Stream or for your Amazon Connect recordings bucket, you will need to update the Lambda Function Roles to include a policy that allows access to those keys. The easiest way to do this is to create a new policy and attach that policy to whichever roles will need it. The most likely roles are:
-   VMX3_Recording_Processor_Role
    -  S3 GetObject
    -  Kinesis Data Streams GetRecords
-  VMX3_Transcriber_Role
    -  S3 GetObject
-  VMX3_Guided_Flow_Role
    -  S3 GetObject
-  VMX3_Presigner_Role
    -  S3 GetObject
-  VMX3_Packager_Role
    -  S3 GetObject

You will need to create a policy that includes:
-  kms:Decrypt
-  kms:GenerateDataKey

## Example Policy
```
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Sid": "VisualEditor0",
			"Effect": "Allow",
			"Action": [
				"kms:Decrypt",
				"kms:GenerateDataKey"
			],
			"Resource": "arn:aws:kms:us-east-1:%YOURACCOUNT%:key/%YOUR_KEY_ID%"
		}
	]
}
```

Use the [least-privilege permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#grant-least-privilege) required, limiting the access to the specific key(s) and resources. 