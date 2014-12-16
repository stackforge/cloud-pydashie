Openstack-PyDashie
########

PyDashie is a port of `Dashing <https://github.com/Shopify/dashing>`_ by `Shopify <http://www.shopify.com/>`_ to Python 2.7

This is simply an implementation of pydashie tailored to showing information about an openstack cluster with nagios/icinga for monitoring. It is primarily for internal use by maintainers of openstack deloyments, as the current flask file servicing may be somewhat unsafe for public access.

It uses the standard python clients for collecting formation from openstack across multiple regions.

The nagios/icinga data is currently collected via ssh but in future might be moved to MKlivestatus as the current method is roundabout.

.. image:: http://catalyst.github.com/openstack-pydashie/images/mainscreen.png

**NOTE**: The current layout is hardcoded for 1080p. This might be changed to be configurable by the conf.yaml later. If you need to change the sizing, you can do so by changing the widget dimensions and number of columns within this function:

    https://github.com/catalyst/openstack-pydashie/blob/master/pydashie/assets/javascripts/app.js#L336

Setup
############

Configuration is handled via a yaml file as follows:

.. code-block:: yaml

    main:
        log_file: pydashie.log
    openstack:
        allocation:
            RegionOne:
                vcpus_allocation_ratio: 2.0
                ram_allocation_ratio: 1.0
                # remove this amount per node available metric
                reserved_ram_per_node: 0
                reserved_vcpus_per_node: 0
                # total IPs are here as getting this from Neutron is
                # far from straightforward
                total_floating_ips: 256
        auth:
            auth_url: 'http://localhost:5000/v2.0'
            username: 'admin'
            password: 'openstack'
            project_name: 'demo'
            insecure: False
    nagios:
        services:
            RegionOne:
                statfile: './RegionOne-status.dat'
                host: 'RegionOne-mon0'
                username: 'admin'

Because of differences between allocation per region, and the need for a region list, each region is given it's own allocation data. We use this to know which regions to build clients for and aggregate data over, but in future might try and query a for a full region list and for allocation data from openstack itself.

The nagios collection relies on a local ssh key for the given username, and access for that key on the given host. 

Widgets
############

Info on adding/removing/updating widgets will go here later.

Installation
############

For development purposes,

    python setup.py develop

OR

    python setup.py install

Running
############

Provided you have a conf with working credentials and correctly named regions, you can run the application by:

    pydashie -c conf.yaml

Goto localhost:5050 to view the application in action.

**NOTE**: Getting the app up and running quickly with just openstack credentials is relatively easy, and you can simply comment out the nagios samplers from:

     https://github.com/catalyst/openstack-pydashie/blob/master/pydashie/openstack_app.py

The port and interface can also be set via the commandline:

    pydashie -c conf.yaml -ip 0.0.0.0 -p 5050

Although they default to 0.0.0.0 and 5050 if not manually given.
