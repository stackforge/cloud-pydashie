import collections
import datetime
from contextlib import contextmanager

import nagios
from math import ceil

from dashie_sampler import DashieSampler

from novaclient.v1_1 import client as novaclient
from cinderclient.v1 import client as cinderclient
from keystoneclient.v2_0 import client as keystoneclient
from neutronclient.v2_0 import client as neutronclient


class BaseOpenstackSampler(DashieSampler):
    """docstring for ClassName"""
    def __init__(self, app, interval, conf=None, client_cache={},
                 response_cache={}):
        self._os_clients = client_cache
        self._conf = conf
        self._response_cache = response_cache
        super(BaseOpenstackSampler, self).__init__(app, interval)

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
            elif service == 'network':
                client = neutronclient.Client(
                    username=self._conf['auth']['username'],
                    password=self._conf['auth']['password'],
                    tenant_name=self._conf['auth']['project_name'],
                    auth_url=self._conf['auth']['auth_url'],
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

    @contextmanager
    def timed(self, region, service):
        start = datetime.datetime.utcnow()
        yield
        end = datetime.datetime.utcnow()
        self._api_response(int((end - start).total_seconds() * 1000),
                           region, service)

    def _api_response(self, ms, region, service):
        self._response_cache['events'].append({'region': region,
                                               'service': service,
                                               'ms': ms})


class CPUSampler(BaseOpenstackSampler):
    def __init__(self, *args, **kwargs):
        super(CPUSampler, self).__init__(*args, **kwargs)
        self._last = 0

    def name(self):
        return 'cpu'

    def sample(self):
        max_cpu = 0
        cur_cpu = 0

        for region, allocation in self._conf['allocation'].iteritems():
            nova = self._client('compute', region)
            with self.timed(region, 'compute'):
                stats = nova.hypervisors.statistics()
            with self.timed(region, 'compute'):
                hypervisors = nova.hypervisors.list()

            reserved = 0
            for hypervisor in hypervisors:
                reserved = reserved + allocation['reserved_vcpus_per_node']

            cpu_ratio = allocation['vcpus_allocation_ratio']

            max_cpu = max_cpu + (stats.vcpus * cpu_ratio) - reserved
            cur_cpu = cur_cpu + stats.vcpus_used

        s = {'min': 0,
             'max': max_cpu,
             'value': cur_cpu,
             'last': self._last}
        s['moreinfo'] = "%s out of %s" % (s['value'], s['max'])
        s['current'] = s['value']
        self._last = s['value']
        return s


class RAMSampler(BaseOpenstackSampler):
    def __init__(self, *args, **kwargs):
        super(RAMSampler, self).__init__(*args, **kwargs)
        self._last = 0

    def name(self):
        return 'ram'

    def sample(self):
        max_ram = 0
        cur_ram = 0

        for region, allocation in self._conf['allocation'].iteritems():
            nova = self._client('compute', region)
            with self.timed(region, 'compute'):
                stats = nova.hypervisors.statistics()
            with self.timed(region, 'compute'):
                hypervisors = nova.hypervisors.list()

            reserved = 0
            for hypervisor in hypervisors:
                reserved = reserved + allocation['reserved_ram_per_node']

            ram_ratio = allocation['ram_allocation_ratio']

            max_ram = (max_ram +
                       (stats.memory_mb * ram_ratio * 1024 * 1024) - reserved)
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


class IPSampler(BaseOpenstackSampler):
    def __init__(self, *args, **kwargs):
        super(IPSampler, self).__init__(*args, **kwargs)
        self._last = 0

    def name(self):
        return 'ips'

    def sample(self):
        max_ips = 0
        cur_ips = 0

        for region in self._conf['allocation'].keys():
            max_ips = (max_ips +
                       self._conf['allocation'][region]['total_floating_ips'])

            neutron = self._client('network', region)

            with self.timed(region, 'network'):
                ips = neutron.list_floatingips()
            with self.timed(region, 'network'):
                routers = neutron.list_routers()

            net_gateways = 0
            for router in routers['routers']:
                if router['external_gateway_info'] is not None:
                    net_gateways = net_gateways + 1

            cur_ips = cur_ips + len(ips['floatingips']) + net_gateways

        s = {'min': 0,
             'max': max_ips,
             'value': cur_ips,
             'last': self._last}
        s['moreinfo'] = "%s out of %s" % (cur_ips, max_ips)
        s['current'] = s['value']
        self._last = s['value']
        return s


class RegionsCPUSampler(BaseOpenstackSampler):
    def __init__(self, *args, **kwargs):
        super(RegionsCPUSampler, self).__init__(*args, **kwargs)

    def name(self):
        return 'cpu_regions'

    def sample(self):
        regions = []

        for region, allocation in self._conf['allocation'].iteritems():
            nova = self._client('compute', region)
            with self.timed(region, 'compute'):
                stats = nova.hypervisors.statistics()
            with self.timed(region, 'compute'):
                hypervisors = nova.hypervisors.list()

            reserved = 0
            for hypervisor in hypervisors:
                reserved = reserved + allocation['reserved_vcpus_per_node']

            cpu_ratio = allocation['vcpus_allocation_ratio']

            max_cpu = (stats.vcpus * cpu_ratio) - reserved
            cur_cpu = stats.vcpus_used

            regions.append({'name': region,
                            'progress': (cur_cpu * 100.0) / max_cpu,
                            'max': max_cpu, 'value': cur_cpu})

        return {'progress_items': regions}


class RegionsRAMSampler(BaseOpenstackSampler):
    def __init__(self, *args, **kwargs):
        super(RegionsRAMSampler, self).__init__(*args, **kwargs)

    def name(self):
        return 'ram_regions'

    def sample(self):
        regions = []

        for region, allocation in self._conf['allocation'].iteritems():
            nova = self._client('compute', region)
            with self.timed(region, 'compute'):
                stats = nova.hypervisors.statistics()
            with self.timed(region, 'compute'):
                hypervisors = nova.hypervisors.list()

            reserved = 0
            for hypervisor in hypervisors:
                reserved = reserved + allocation['reserved_ram_per_node']

            ram_ratio = allocation['ram_allocation_ratio']

            max_ram = (stats.memory_mb * ram_ratio * 1024 * 1024) - reserved
            cur_ram = stats.memory_mb_used * 1024 * 1024

            ram_converted = self._convert(max_ram)[0]
            ram_converted_used = self._convert(cur_ram)[0]

            regions.append({'name': region,
                            'progress': ((ram_converted_used * 100.0) /
                                         ram_converted),
                            'max': ram_converted, 'value': ram_converted_used})

        return {'progress_items': regions}


class RegionIPSampler(BaseOpenstackSampler):
    def __init__(self, *args, **kwargs):
        super(RegionIPSampler, self).__init__(*args, **kwargs)
        self._last = 0

    def name(self):
        return 'ips_regions'

    def sample(self):
        regions = []

        for region in self._conf['allocation'].keys():
            neutron = self._client('network', region)

            with self.timed(region, 'network'):
                ips = neutron.list_floatingips()
            with self.timed(region, 'network'):
                routers = neutron.list_routers()

            net_gateways = 0
            for router in routers['routers']:
                if router['external_gateway_info'] is not None:
                    net_gateways = net_gateways + 1

            cur_ips = len(ips['floatingips']) + net_gateways
            max_ips = self._conf['allocation'][region]['total_floating_ips']

            regions.append({'name': region,
                            'progress': ((cur_ips * 100.0) /
                                         max_ips),
                            'max': max_ips, 'value': cur_ips})

        return {'progress_items': regions}


class NagiosSampler(BaseOpenstackSampler):
    def __init__(self, *args, **kwargs):
        super(NagiosSampler, self).__init__(*args, **kwargs)
        self._last = 0

    def name(self):
        return 'nagios'

    def sample(self):

        try:
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
        except Exception, e:
            print e


class NagiosRegionSampler(BaseOpenstackSampler):
    def name(self):
        return 'nagios_regions'

    def sample(self):
        try:
            nagios.get_statusfiles(self._conf['services'])
            servicestatus = nagios.parse_status(self._conf['services'])

            criticals = []
            warnings = []

            for region in servicestatus:
                criticals.append({'label': region,
                                  'value': servicestatus[region]['critical']})
                warnings.append({'label': region,
                                 'value': servicestatus[region]['warning']})

            # (adriant) the following is for easy testing:
            # regions = ['region1', 'region2', 'region3']

            # criticals = []
            # warnings = []

            # for region in regions:
            #     criticals.append({'label': region, 'value': random.randint(0, 5)})
            #     warnings.append({'label': region, 'value': random.randint(0, 5)})

            return {'criticals': criticals, 'warnings': warnings}
        except Exception, e:
            print e


class ResourceSampler(BaseOpenstackSampler):

    def name(self):
        return 'resources'

    def sample(self):
        resources = {'instances': 0,
                     'routers': 0,
                     'networks': 0,
                     # 'volumes': 0,
                     # 'images': 0,
                     'vpns': 0}

        for region in self._conf['allocation'].keys():
            neutron = self._client('network', region)
            nova = self._client('compute', region)
            # cinder = self._client('storage', region)

            with self.timed(region, 'compute'):
                stats = nova.hypervisors.statistics()
            resources['instances'] = resources['instances'] + stats.running_vms

            with self.timed(region, 'network'):
                routers = neutron.list_routers()
            resources['routers'] = (resources['routers'] +
                                    len(routers['routers']))

            with self.timed(region, 'network'):
                networks = neutron.list_networks()
            resources['networks'] = (resources['networks'] +
                                     len(networks['networks']))

            with self.timed(region, 'network'):
                vpns = neutron.list_vpnservices()
            resources['vpns'] = (resources['vpns'] +
                                 len(vpns['vpnservices']))

            # volumes = cinder.volumes.list(search_opts={'all_tenants': 1})
            # resources['volumes'] = (resources['volumes'] +
            #                         len(volumes))

        items = []
        for key, value in resources.iteritems():
            items.append({'label': key, 'value': value})

        return {'items': items}


class APISampler(BaseOpenstackSampler):

    def __init__(self, *args, **kwargs):
        super(APISampler, self).__init__(*args, **kwargs)
        self._by_region = True

    def name(self):
        return 'api_response'

    def sample(self):
        while self._response_cache['events']:
            self._process_event(self._response_cache['events'].popleft())

        displayedValue = ""
        series = []

        if self._by_region:
            for region, cache in self._response_cache['regions'].iteritems():
                displayedValue += ("%s - (min: %s  max: %s  avg: %s)\n" %
                                   (region,
                                    cache['stats']['min'],
                                    cache['stats']['max'],
                                    cache['stats']['avg']))
                series.append({'name': region, 'data': list(cache['items'])})

            self._by_region = not self._by_region
            return {'displayedValue': displayedValue, 'series': series}
        else:
            for service, cache in self._response_cache['services'].iteritems():
                displayedValue += ("%s - (min: %s  max: %s  avg: %s)\n" %
                                   (service,
                                    cache['stats']['min'],
                                    cache['stats']['max'],
                                    cache['stats']['avg']))
                series.append({'name': service, 'data': list(cache['items'])})

            self._by_region = not self._by_region
            return {'displayedValue': displayedValue, 'series': series}

    def _process_event(self, event):

        region_cache = self._response_cache['regions'].get(event['region'])
        service_cache = self._response_cache['services'].get(event['service'])

        if region_cache:
            region_cache['items'].append({'x': region_cache['x'],
                                          'y': event['ms']})
        else:
            region_cache = {}
            region_cache['items'] = collections.deque()
            region_cache['x'] = 0
            region_cache['items'].append({'x': region_cache['x'],
                                          'y': event['ms']})
            self._response_cache['regions'][event['region']] = region_cache

        if service_cache:
            service_cache['items'].append({'x': service_cache['x'],
                                           'y': event['ms']})
        else:
            service_cache = {}
            service_cache['items'] = collections.deque()
            service_cache['x'] = 0
            service_cache['items'].append({'x': service_cache['x'],
                                           'y': event['ms']})
            self._response_cache['services'][event['service']] = service_cache

        region_cache['x'] += 1
        service_cache['x'] += 1

        # to stop the x value getting too high
        if region_cache['x'] == 1000000:
            # reset the x value, and adjust the items
            region_cache['x'] = 0
            for time in region_cache['items']:
                time['x'] = region_cache['x']
                region_cache['x'] += 1

        # to stop the x value getting too high
        if service_cache['x'] == 1000000:
            # reset the x value, and adjust the items
            service_cache['x'] = 0
            for time in service_cache['items']:
                time['x'] = service_cache['x']
                service_cache['x'] += 1

        if len(region_cache['items']) > 100:
            region_cache['items'].popleft()

        if len(service_cache['items']) > 100:
            service_cache['items'].popleft()

        region_stats = {'min': -1, 'max': -1, 'avg': -1}
        region_total = 0

        for time in region_cache['items']:
            region_total += time['y']
            if time['y'] > region_stats['max']:
                region_stats['max'] = time['y']
            if region_stats['min'] == -1 or time['y'] < region_stats['min']:
                region_stats['min'] = time['y']

        region_stats['avg'] = int(region_total / len(region_cache['items']))

        region_cache['stats'] = region_stats

        service_stats = {'min': -1, 'max': -1, 'avg': -1}
        service_total = 0

        for time in service_cache['items']:
            service_total += time['y']
            if time['y'] > service_stats['max']:
                service_stats['max'] = time['y']
            if service_stats['min'] == -1 or time['y'] < service_stats['min']:
                service_stats['min'] = time['y']

        service_stats['avg'] = int(service_total / len(service_cache['items']))

        service_cache['stats'] = service_stats
