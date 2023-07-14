from django.shortcuts import render
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse

import json
from datetime import datetime
from django.core import serializers
# from itertools import zip_longest
from collections import namedtuple
from .models import Services, ServiceAvailability, Systems, SystemsLogs, IServices, InternetAvailability, SystemsMetrics

services = []
systems = []
iservices = []
services_events_nlist = namedtuple('Services_events', ['check_time', 'availability'])
systems_events_nlist = namedtuple('System_events', ['realtime_timestamp', 'message'])
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
    systems_events = [SystemsLogs.objects.order_by('-id').filter(system_id=system.id, ignored=False, solved=False)[0] if SystemsLogs.objects.filter(system_id=system.id, ignored=False, solved=False) else systems_events_nlist('', '') for system in systems]
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
    datapoints = []
    datapoint_query_set_list = []
    
    systems_active_qset = Systems.objects.all().filter(enabled=1)
    # print("\nsystems_active_qset= ", systems_active_qset, "\n")
    
    for sys_item in systems_active_qset:
        datapoint_query_set_list.append(SystemsMetrics.objects.all().filter(system=sys_item.id).order_by('id')[:10])
    # print("\ndatapoint_query_set_list= ", datapoint_query_set_list[0], "\n")
    
    for i, sys_item in enumerate(datapoint_query_set_list):
        if sys_item:
            datapoints.append(json.loads(serializers.serialize('json', sys_item)))
        else:
            datapoints.append([{'model': '', 'pk': '', 'fields': {'system': systems_active_qset[i].id, 'check_time': 'No data', 'uptime': '0', 'cpu_load_1': '0', 'cpu_load_5': '0', 'cpu_load_15': '0', 'mem_used': '0', 'disk_usage': '0'}}])
    
    for i, data in enumerate(datapoints):
            for rec in data:
                #print('rec[j]=', rec)
                # rec['fields']['mem_used'] = float(rec['fields']['mem_used'])
                rec['fields']['RAM'] = systems_active_qset[i].RAM
                rec['fields']['system_name'] = systems_active_qset[i].system_name

    # print('\ndatapoints= ', datapoints, '\n')
        
    context = {
        "services_info_list": services_info_list,
        "systems_info_list": systems_info_list,
        "iservices_info_list": iservices_info_list,
        "systems_metrics_list": systems_metrics_list,
        "datapoints": datapoints,
    }

    #return render(request, 'monitor/monitor-index.html', {'context': context, 'datapoints': datapoints})
    return render(request, 'monitor/monitor-index.html', context=context)

def solve(request: HttpRequest, id):
  SystemsLogs.objects.filter(id=id).update(solved=True)
  return HttpResponseRedirect(reverse('monitor:index'))

def ignore(request: HttpRequest, id):
  SystemsLogs.objects.filter(id=id).update(ignored=True)
  return HttpResponseRedirect(reverse('monitor:index'))

def line_chart(request):
    
    datapoint_query_set = SystemsMetrics.objects.all().order_by('id')[:6
    ]
    # systems_id = SystemsMetrics.objects.order_by().values('system').distinct()
    
    for data in datapoint_query_set:
        data.check_time = int(datetime.timestamp(datetime.strptime(data.check_time, "%d-%m-%Y %H:%M:%S"))) * 1000
        data.mem_used = int(data.mem_used)
 
    datapoints = serializers.serialize('json', datapoint_query_set)
    # print('datapoints= ', datapoints)
    # print('datapoint_query_set= ', datapoint_query_set[0].system_id)
    # print('systems_id= ', systems_id)
    # print("systems_id[0]['system']= ", systems_id[0]['system'])
    return render(request, "monitor/line_chart.html", { "datapoints": datapoints })
    # return render(request, 'monitor/line_chart.html', { "user_data_2021": user_data_2021, "user_data_2020": user_data_2020 })

def chartjs(request):
    datapoints = []
    datapoint_query_set_list = []
    
    systems_active_qset = Systems.objects.all().filter(enabled=1)
    # print("\nsystems_active_qset= ", systems_active_qset, "\n")
    
    for sys_item in systems_active_qset:
        datapoint_query_set_list.append(SystemsMetrics.objects.all().filter(system=sys_item.id).order_by('id')[:10])
    # print("\ndatapoint_query_set_list= ", datapoint_query_set_list[0], "\n")
    
    for i, sys_item in enumerate(datapoint_query_set_list):
        if sys_item:
            datapoints.append(json.loads(serializers.serialize('json', sys_item)))
        else:
            datapoints.append([{'model': '', 'pk': '', 'fields': {'system': systems_active_qset[i].id, 'check_time': 'No data', 'uptime': '0', 'cpu_load_1': '0', 'cpu_load_5': '0', 'cpu_load_15': '0', 'mem_used': '0', 'disk_usage': '0'}}])
    
    for i, data in enumerate(datapoints):
            for rec in data:
                #print('rec[j]=', rec)
                # rec['fields']['mem_used'] = float(rec['fields']['mem_used'])
                rec['fields']['RAM'] = systems_active_qset[i].RAM
                rec['fields']['system_name'] = systems_active_qset[i].system_name

    # print('\ndatapoints= ', datapoints, '\n')
        
    context = {
        "datapoints": datapoints,
    }
    return render(request, 'monitor/chartjs.html', context=context)