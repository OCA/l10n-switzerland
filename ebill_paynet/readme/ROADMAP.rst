To Do
=====

* The B2C invoice generated is only a draft and not tested, yet.
* Invoice in currency other than CHF will not be generated correctly.
* Implementation of the automatic registration of contracts, is not implemented and probably not supported by the DWS

Improvements
============

* On the contract view the list of messages for that contract could be visible.
* When an error is returned by the service it should be clearer where it is located in the payload send.
* In the chatter add a link to the job when it fails

Refactoring
===========

The dependence on `delivery` module could be extracted in a glue module.
For v14 or v15 consider refactoring on top of EDI framework
