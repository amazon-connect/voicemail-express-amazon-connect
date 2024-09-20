# Delivering Voicemails as Email via Amazon Simple Email Service (SES)
Email delivery is fairly straightforward from an AWS perspective. Once you have [validated the email domain/addresses](vmx_prerequistes.md#setup-steps-for-email-delivery), and configured queue emails appropriately, there is little else to manage. The main effort here would be on creating additional email templates, where required.

## Routing Emails to Agent Email Addresses
Agent email address field is selectable on deployment and can be either: `Email, SecondaryEmail, or Username`. For SAML implementations, you will be using either `SecondaryEmail` or `Username`. Other implementations may use whichever field is appropriate. The agent's email address must be in one of these fields. 

## Additional Contact Attributes Specific to Email
There are three additional contact attribute that applies to this delivery model:
-  **email_from (Optional)**: (email address) email address to send the voicemail FROM. If this is not provided, the default FROM address configured during implementation will be used.
    -  Example: 'email_from':'my_company@example.com'
-  **email_to (Optional)**: (email address) email address to send the voicemail TO. If this is not provided, and it cannot be determined by looking at the agent or queue data, the default TO address configured during implementation will be used.
    -  Example: 'email_to':'my_company@example.com'
-  **email_template (Optional)**: (template name) Amazon SES email template to use when sending this email.  If this is not provided, the default email template configured during implementation will be used.

## Creating New Email Templates Using the Provided Lambda Functions
To help customers manage email templates, the voicemail express solution includes an AWS Lambda function that allows for easy creation, modification, and deletion of email templates. You do not have to use this function to build or modify templates, however SES only provides programmatic or CLI methods for managing templates; there is no GUI.

### Standard Data Included with the Email Request
The standard configuration passes along a few key data elements by default. These are values that may not be a part of the contact trace record and have been set by the VMXPackager Lambda function. These data elements can be referenced in any custom templates that you use without additional configuration.

-  **callback_number**: the phone number that the customer called from or provided as a callback number
-  **entity_name**: the name of the queue or agent that this voicemail was intended for
-  **presigned_url**: the presigned URL of the voicemail recording
-  **transcript_contents**: the transcript of the voicemail

In SES templates, you reference these variables using double curly braces. For example, in your template code, you would reference entity_name as follows: `This is a voicemail for {{entity_name}}.`

### Using Custom Data in Templates
Since all contact attributes are passed along as data with the email request, you can use any contact attribute value in your templates. Your custom attributes are referenced in the same manner as the standard attributes, with double curly braces. For example, if you had an attribute named `customer_level` you could reference that as follows: `Voicemail from a {{customer_level}} customer.`

### Using the VMXSESTool function
The VMXSESTool Lambda function is designed to give users an easy way to create and manage templates without having to write new code. To invoke the function, you create test events. The test events will tell the function which method to execute and pass along the required data. Each supported method is detailed below. The test events require different values to work correctly. They are defined below:
-  **mode**: (create|get|update|delete) This defines the operation to perform; **create** a new template, **get** an existing template, **update an existing template**, **delete** am existing template
-  **template_name**: (string) The name of the template
-  **template_subject**: (string) The email subject. This can include attribute keys (in double curly braces)
-  **template_text**: (string) The plain text formatted version of the email. This is used when viewing the email in a plain text email application. This can include attribute keys (in double curly braces).
-  **template_html**: (string) The HTML formatted version of the email. This is used when viewing the email in a client that supports HTML email.

#### Example Test Events
Create a new template:
```
{
  "mode":"create",
  "template_name":"NewAgent",
  "template_subject":"This is a new voicemail from {{callback_number}}.",
  "template_text":"Dear {{entity_name}}, You have a new voicemail from {{callback_number}}. You can listen to the message via the following URL: {{presigned_url}}",
  "template_html":"<h1>Voicemail for {{entity_name}} </h1><p>You have a new voicemail from {{callback_number}}.</p><p><a href=\"{{presigned_url}}\">Listen to the voicemail.</a></p><h2>Voicemail transcription</h2><p>{{transcript_contents}}</p>"
}
```
Get an existing template:
```
{
  "mode":"get",
  "template_name":"NewAgent"
}
```

Update an existing template:
```
{
  "mode":"update",
  "template_name":"NewAgent",
  "template_subject":"This is a super new voicemail from {{callback_number}}.",
  "template_text":"Dear {{entity_name}}, You have a new voicemail from {{callback_number}}. The recording can be found here: {{presigned_url}}",
  "template_html":"<h1>Fresh Voicemail for {{entity_name}} </h1><p>You have a new voicemail from {{callback_number}}.</p><p><a href=\"{{presigned_url}}\">Listen to the voicemail.</a></p><h2>Voicemail transcription</h2><p>{{transcript_contents}}</p>"
}
```

Delete an existing template:
```
{
  "mode":"delete",
  "template_name":"NewAgent"
}
```
