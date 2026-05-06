--- 
name: release-notes
description: Analyze the all commit's from Git from the last push and write a friendly document and send it to the client's or the management team
allowed tools: [Bash, Read, Git]
---
When you generate notes , run scripts/get-history.sh to take the history .
Then , form the result using the template from assets/changelog-template.md
