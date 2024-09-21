# Upgrade Voicemail Express
When new versions of Voicemail Express are release, you can easily upgrade to the latest version using the **Update** feature of Amazon CloudFormation. There are a few considerations that you will need to note prior to the upgrade:

1.  The upgrade process will overwrite any customizations that you have made. Best practice is to note the modifications you have made so that they can be migrated to the new version. You can also create your own versions of the contact flows and Lambda functions, if you like. That will allow for deployment without overwriting your existing modifications
1.  When you load the new template, it will retain the previous settings. You **must** make sure to change the template version field at the bottom to get the new version.

## Upgrade Instructions
1.  Open this link in a new tab: [Voicemail Express CloudFormation template](../CloudFormation/vmx3.yaml). In the new tab right-click/control-click the **raw** button and save the template locally.
1.  Login to the [AWS Console](https://console.aws.amazon.com).
1.  Navigate to the [AWS CloudFormation console](https://console.aws.amazon.com/cloudformation/home).
1.  Make sure that you are in the correct region for your deployment.
1.  Select **Stacks**, then choose the Voicemail Express stack that you deployed. If you don't recall the name, the description should include **Voicemail Express**.
1.  Choose **Update**.
1.  Select the option to **Replace existing template**, then choose **Upload a template file**.
1.  Select **Choose file**.
1.  Navigate to the **vmx3.yaml** file that you downloaded previously and choose **Open**.
1.  Wait a moment for the S3 URL to update, then find the parameter field labeled **(ADVANCED USE ONLY) What is version you wish to deploy?**.
1.  Change that value to the latest version available. You can find the latest version at the end of the [README](https://github.com/amazon-connect/voicemail-express-amazon-connect) page.
1.  There may have been additional fields and changes. Please validate/update all other fields as well.
1.  Once the parameters are filled out, choose **Next**
1. 	Scroll to the bottom and select **Next**
1. 	Scroll to the bottom, select the boxes to **acknowledge that IAM resources will be created**
1.  Select **Submit**
1.  The deployment will take 3-5 minutes. During this time, multiple nested stacks will be deployed. Once the main stack shows **UPDATE_COMPLETE**, your deployment of Voicemail Express is complete.