# Removing/Uninstalling Voicemail Express
WUninstalling Voicemail Express is a fairly straightforward process.

## Prepare the Amazon Connect Instance
First, you will need to prepare the instance for Voicemail removal. To do this, perform the following tasks:
1.  Log into your Amazon Connect instance as an administrator.
1.  Select **Channels**, then choose **Phone numbers**.
1.  Make sure that none of VMX default flows are set as the **Contact flow/IVR** for any phone numbers in your instance. The default flows all begin with `VMX3`

> [!Caution]
> You may have referenced some of these flows from within your other flows. While not necessary to uninstall Voicemail Express, you should also validate that these default flows are not referenced elsewhere as that could result in flow failures.

## Move your voicemail recordings/transcripts
Since the retention policy of the CloudFormation template used to deploy voicemail does not allow for the deletion of the S3 buckets that hold the voicemail recordings and temporary transcripts if they have objects in them, you should first either copy the contents elsewhere (if you wish to retain copies for archival) or delete the contents of the S3 buckets. 

To determine which S3 buckets are in use:
1.  Login to the [AWS Console](https://console.aws.amazon.com).
1.  Navigate to the [AWS CloudFormation console](https://console.aws.amazon.com/cloudformation/home).
1.  Make sure that you are in the correct region for your deployment.
1.  Select **Stacks**, then choose the **VMXCoreStack** stack.
1.  Select the **Resources** tab.
1.  In the **Logical ID** column, find both **VMXS3RecordingsBucket** and **VMXS3TranscriptsBucket**. 
1.  The link in the corresponding **Physical ID** column will take you to each bucket.
1.  Export or delete the objects as desired.

## Delete the CloudFormation Stack
Next, you will delete the CloudFormation stack. This will remove **ALL** AWS resources that were created with the conditional exception of the S3 buckets. By default, if the S3 buckets have any objects in them, they will not be deleted and all contents will remain in place. If you are not concerned with keeping your recordings, or if you wish to move them to 

1.  Login to the [AWS Console](https://console.aws.amazon.com).
1.  Navigate to the [AWS CloudFormation console](https://console.aws.amazon.com/cloudformation/home).
1.  Make sure that you are in the correct region for your deployment.
1.  Select **Stacks**, then choose the Voicemail Express stack that you deployed. If you don't recall the name, the description should include **Voicemail Express**.
1.  Select **Delete**, then confirm by choosing **Delete** from the popup.
1.  **IF** your stack deleted completely, you may move on to the next section.
1.  **IF** your stack failed to fully delete, it is most likely due to there being content in your S3 bucket. In this case, select the nested stack that failed, most likely the VMXCoreStack, and choose **Delete**. 
1.  In the popup window, you will likely see the resources that could not be deleted, which are probably the S3 buckets. Select both to retain them, and select **Delete**.
1.  Once the nested stack deletes, reselect the main stack, and select **Delete**. This time, the resources should delete without further issue.

You have successfully removed Voicemail Express.