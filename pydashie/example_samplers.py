import collections
import random

from dashie_sampler import DashieSampler


class SynergySampler(DashieSampler):
    def __init__(self, *args, **kwargs):
        super(SynergySampler, self).__init__(*args, **kwargs)
        self._last = 0

    def name(self):
        return 'synergy'

    def sample(self):
        s = {'min': 0,
             'max': 100,
             'value': random.randint(0, 100),
             'last': self._last}
        s['moreinfo'] = "%s/%s" % (s['value'], s['max'])
        s['current'] = s['value']
        self._last = s['value']
        return s


class HotnessSampler(DashieSampler):
    def __init__(self, *args, **kwargs):
        super(HotnessSampler, self).__init__(*args, **kwargs)
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
        return {'items': items}


class ConvergenceSampler(DashieSampler):
    def name(self):
        return 'convergence'

    def __init__(self, *args, **kwargs):
        self.seedX = 0
        self.items = collections.deque()
        super(ConvergenceSampler, self).__init__(*args, **kwargs)

    def sample(self):
        self.items.append({'x': self.seedX,
                           'y': random.randint(0, 20)})
        self.seedX += 1
        if len(self.items) > 10:
            self.items.popleft()

        return {'points': list(self.items)}


class ProgressBarsSampler(DashieSampler):
    def __init__(self, *args, **kwargs):
        super(ProgressBarsSampler, self).__init__(*args, **kwargs)

    def name(self):
        return 'progress_bars'

    def sample(self):
        random_progress = []

        for i in range(5):
            random_progress.append({'name': "Project %d" % i, 'progress': random.randint(0, 100)})

        return {'title': "Progress Bars Title", 'progress_items': random_progress}


class UsageGaugeSampler(DashieSampler):
    def __init__(self, *args, **kwargs):
        super(UsageGaugeSampler, self).__init__(*args, **kwargs)

    def name(self):
        return 'usage_gauge'

    def sample(self):
        return {'value': random.randint(0, 100), 'max': 100}
