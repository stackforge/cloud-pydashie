from example_samplers import *

def run(app, xyzzy):
    samplers = [
        SynergySampler(xyzzy, 3),
        HotnessSampler(xyzzy, 3),
        BuzzwordsSampler(xyzzy, 2), # 10
        ConvergenceSampler(xyzzy, 1),
        ProgressBarsSampler(xyzzy, 5),
        UsageGaugeSampler(xyzzy, 3),
        ZabbixSampler(xyzzy,3)
    ]

    try:
        app.run(debug=True,
                host='0.0.0.0',
                port=5000,
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
