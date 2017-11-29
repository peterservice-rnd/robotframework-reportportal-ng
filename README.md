# robotframework-reportportal

Short Description
---

Robot Framework listener module for integration with Report Portal

Usage
---

Example command to run test using pabot with report portal listener.
 
```bash
pybot --listener reportportal_listener --escape quot:Q \
--variable RP_ENDPOINT:http://reportportal.local:8080 \
--variable RP_UUID:73628339-c4cd-4319-ac5e-6984d3340a41 \
--variable RP_LAUNCH:"Demo Tests" \
--variable RP_PROJECT:DEMO_USER_PERSONAL test_folder
```
