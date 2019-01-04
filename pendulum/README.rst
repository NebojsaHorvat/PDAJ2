About
=====

A distributed system for computing pendulum angles with different starting data.

Installation
============

pendulum doesn't require system wide installation, just clone this
repository to get started.


Quick start (distributed system in a box)
=========================================

Make any changes you'd like to ``Vagrantfile`` and ``docker-compose.yml``,
and please note that environment variables are used to configure the distributed
system. See ``Dockerfile.server`` and ``Dockerfile.worker`` for more details.

Run the following command will automatically provision a new virtual machine;
which will then build, configure and start the entire distributed system::

    $ vagrant up


Production use
==============
. See``Dockerfile.server`` and ``Dockerfile.worker`` for more details.

Contribute
==========

If you find any bugs, or wish to propose new features `please let us know`_. 

If you'd like to contribute, simply fork `the repository`_, commit your changes
and send a pull request. Make sure you add yourself to `AUTHORS`_.

.. _`the repository`: https://github.com/NebojsaHorvat/PDAJ2
.. _`AUTHORS`: https://github.com/NebojsaHorvat/PDAJ2/blob/master/pendulum/AUTHORS
