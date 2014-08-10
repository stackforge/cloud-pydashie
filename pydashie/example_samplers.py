from dashie_sampler import DashieSampler

import random
import collections

class SynergySampler(DashieSampler):
    def __init__(self, *args, **kwargs):
        DashieSampler.__init__(self, *args, **kwargs)
        self._last = 0

    def name(self):
        return 'synergy'

    def sample(self):
        s = {'value': random.randint(0, 100),
             'current': random.randint(0, 100),
             'last': self._last}
        self._last = s['current']
        return s

class HotnessSampler(DashieSampler):
    def __init__(self, *args, **kwargs):
        DashieSampler.__init__(self, *args, **kwargs)
        self._last = 0

    def name(self):
        return 'hotness'

    def sample(self):
        s = {'value': random.randint(0, 100),
             'current': random.randint(0, 100),
             'last': self._last}
        self._last = s['current']
        return s

class BuzzwordsSampler(DashieSampler):
    def name(self):
        return 'buzzwords'

    def sample(self):
        my_little_pony_names = ['Rainbow Dash',
                                'Blossomforth',
                                'Derpy',
                                'Fluttershy',
                                'Lofty',
                                'Scootaloo',
                                'Skydancer']
        items = [{'label': pony_name, 'value': random.randint(0, 20)} for pony_name in my_little_pony_names]
        random.shuffle(items)
        return {'items':items}

class ConvergenceSampler(DashieSampler):
    def name(self):
        return 'convergence'

    def __init__(self, *args, **kwargs):
        self.seedX = 0
        self.items = collections.deque()
        DashieSampler.__init__(self, *args, **kwargs)

    def sample(self):
        self.items.append({'x': self.seedX,
                           'y': random.randint(0,20)})
        self.seedX += 1
        if len(self.items) > 10:
            self.items.popleft()
        return {'points': list(self.items)}


class ProgressBarsSampler(DashieSampler):
    def __init__(self, *args, **kwargs):
        DashieSampler.__init__(self, *args, **kwargs)
    
    def name(self):
        return 'progress_bars'

    def sample(self):
        random_progress = []
        
        for i in range(5):
            random_progress.append({'name': "Project %d" % i, 'progress': random.randint(0, 100)})
    
        return {'title': "Progress Bars Title", 'progress_items': random_progress}


class UsageGaugeSampler(DashieSampler):
    def __init__(self, *args, **kwargs):
        DashieSampler.__init__(self, *args, **kwargs)

    def name(self):
        return 'usage_gauge'

    def sample(self):
        return {'value': random.randint(0, 100), 'max': 100}

from pyzabbix import ZabbixAPI

class ZabbixSampler(DashieSampler):
    def __init__(self, *args, **kwargs):
        self.seedX = 0
        self.items = collections.deque()
        DashieSampler.__init__(self, *args, **kwargs)

    def name(self):
        return 'zabbix'

    def sample(self):
        zapi = ZabbixAPI("http://zabbix.tonyrogers.me/zabbix/")
        zabbix.session.verify = False
        zapi.login("Admin", "zabbix")
        ret = zapi.item.get(output=['lastvalue'],filter={'host':'zabbix.tonyrogers.me'},search={'key_':'zabbix[wcache,values]'})

        self.items.append({'x': self.seedX,
                           'y': ret[0]['lastvalue']})
        self.seedX += 1
        if len(self.items) > 10:
            self.items.popleft()
        return {'points': list(self.items)}
