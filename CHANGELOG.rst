v0.3
====

* Remove support for auto-detecting and running migrations from the main code.

    * Instead, users must manually specify the comamnds to run via the post_deploy node in the configuration YAML. See settings/sample.conf for an example.
    * This change provides better support for pipelined deployments.