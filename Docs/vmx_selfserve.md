# Allow agents to pull/pick voicemails from a queue (Task delivery modes only)
Amazon Connect recently released the option to allow agents to self-assign contacts. This functions across contact types. Since voicemails are delivered as Amazon Connect Tasks, you can use this feature to allow agents to manually select voicemails from a worklist of voicemails waiting in queue instead of having them automatically route. Additionally, since this capability is configured at the routing profile, delivery can be mixed among different agent pools with some being routed automatically and some being self-service. This can be helpful in circumstances where you want voicemails to be addressed first in the morning, without having to compete with incoming contacts. This can also be used to make personal voicemails (voicemails targeted at a specific agent) available via picklist.

> [!NOTE]  
> This option is currently only available for agents using the Agent Workspace.

## Configure your Amazon Connect instance
### Update the security profile
To enable this option, you must first make sure that users have a security profile that allows them to manually assign contacts to themselves. 
1.  Login to the Amazon Connect administrative interface. 
1.  Select **Users** and choose **Security profiles**.
1.  Find the security profile that you want to modify and select the name to edit it.
1.  In the **Contact Actions** section, select **Allow 'Assign to me' for my contact** or **Allow 'Assign to me' for any contact** as appropriate for your use case. 
    -  Allow 'Assign to me' for any contact permission - Enables agents to view contacts under any of these conditions:
        -  Current Agent is the only Preferred Agent on the Contact.
        -  Current Agent is one of the Preferred Agents on the Contact.
        -  Any Agent or set of Agents are Preferred Agents on the Contact.
        -  Contact with no Preferred Agents.
    -  Allow 'Assign to me' for my contact permission - Enables agents to view contacts under these conditions:
        -  Current Agent is the only Preferred Agent on the Contact.
        -  Current Agent is one of the Preferred Agents on the Contact.
1.  **Save** the security profile.
![Security profile permnission](/Docs/Img/self_serve_security_profile.png)

### Update the Routing Profile
Next, you need to give the agent the ability to manually select tasks for each queue that you want them to. 
1.  Select **Users** and choose **Routing profiles**.
1.  Find the routing profile that you want to modify and select the name to edit it.
1.  In the **Manual Assignment** section, select the queues you want agents to be able to self-service, then set the **Channels** to **Task** for each.
1.  If you do not want tasks to automatically route, make sure to remove tasks from the queues in the **Queues** section.
1.  Save the routing profile.
![Routing profile configuration](/Docs/Img/self_serve_routing_profile.png)

### OPTIONAL: Create a new status for manual voicemail work
If you want agents to be able to remove themselves from the normal contact queue, but still address work in the worklist, you can create a new status that makes them unavailable for routing, but allows them to self-assign work. 
1.  Select **Users** and choose **Agent status**.
1.  Choose **Add new agent status**.
1.  Create a new status. Give it a name like `Working Voicemail` or something to clearly indicate that the agent is self-assigning work.
1.  Provide a description, if desired, then choose **Save**.
![New agent status](/Docs/Img/self_serve_agent_status.png)

## Validate your setup
Once you have made this changes, you can validate by performing the following:
1.  Log an agent into the agent workspace and put them into the new state.
    ![Agent in the Working Voicemail state](/Docs/Img/self_serve_logged_in.png)
1.  Place a few voicemails into queue
1.  In the agent workspace, select the **Aps** dropdown and choose **Worklist**
    ![Choose worklist](/Docs/Img/self_serve_set_worklist.png)
1.  Once the voicemails are ready and the tasks have been created, you will see thenm in the worklist.
    ![Items in worklist](/Docs/Img/self_serve_worklist_items.png)
1.  Selecting an item will load a preview of the task. 
    ![Items in worklist](/Docs/Img/self_serve_task_preview.png)
1.  Select **Assign to me**, the choose **Assign** in the popup. The task will route to you. 
    ![Items in worklist](/Docs/Img/self_serve_connected_task.png)

You're all set!