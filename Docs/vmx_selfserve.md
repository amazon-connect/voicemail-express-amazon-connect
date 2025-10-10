# Allow agents to pull/pick voicemails from a queue (Task delivery modes only)
### Based on feedback and input from [Kgopelo](https://github.com/kgopelom)
Amazon Connect recently released the option to allow agents to self-assign contacts. This functions across contact types. Since voicemails are delivered as Amazon Connect Tasks, you can use this feature to allow agents to manually select voicemails from a worklist of voicemails waiting in queue instead of having them automatically route. Additionally, since this capability is configured at the routing profile, delivery can be mixed among different agent pools with some being routed automatically and some being self-service. 

To enable this option, you must first make sure that users have a security profile that allows them to manually assign contacts to themselves. 
1.  Login to the Amazon Connect administrative interface. 
1.  Select **Users** and choose **Security profiles**.
1.  Find the security profile that you want to modify and select the name to edit it.
1.  