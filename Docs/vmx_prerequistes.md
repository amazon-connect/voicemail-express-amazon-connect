# Voicemail Express Prerequisites
Before deploying the Voicemail Express, you will need to complete a few prerequisites. These will ensure that your Amazon Connect instance is ready for Voicemail Express. These **must be completed** prior to the deployment and use of Voicemail Express.

## Delivery mode specific prerequisites
### Setup steps for Amazon Connect Task delivery
For Amazon Connect Task delivery, you simply need to have the following configured for your Amazon Connect instance:
-  [Contact records streaming via Amazon Kinesis Data Stream](https://docs.aws.amazon.com/connect/latest/adminguide/data-streaming.html) (Amazon Kinesis Data Firehose is not supported)
-  [Live media streaming](https://docs.aws.amazon.com/connect/latest/adminguide/customer-voice-streams.html) must be enabled and the retention period needs to be set for at least 1 hour. Longer is not required.
-  Routing profiles have [Tasks enabled in the Channel Settings](https://docs.aws.amazon.com/connect/latest/adminguide/routing-profiles.html), and for the appropriate queues
-  Agents are [assigned to those routing profiles](https://docs.aws.amazon.com/connect/latest/adminguide/configure-agents.html).

### Setup steps for Email delivery
For email delivery, Voicemail Express uses SES. If you have not already configured SES for use in your account, you will need to perform some minimal configuration to validate email addresses. 

-  There are two types of email addresses in this solution: `from` and `to`. 
   -  The from address will indicate where the email is from, for example contact_center@yourcompany.com. You can dynamically assign the from address, or simply use a default. This decision can be made on a call-by-call basis. 
   -  The `to` address will be where the email is being delivered to. For agent voicemails, it should be the email address of the agent, for example: joe.smith@yourcompany.com. For queue voicemails, it would be a group address or distribution list, for example: customer_support@yourcompany.com. 
   -  In order for SES to send emails using your email addresses, you need to validate ownership of either the individual addresses or the entire email domain. You can follow the instructions online for [creating and verifying identities in Amazon SES](https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html) to accomplish this. 
   -  You must use verified identities/domains, or the emails will not be delivered.

#### Voicemail to agent emails
This solution is designed to use the agent's email address, configured in Amazon Connect, as the delivery email address. If you wish to use a different email address, the packager function will need to be modified to account for that. 

#### Voicemail to queues
For queues, the solution is designed to extract the email address from the queue tags. This allows you to set the address by queue. If no address is specified, the solution will used the provided default address.

#### Update the queue to include the email address tag
1.  Login to the Amazon Connect administration interface
1.  Select Routing, then choose Queues
1.  Select the Queue that you wish to modify
1.  In the **Tags** section, create a new tag with the key of `vmx3_queue_email` and the value set to the email address that you want voicemails delivered to for this queue.
1.  Save the queue

## Prerequisites Complete
You have completed the prerequisites for Voicemail Express. You may now proceed to the [installation instructions](vmx_installation_instructions.md).
