from django.shortcuts import render
from django.http import HttpRequest
# from itertools import zip_longest
from collections import namedtuple
from .models import Services, ServiceAvailability, Systems, SystemsLogs, IServices, InternetAvailability, SystemsMetrics

services = []
systems = []
iservices = []
services_events_nlist = namedtuple('Services_events', ['check_time', 'availability'])
systems_events_nlist = namedtuple('System_events', ['hostname', 'realtime_timestamp'])
systems_metrics_nlist = namedtuple('System_metrics', ['check_time', 'uptime', 'cpu_load_1', 'cpu_load_5', 'cpu_load_15', 'mem_used', 'disk_usage'])
iservices_events_nlist = namedtuple('IServices_events', ['check_time', 'availability', 'packet_loss_rate', 'rtt_min', 'rtt_max'])

def monitor_index(request: HttpRequest):
    global services
    global systems
    global iservices
    global services_events_nlist
    global systems_events_nlist
    global iservices_events_nlist
    global systems_metrics_nlist
    if not services:
        services = Services.objects.all().filter(enabled=1)
        # print(services)
        # print(len(services))
    if not systems:
        systems = Systems.objects.all().filter(enabled=1)
        # print(systems)
        # print(len(systems))
    if not iservices:
        iservices = IServices.objects.all().filter(enabled=1)
        # print(systems)
        # print(len(systems))
    service_events = [ServiceAvailability.objects.order_by('-id').filter(service_id=srv.id)[0] if ServiceAvailability.objects.filter(service_id=srv.id) else services_events_nlist('', '') for srv in services]
    services_info_list = zip(services, service_events)
    systems_events = [SystemsLogs.objects.order_by('-id').filter(system_id=system.id)[0] if SystemsLogs.objects.filter(system_id=system.id) else systems_events_nlist('', '') for system in systems]
    systems_info_list = zip(systems, systems_events)
    systems_metrics = [SystemsMetrics.objects.order_by('-id').filter(system_id=system.id)[0] if SystemsMetrics.objects.filter(system_id=system.id) else systems_metrics_nlist('', '', '', '', '', '', '') for system in systems]
    systems_metrics_list = zip(systems, systems_metrics)
    iservices_events = [InternetAvailability.objects.order_by('-id').filter(iservice_id=iservice.id)[0] if InternetAvailability.objects.filter(iservice_id=iservice.id) else iservices_events_nlist('', '', '', '', '') for iservice in iservices]
    iservices_info_list = zip(iservices, iservices_events)

    # print('systems_events= ', systems_events)
    # print('systems_info_list= ', systems_info_list)
    # print('iservices_events_nlist= ', iservices_events_nlist)
    # print('services_info_list_elements= ', list(services_info_list))
    # print('systems_info_list_elements= ', list(systems_info_list))
    context = {
        "services_info_list": services_info_list,
        "systems_info_list": systems_info_list,
        "iservices_info_list": iservices_info_list,
        "systems_metrics_list": systems_metrics_list,
    }
    return render(request, 'monitor/monitor-index.html', context=context)