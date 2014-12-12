from example_samplers import (
    CPUSampler,
    RAMSampler,
    IPSampler,
    RegionsRAMSampler,
    RegionsCPUSampler,
    RegionIPSampler,
    NagiosSampler,
    NagiosRegionSampler,
    # ConvergenceSampler,
)


def run(args, conf, app, xyzzy):

    samplers = [
        CPUSampler(xyzzy, 60, conf['openstack']),
        RAMSampler(xyzzy, 60, conf['openstack']),
        IPSampler(xyzzy, 60, conf['openstack']),
        RegionsCPUSampler(xyzzy, 60, conf['openstack']),
        RegionsRAMSampler(xyzzy, 60, conf['openstack']),
        RegionIPSampler(xyzzy, 60, conf['openstack']),
        NagiosSampler(xyzzy, 15, conf['nagios']),
        NagiosRegionSampler(xyzzy, 15, conf['nagios']),
        # ConvergenceSampler(xyzzy, 1),
    ]

    try:
        app.run(debug=True,
                host=args.ip,
                port=args.port,
                threaded=True,
                use_reloader=False,
                use_debugger=True
                )
    finally:
        print "Disconnecting clients"
        xyzzy.stopped = True

        print "Stopping %d timers" % len(samplers)
        for (i, sampler) in enumerate(samplers):
            sampler.stop()

    print "Done"
