from example_samplers import (
    CPUSampler,
    RAMSampler,
    RegionsRAMSampler,
    RegionsCPUSampler,
    NagiosSampler,
    BuzzwordsSampler,
    ConvergenceSampler,
    UsageGaugeSampler,
)


def run(args, conf, app, xyzzy):

    samplers = [
        CPUSampler(xyzzy, 10, conf['openstack']),
        RAMSampler(xyzzy, 10, conf['openstack']),
        RegionsCPUSampler(xyzzy, 10, conf['openstack']),
        RegionsRAMSampler(xyzzy, 10, conf['openstack']),
        NagiosSampler(xyzzy, 10, conf['nagios']),
        # BuzzwordsSampler(xyzzy, 2),
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
