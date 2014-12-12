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
        s['moreinfo'] = "%s out of %s" % (s['value'], s['max'])
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


class IPSampler(DashieSampler):
    def __init__(self, *args, **kwargs):
        super(IPSampler, self).__init__(*args, **kwargs)
        self._last = 0

    def name(self):
        return 'ips'

    def sample(self):
        max_ips = 0
        cur_ips = 0

        for region in self._conf['regions']:
            max_ips = (max_ips +
                       self._conf['allocation'][region]['total_floating_ips'])

            neutron = self._client('network', region)

            ips = neutron.list_floatingips()
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


class RegionIPSampler(DashieSampler):
    def __init__(self, *args, **kwargs):
        super(RegionIPSampler, self).__init__(*args, **kwargs)
        self._last = 0

    def name(self):
        return 'ips_regions'

    def sample(self):
        regions = []

        for region in self._conf['regions']:
            neutron = self._client('network', region)

            ips = neutron.list_floatingips()
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


class NagiosRegionSampler(DashieSampler):
    def name(self):
        return 'nagios_regions'

    def sample(self):
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


class ResourceSampler(DashieSampler):
    def name(self):
        return 'resources'

    def sample(self):
        resources = {'instances': 0,
                     'routers': 0,
                     'networks': 0,
                     # 'volumes': 0,
                     # 'images': 0,
                     'vpns': 0}

        for region in self._conf['regions']:
            neutron = self._client('network', region)
            nova = self._client('compute', region)
            # cinder = self._client('storage', region)

            stats = nova.hypervisors.statistics()
            resources['instances'] = resources['instances'] + stats.running_vms

            routers = neutron.list_routers()
            resources['routers'] = (resources['routers'] +
                                    len(routers['routers']))

            networks = neutron.list_networks()
            resources['networks'] = (resources['networks'] +
                                     len(networks['networks']))

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
