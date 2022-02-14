This module is based on the `server_environment` module to use files for
configuration. So we can have different configuration for each
environment (dev, test, integration, prod).

This module define the config variables for the `ebill_postfinance` module.

Exemple of the section to put in the configuration file::

    [postfinance_service.name_of_the_service]
    use_test_service": True,
    username": username,
    password": password,
