This module is based on the `server_environment` module to use files for
configuration. So we can have a different configuration for each
environment (dev, test, integration, prod).  This module define the config
variables for the `ebill_paynet` module.

Exemple of the section to put in the configuration file::

    [paynet_service.name_of_the_service]
    use_test_service": True,
    client_pid": 123456789,
    service_type": b2b,
    username": username,
    password": password,
