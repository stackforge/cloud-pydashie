import collections
import random
import nagios

from dashie_sampler import DashieSampler


class CPUSampler(DashieSampler):
    def __init__(self, *args, **kwargs):
        super(CPUSampler, self).__init__(*args, **kwargs)
        self._last = 0

    def name(self):
        return 'cpu'

    def sample(self):
        max_cpu = 0
        cur_cpu = 0

        for region in self._conf['regions']:
            nova = self._client('compute', region)
            stats = nova.hypervisors.statistics()
            hypervisors = nova.hypervisors.list()

            reserved = 0
            for hypervisor in hypervisors:
                reserved = reserved + self._conf['allocation'][region]['reserved_vcpus_per_node']

            cpu_ratio = self._conf['allocation'][region]['vcpus_allocation_ratio']

            max_cpu = max_cpu + (stats.vcpus * cpu_ratio) - reserved
            cur_cpu = cur_cpu + stats.vcpus_used

        s = {'min': 0,
             'max': max_cpu,
             'value': cur_cpu,
             'last': self._last}
        s['moreinfo'] = "%s/%s" % (s['value'], s['max'])
        s['current'] = s['value']
        self._last = s['value']
        return s


class RAMSampler(DashieSampler):
    def __init__(self, *args, **kwargs):
        super(RAMSampler, self).__init__(*args, **kwargs)
        self._last = 0

    def name(self):
        return 'ram'

    def sample(self):
        max_ram = 0
        cur_ram = 0

        for region in self._conf['regions']:
            nova = self._client('compute', region)
            stats = nova.hypervisors.statistics()
            hypervisors = nova.hypervisors.list()

            reserved = 0
            for hypervisor in hypervisors:
                reserved = reserved + self._conf['allocation'][region]['reserved_ram_per_node']

            ram_ratio = self._conf['allocation'][region]['ram_allocation_ratio']

            max_ram = max_ram + (stats.memory_mb * ram_ratio * 1024 * 1024) - reserved
            cur_ram = cur_ram + stats.memory_mb_used * 1024 * 1024

        ram_converted = self._convert(max_ram)
        ram_converted_used = self._convert(cur_ram)

        s = {'min': 0,
             'max': ram_converted[0],
             'value': ram_converted_used[0],
             'last': self._last}
        s['moreinfo'] = "%s%s out of %s%s" % (ram_converted_used[0],
                                              ram_converted_used[1],
                                              ram_converted[0],
                                              ram_converted[1])
        s['current'] = s['value']
        self._last = s['value']
        return s


class RegionsCPUSampler(DashieSampler):
    def __init__(self, *args, **kwargs):
        super(RegionsCPUSampler, self).__init__(*args, **kwargs)

    def name(self):
        return 'cpu_regions'

    def sample(self):
        regions = []

        for region in self._conf['regions']:
            nova = self._client('compute', region)
            stats = nova.hypervisors.statistics()
            hypervisors = nova.hypervisors.list()

            reserved = 0
            for hypervisor in hypervisors:
                reserved = reserved + self._conf['allocation'][region]['reserved_vcpus_per_node']

            cpu_ratio = self._conf['allocation'][region]['vcpus_allocation_ratio']

            max_cpu = (stats.vcpus * cpu_ratio) - reserved
            cur_cpu = stats.vcpus_used

            regions.append({'name': region, 'progress': (cur_cpu * 100.0) / max_cpu,
                            'max': max_cpu, 'value': cur_cpu})

        return {'progress_items': regions}


class RegionsRAMSampler(DashieSampler):
    def __init__(self, *args, **kwargs):
        super(RegionsRAMSampler, self).__init__(*args, **kwargs)

    def name(self):
        return 'ram_regions'

    def sample(self):
        regions = []

        for region in self._conf['regions']:
            nova = self._client('compute', region)
            stats = nova.hypervisors.statistics()
            hypervisors = nova.hypervisors.list()

            reserved = 0
            for hypervisor in hypervisors:
                reserved = reserved + self._conf['allocation'][region]['reserved_ram_per_node']

            ram_ratio = self._conf['allocation'][region]['ram_allocation_ratio']

            max_ram = (stats.memory_mb * ram_ratio * 1024 * 1024) - reserved
            cur_ram = stats.memory_mb_used * 1024 * 1024

            ram_converted = self._convert(max_ram)[0]
            ram_converted_used = self._convert(cur_ram)[0]

            regions.append({'name': region,
                            'progress': ((ram_converted_used * 100.0) /
                                         ram_converted),
                            'max': ram_converted, 'value': ram_converted_used})

        return {'progress_items': regions}


class NagiosSampler(DashieSampler):
    def __init__(self, *args, **kwargs):
        super(NagiosSampler, self).__init__(*args, **kwargs)
        self._last = 0

    def name(self):
        return 'nagios'

    def sample(self):

        nagios.get_statusfiles(self._conf['services'])
        servicestatus = nagios.parse_status(self._conf['services'])

        criticals = 0
        warnings = 0

        for region in servicestatus:
            criticals = criticals + servicestatus[region]['critical']
            warnings = warnings + servicestatus[region]['warning']

        status = 'green'

        if criticals > 0:
            status = 'red'
        elif warnings > 0:
            status = 'yellow'

        s = {'criticals': criticals,
             'warnings': warnings,
             'status': status}
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


class UsageGaugeSampler(DashieSampler):
    def __init__(self, *args, **kwargs):
        super(UsageGaugeSampler, self).__init__(*args, **kwargs)

    def name(self):
        return 'usage_gauge'

    def sample(self):
        return {'value': random.randint(0, 100), 'max': 100}
