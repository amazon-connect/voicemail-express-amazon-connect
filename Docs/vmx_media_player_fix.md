# Media Player Fix
In some regions, the rendering of the view is incorrectly formatting the media player url. To address this please make the following changes. 

1.  In the Amazon Connect UI, open the **VMX3_Guided_Task_Agent_Flow_%INSTANCE%** flow.
1.  Between the **Generate Presigned URL** and the **Show VMX Guided Task view** blocks, add a **Set contact attributes** block.
1.  In the new block, set the following attributes as **FLOW ATTRIBUTES**:
    -  key: media_player, value (Set manually): `{"TemplateString":"<div><audio controls controlsList='nodownload' preload='auto' src='$.External.vmx3_presigned_url' style='width: 100%;'></audio><p>&nbsp;</p></div>"}`
    -  key: customer_data, value (Set manually): `{"Items":[{"Value":"$.Attributes.vmx3_source_queue"},{"Value":"$.Attributes.vmx3_target"},{"Value":"$.Attributes.vmx3_callback_number"},{"Value":"$.Attributes.vmx3_timestamp"}]}`
    -  key: genai_summary, value (Set manually): `{"TemplateString":"<h2><b>Generative AI Summary</b></h2>  <p>$.Attributes.vmx3_genai_summary</p>"}`
    -  key: vm_transcript, value (Set manually): `{"TemplateString":"<div>$.Attributes.vmx3_transcript</div>"}`
1.  **Save** the block
1.  Connect the **Success** and **Error** branches of the **Generate Presigned URL** block to the input of the new **Set contact attributes** block.
1.  Connect the exit paths of the **Set contact attributes** block to the **Show VMX Guided Task view** block. 
1.  Modify the **Show VMX Guided Task view** block as follows:
    -  Set the **customer_data** value to:
       -  Set Dynamically
       -  Namespace: Flow
       -  Key: customer_data
    -  Set the **GenAISummary** value to:
       -  Set Dynamically
       -  Namespace: Flow
       -  Key: genai_summary
    -  Set the **media_player** value to:
       -  Set Dynamically
       -  Namespace: Flow
       -  Key:  media_player
    -  Set the **transcript_box** value to:
       -  Set Dynamically
       -  Namespace: Flow
       -  Key:  vm_transcript
1.  **Save** the block
1.  **Save** the flow
1.  **Publish** the flow

Once this is complete, run some test voicemails through the guided flow experience to validate functionality.

Thanks to [Javier Vargas](https://www.linkedin.com/in/javier-eduardo-vargas-a34041a/) for identifying this and coming up with a solution. 