#!/usr/bin/env python

# quick checker for nagios status

import paramiko
from pynag.Parsers import status


def get_statusfiles(services):
    # ssh to each server in the config, grab the status.dat and put it in
    # the location specified in the config
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    for region in services.keys():
        ssh.connect(services[region]['host'],
                    username=services[region]['username'])
        ftp = ssh.open_sftp()
        ftp.get('/var/lib/icinga/status.dat', services[region]['statfile'])
        ftp.close()
        ssh.close()


def parse_status(services):
    # parse the status.dat files listed in the config
    # return the status of the servers in a hash
    for region in services.keys():
        services[region]['warning'] = 0
        services[region]['critical'] = 0
        services[region]['unknown'] = 0
        s = status(services[region]['statfile'])
        s.parse()
        for service in s.data.get('servicestatus', []):
            if (int(service.get('scheduled_downtime_depth', None)) == 0
                    and int(service.get('problem_has_been_acknowledged',
                                        None)) == 0):
                # get all the 'not OK' services
                if (int(service.get('current_state', None)) == 1):
                    services[region]['warning'] += 1
                elif (int(service.get('current_state', None)) == 2):
                    services[region]['critical'] += 1
                elif (int(service.get('current_state', None)) == 3):
                    services[region]['unknown'] += 1

    return services
