import datetime
import json
from math import ceil

from repeated_timer import RepeatedTimer

from novaclient.v1_1 import client as novaclient
from cinderclient.v1 import client as cinderclient
from keystoneclient.v2_0 import client as keystoneclient


class DashieSampler(object):
    def __init__(self, app, interval, conf=None):
        self._app = app
        self._os_clients = {}
        self._conf = conf
        self._timer = RepeatedTimer(interval, self._sample)

    def stop(self):
        self._timer.stop()

    def name(self):
        '''
        Child class implements this function
        '''
        return 'UnknownSampler'

    def sample(self):
        '''
        Child class implements this function
        '''
        return {}

    def _send_event(self, widget_id, body):
        body['id'] = widget_id
        body['updatedAt'] = (datetime.datetime.now().
                             strftime('%Y-%m-%d %H:%M:%S +0000'))
        formatted_json = 'data: %s\n\n' % (json.dumps(body))
        self._app.last_events[widget_id] = formatted_json
        for event_queue in self._app.events_queue.values():
            event_queue.put(formatted_json)

    def _sample(self):
        data = self.sample()
        if data:
            self._send_event(self.name(), data)

    def _convert(self, num):
        if num >= 1024 ** 3:
            return int(ceil(num / (1024 ** 3))), 'GB'
        elif num >= 1024 ** 2:
            return int(ceil(num / (1024 ** 2))), 'MB'
        elif num >= 1024:
            return int(ceil(num / (1024))), 'KB'
        else:
            return num, 'B'

    def _client(self, service, region):
        if not self._os_clients.get(region):
            self._os_clients[region] = {}

        if not self._os_clients[region].get(service):
            if service == 'compute':
                client = novaclient.Client(
                    self._conf['auth']['username'],
                    self._conf['auth']['password'],
                    self._conf['auth']['project_name'],
                    self._conf['auth']['auth_url'],
                    region_name=region,
                    insecure=self._conf['auth']['insecure'])
                self._os_clients[region][service] = client
            elif service == 'storage':
                client = cinderclient.Client(
                    self._conf['auth']['username'],
                    self._conf['auth']['password'],
                    self._conf['auth']['project_name'],
                    self._conf['auth']['auth_url'],
                    region_name=region,
                    insecure=self._conf['auth']['insecure'])
                self._os_clients[region][service] = client
            elif service == 'identity':
                client = keystoneclient.Client(
                    username=self._conf['auth']['username'],
                    password=self._conf['auth']['password'],
                    project_name=self._conf['auth']['project_name'],
                    auth_url=self._conf['auth']['auth_url'],
                    region_name=region,
                    insecure=self._conf['auth']['insecure'])
                self._os_clients[region][service] = client

        return self._os_clients[region][service]
