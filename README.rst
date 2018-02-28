robotframework-reportportal-ng
==============================

|Build Status|

Short Description
-----------------

Robot Framework listener module for integration with Report Portal.

Installation
------------

::

    pip install robotframework-reportportal-ng

Usage
-----

This listener requires specified robot framework context variables to be
set up. Some of them are required for execution and some are not.

Parameters list:

::

        RP_UUID - unique id of user in Report Portal profile..
        RP_ENDPOINT - <protocol><hostname>:<port> for connection with Report Portal.
                      Example: http://reportportal.local:8080/
        RP_LAUNCH - name of launch to be used in Report Portal.
        RP_PROJECT - project name for new launches.
        RP_LAUNCH_DOC - documentation of new launch.
        RP_LAUNCH_TAGS - additional tags to mark new launch.

Example
-------

Example command to run test using pabot with report portal listener.

.. code:: bash

    pybot --listener reportportal_listener --escape quot:Q \
    --variable RP_ENDPOINT:http://reportportal.local:8080 \
    --variable RP_UUID:73628339-c4cd-4319-ac5e-6984d3340a41 \
    --variable RP_LAUNCH:"Demo Tests" \
    --variable RP_PROJECT:DEMO_USER_PERSONAL test_folder

License
-------

Apache License 2.0

.. |Build Status| image:: https://travis-ci.org/ailjushkin/robotframework-reportportal-ng.svg?branch=master
   :target: https://travis-ci.org/ailjushkin/robotframework-reportportal-ng