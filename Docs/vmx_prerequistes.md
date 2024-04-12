# Voicemail Express Prerequisites
Before deploying the Voicemail Express, you will need to complete a few prerequisites. These will insure that your Amazon Connect instance is ready for Voicemail Express. These **must be completed** prior to the deployment and use of Voicemail Express.

### Setup steps for Voicemail Express with Amazon Connect
For Amazon Connect Task delivery, you simply need to have the following configured for your Amazon Connect instance:
-  [Contact records streaming via Amazon Kinesis Data Stream](https://docs.aws.amazon.com/connect/latest/adminguide/data-streaming.html) (Amazon Kinesis Data Firehose is not supported)
-  [Live media streaming](https://docs.aws.amazon.com/connect/latest/adminguide/customer-voice-streams.html) must be enabled and the retention period needs to be set for at least 1 hour. Longer is not required.
-  Routing profiles have [Tasks enabled in the Channel Settings](https://docs.aws.amazon.com/connect/latest/adminguide/routing-profiles.html), and for the appropriate queues
-  Agents are [assigned to those routing profiles](https://docs.aws.amazon.com/connect/latest/adminguide/configure-agents.html).

## Prerequistes Complete
You have completed the prerequisites for Voicemail Express. You may now proceed to the [installation instructions](vmx_installation_instructions.md).
