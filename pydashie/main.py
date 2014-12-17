import argparse
import logging
import os
import sys
import Queue
import yaml

from flask import (
    current_app,
    Flask,
    render_template,
    Response,
    send_from_directory,
    request,
)

app = Flask(__name__)

# we setup the log in __main__
log = None


@app.route("/")
def main():
    return render_template('main.html', title='pyDashie')


@app.route("/dashboard/<dashlayout>/")
def custom_layout(dashlayout):
    return render_template('{}.html'.format(dashlayout), title='pyDashie')


@app.route("/assets/application.js")
def javascripts():
    if not hasattr(current_app, 'javascripts'):
        import coffeescript
        scripts = [
            'assets/javascripts/jquery.js',
            'assets/javascripts/es5-shim.js',
            'assets/javascripts/d3.v2.min.js',

            'assets/javascripts/batman.js',
            'assets/javascripts/batman.jquery.js',

            'assets/javascripts/jquery.gridster.js',
            'assets/javascripts/jquery.leanModal.min.js',

            # 'assets/javascripts/dashing.coffee',
            'assets/javascripts/dashing.gridster.coffee',

            'assets/javascripts/jquery.knob.js',
            'assets/javascripts/rickshaw.min.js',
            # 'assets/javascripts/application.coffee',
            'assets/javascripts/app.js',
            # 'widgets/clock/clock.coffee',
            'widgets/number/number.coffee',
            'widgets/hotness/hotness.coffee',
            'widgets/progress_bars/progress_bars.coffee',
            'widgets/usage_gauge/usage_gauge.coffee',
            'widgets/nagios/nagios.coffee',
            'widgets/nagios_list/nagios_list.coffee',
            'widgets/graph/graph.coffee',
        ]
        nizzle = True
        if not nizzle:
            scripts = ['assets/javascripts/application.js']

        output = []
        for path in scripts:
            path = ('{1}/{0}'.
                    format(path,
                           os.path.dirname(os.path.realpath(__file__))))
            output.append('// JS: %s\n' % path)
            if '.coffee' in path:
                log.info('Compiling Coffee for %s ' % path)
                contents = coffeescript.compile_file(path)
            else:
                f = open(path)
                contents = f.read()
                f.close()

            output.append(contents)

        if nizzle:
            f = open('/tmp/foo.js', 'w')
            for o in output:
                print >> f, o
            f.close()

            f = open('/tmp/foo.js', 'rb')
            output = f.read()
            f.close()
            current_app.javascripts = output
        else:
            current_app.javascripts = ''.join(output)

    return Response(current_app.javascripts, mimetype='application/javascript')


@app.route('/assets/application.css')
def application_css():
    scripts = [
        'assets/stylesheets/application.css',
    ]
    output = ''
    for path in scripts:
        path = '{1}/{0}'.format(path,
                                os.path.dirname(os.path.realpath(__file__)))
        output = output + open(path).read()
    return Response(output, mimetype='text/css')


@app.route('/assets/images/<path:filename>')
def send_static_img(filename):
    directory = os.path.join('assets', 'images')
    return send_from_directory(directory, filename)


@app.route('/views/<widget_name>.html')
def widget_html(widget_name):
    html = '%s.html' % widget_name
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        'widgets', widget_name, html)
    if os.path.isfile(path):
        f = open(path)
        contents = f.read()
        f.close()
        return contents


class Z:
    pass


xyzzy = Z()
xyzzy.events_queue = {}
xyzzy.last_events = {}
xyzzy.using_events = True
xyzzy.MAX_QUEUE_LENGTH = 20
xyzzy.stopped = False


@app.route('/events')
def events():
    if xyzzy.using_events:
        event_stream_port = request.environ['REMOTE_PORT']
        current_event_queue = Queue.Queue()
        xyzzy.events_queue[event_stream_port] = current_event_queue
        current_app.logger.info('New Client %s connected. Total Clients: %s' %
                                (event_stream_port, len(xyzzy.events_queue)))

        # Start the newly connected client off by pushing
        # the current last events
        for event in xyzzy.last_events.values():
            current_event_queue.put(event)
        return Response(pop_queue(current_event_queue),
                        mimetype='text/event-stream')

    return Response(xyzzy.last_events.values(), mimetype='text/event-stream')


def pop_queue(current_event_queue):
    while not xyzzy.stopped:
        try:
            data = current_event_queue.get(timeout=0.1)
            yield data
        except Queue.Empty:
            # this makes the server quit nicely - previously the queue
            # threads would block and never exit. This makes it keep
            # checking for dead application
            pass


def purge_streams():
    big_queues = [port for port, queue in xyzzy.events_queue
                  if len(queue) > xyzzy.MAX_QUEUE_LENGTH]
    for big_queue in big_queues:
        current_app.logger.info(('Client %s is stale. Disconnecting.' +
                                 ' Total Clients: %s') %
                                (big_queue, len(xyzzy.events_queue)))
        del queue[big_queue]


def close_stream(*args, **kwargs):
    event_stream_port = args[2][1]
    del xyzzy.events_queue[event_stream_port]
    log.info(('Client %s disconnected. Total Clients: %s' %
              (event_stream_port, len(xyzzy.events_queue))))


def run_sample_app():
    a = argparse.ArgumentParser("Openstack-PyDashboard")

    a.add_argument("-c", "--config", dest="config", help="Path to config file",
                   required=True)
    a.add_argument("-ip", "--interface", dest="ip",
                   help="IP address to serve on.", default="0.0.0.0")
    a.add_argument("-p", "--port", help="port to serve on", default="5050")

    args = a.parse_args()

    conf = None

    try:
        with open(args.config) as f:
            conf = yaml.load(f)
    except IOError as e:
        print "Couldn't load config file: %s" % e
        sys.exit(1)

    logging.basicConfig(filename=conf['main']['log_file'],
                        level=logging.INFO,
                        format='%(asctime)s %(message)s')
    global log
    log = logging.getLogger(__name__)

    import SocketServer
    SocketServer.BaseServer.handle_error = close_stream
    import openstack_app
    openstack_app.run(args, conf, app, xyzzy)


if __name__ == "__main__":
    run_sample_app()
