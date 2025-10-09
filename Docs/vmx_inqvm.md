# Offer voicemail option to customers in queue
To offer the voicemail option while a customer is in queue, you effectively need to reproduce the functionality of the VMX3_Main_VM_Module flow in your customer queue flow, with one key difference: you need to provide a mechanism to clear the voicemail flag if an agent takes the contact. 

In Amazon Connect, when a customer is in a queue flow, if an eligible agent becomes available, the caller will be reouted to them, regardless of what they are doing in the queue flow. While this is good, we do want customers to connect to agents, if the flag is not cleared, the entire conversation will be streamed and processed as if it were a voicemail. To prevent this, we can use an agent whisper flow to clear them vmx3_flag setting. Additionally, the VMX3_AWS_Test_Flow flow has been updated to provide an example of how to set the queue flow, agent whisper, and other attributes to make the in-queue experience possible

In this version of Voicemail Express, three contact flows have been provided to help deliver this experience:
-  VMX3_In_Queue_Option: sample customer queue flow that loops recordings and provides the voicemail offer experience. Also sets the agent whisper flow.
-  VMX3_In_Queue_Agent_Whisper: looks for the presence of the vmx3_flag, and sets it to 0 if it exists
-  VMX3_In_Queue_Customer_Whisper: lets the customer know that they are now connecting to an agent

## VMX3_In_Queue_Option
![VMX3_In_Queue_Option Flow](/Docs/Img/vmx3_inqueue_option.png)
This flow provides the option to leave a voicemail instead of remaining in queue. It tracks the customer reposne to the offer, and does not offer the option again if the customer declines so that they are not repeatedly asked the same question. If they do select to leave a voicemail, the VMX3_In_Queue_Agent_Whisper flow is set, and the rest of the experience mimics the normal voicemail experience. 

## VMX3_In_Queue_Agent_Whisper
![VMX3_In_Queue_Agent_Whisper Flow](/Docs/Img/vmx3_inqueue_whisper.png)
This flow checks for the presence of the vmx3_flag and, if it exists, resets the value to 0 so that this contact is not interpreted as a voicemail. 


## VMX3_In_Queue_Customer_Whisper
![VMX3_In_Queue_Agent_Whisper Flow](/Docs/Img/vmx3_inqueue_customer_whisper.png)
This flow lets the customer know that an agent has become available and is connecting to the call.

## Implementing in your environment
You can use the test flow as an example of how to configure the vmx3 attributes prior to queuing. Make sure to set the customer queue flow before doing the transfer. Once you transfer to the provided customer queue flow, the agent and customer whisper flows are set for you. These are critical should an agent become available and the call transfers.