from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout

import json
from datetime import datetime, timedelta
# from dateutil.relativedelta import timedelta
from django.core import serializers
# from itertools import zip_longest
from collections import namedtuple
from .models import Services, ServiceAvailability, Systems, SystemsLogs, IServices, InternetAvailability, SystemsMetrics
from .forms import SelectDateForm

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
    if services: 
        services_info_list = zip(services, service_events)
    else:
        services_info_list = []
    
    if systems:
        systems_events = [SystemsLogs.objects.order_by('-id').filter(system_id=system.id, ignored=False, solved=False)[0] if SystemsLogs.objects.filter(system_id=system.id, ignored=False, solved=False) else systems_events_nlist('', '') for system in systems]
        systems_info_list = zip(systems, systems_events)
        systems_metrics = [SystemsMetrics.objects.order_by('-id').filter(system_id=system.id)[0] if SystemsMetrics.objects.filter(system_id=system.id) else systems_metrics_nlist('', '', '', '', '', '', '') for system in systems]
        systems_metrics_list = zip(systems, systems_metrics)
    else:
        systems_info_list = []
        systems_metrics_list = []
    
    if iservices:
        iservices_events = [InternetAvailability.objects.order_by('-id').filter(iservice_id=iservice.id)[0] if InternetAvailability.objects.filter(iservice_id=iservice.id) else iservices_events_nlist('', '', '', '', '') for iservice in iservices]
        iservices_info_list = zip(iservices, iservices_events)
    else:
        iservices_info_list = []

    # print('systems_events= ', systems_events)
    # print('systems_info_list= ', systems_info_list)
    # print('iservices_events_nlist= ', iservices_events_nlist)
    # print('services_info_list_elements= ', list(services_info_list))
    # print('systems_info_list_elements= ', list(systems_info_list))
    datapoints_metrics = []
    datapoints_internet_check = []
    datapoints_service_check = []
    datapoints_service_check_query_set_list = []
    datapoints_metrics_query_set_list = []
    datapoints_internet_check_query_set_list = []
    
    # month_now = datetime.strftime(datetime.now().replace(microsecond=0), '%Y-%m-%d %H:%M:%S')
    # date_before_month = datetime.now() - relativedelta(months=1)
    # date_before_week = datetime.now() - relativedelta(weeks=1)
    # date_last_3_days = datetime.now() - timedelta(days=3)
    date_last_day = datetime.now() - timedelta(days=1)
    date_dashboard = date_last_day
    # print('Today: ',datetime.now().replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S'))
    # print('After Month:', date_before_month.replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S'))
    # print('\nmonth_now: ', month_now, '\n')
    # Get active systems
    # systems_active_qset = Systems.objects.all().filter(enabled=1)
    # print("\nsystems_active_qset= ", systems_active_qset, "\n")
    
    # Get all internet check events
    for isrc_item in iservices:
        datapoints_internet_check_query_set_list.append(InternetAvailability.objects.all().filter(iservice=isrc_item.id, check_time__gte=date_dashboard).order_by('-id')[::-1])
        # datapoints_internet_check_query_set_list.append(InternetAvailability.objects.all().filter(iservice=isrc_item.id, check_time__gte=date_before_month).order_by('-id')[:100][::-1])

    # Prepare internet check events for charts
    for i, isrc_item in enumerate(datapoints_internet_check_query_set_list):
        if isrc_item:
            # print("\nisrc_item= ", isrc_item, "\n")
            datapoints_internet_check.append(json.loads(serializers.serialize('json', isrc_item)))
        else:
            datapoints_internet_check.append([{'model': '', 'pk': '', 'fields': {'iservice': iservices[i].id, 'check_time': 'No data', 'availability': '0', 'destination': 'No data', 'packet_transmit': 'No data', 'packet_receive': 'No data', 'packet_loss_count': 'No data', 'packet_loss_rate': 'No data', 'rtt_min': 'No data', 'rtt_avg': 'No data', 'rtt_max': 'No data', 'rtt_mdev': 'No data', 'packet_duplicate_count': 'No data', 'packet_duplicate_rate': 'No data'}}])
    # print("\ndatapoints_internet_check= ", datapoints_internet_check, "\n")
    for i, data in enumerate(datapoints_internet_check):
            for rec in data:
                if rec['fields']['availability']: 
                    rec['fields']['availability'] = 1
                else:
                    rec['fields']['availability'] = 0
                    rec['fields']['rtt_min'] = 'No data'
                    rec['fields']['rtt_avg'] = 'No data'
                    rec['fields']['rtt_max'] = 'No data'
                    rec['fields']['rtt_mdev'] = 'No data'
                    rec['fields']['packet_duplicate_rate'] = 'No data'
                rec['fields']['service_name'] = iservices[i].service_name

    # Get all systems metrics
    for sys_item in systems:
        datapoints_metrics_query_set_list.append(SystemsMetrics.objects.all().filter(system=sys_item.id, check_time__gte=date_dashboard).order_by('-id')[::-1])
        # datapoints_metrics_query_set_list.append(SystemsMetrics.objects.all().filter(system=sys_item.id).order_by('-id')[:10][::-1])
    # print("\ndatapoint_query_set_list= ", datapoint_query_set_list[0], "\n")

    # Prepare metrics data for charts
    for i, sys_item in enumerate(datapoints_metrics_query_set_list):
        if sys_item:
            datapoints_metrics.append(json.loads(serializers.serialize('json', sys_item)))
        else:
            datapoints_metrics.append([{'model': '', 'pk': '', 'fields': {'system': systems[i].id, 'check_time': 'No data', 'uptime': '0', 'cpu_load_1': '0', 'cpu_load_5': '0', 'cpu_load_15': '0', 'mem_used': '0', 'disk_usage': '0'}}])
    
    for i, data in enumerate(datapoints_metrics):
            for rec in data:
                #print('rec[j]=', rec)
                # rec['fields']['mem_used'] = float(rec['fields']['mem_used'])
                rec['fields']['RAM'] = systems[i].RAM
                rec['fields']['HDD'] = systems[i].HDD
                rec['fields']['CPU_cores'] = systems[i].CPU_cores
                rec['fields']['system_name'] = systems[i].system_name

    # print('\ndatapoints= ', datapoints, '\n')
    # print('\nservices_info_list= ', services_info_list, '\n')

    # Get all service availability check events
    for src_item in services:
        datapoints_service_check_query_set_list.append(ServiceAvailability.objects.all().filter(service=src_item.id, check_time__gte=date_dashboard).order_by('-id')[::-1])
        # datapoints_service_check_query_set_list.append(ServiceAvailability.objects.all().filter(service=src_item.id,).order_by('-id')[:10][::-1])

    # Prepare internet check events for charts
    for i, src_item in enumerate(datapoints_service_check_query_set_list):
        if src_item:
            datapoints_service_check.append(json.loads(serializers.serialize('json', src_item)))
        else:
            datapoints_service_check.append([{'model': '', 'pk': '', 'fields': {'service': services[i].id, 'check_time': 'No data', 'availability': '0'}}])
    
    for i, data in enumerate(datapoints_service_check):
        for rec in data:
            if rec['fields']['availability']: 
                rec['fields']['availability'] = 1
            else:
                rec['fields']['availability'] = 0
            rec['fields']['service_name'] = services[i].service_name

    context = {
        "services_info_list": services_info_list,
        "systems_info_list": systems_info_list,
        "iservices_info_list": iservices_info_list,
        "systems_metrics_list": systems_metrics_list,
        "datapoints_metrics": datapoints_metrics,
        "datapoints_internet_check": datapoints_internet_check,
        "datapoints_service_check": datapoints_service_check,
    }

    #return render(request, 'monitor/monitor-index.html', {'context': context, 'datapoints': datapoints})
    return render(request, 'monitor/monitor-index.html', context=context)

def solve(request: HttpRequest, id):
  SystemsLogs.objects.filter(id=id).update(solved=True)
  return HttpResponseRedirect(reverse('monitor:index'))

def ignore(request: HttpRequest, id):
  SystemsLogs.objects.filter(id=id).update(ignored=True)
  return HttpResponseRedirect(reverse('monitor:index'))

def setdate(request: HttpRequest, imstart, imstop):
  # print('\nstart_date= ', imstart)
  # print('\nstop_date= ', imstop)
  # SystemsLogs.objects.filter(id=id).update(ignored=True)
  return HttpResponseRedirect(reverse('monitor:charts'))


def charts(request: HttpRequest):
    global services
    global systems
    global iservices
    global services_events_nlist
    global systems_events_nlist
    global iservices_events_nlist
    global systems_metrics_nlist
    
    '''if request.method == "POST":
        form = SelectDateForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data["start_date"]
            end_date = form.cleaned_data["end_date"]
            print("\nstart_date", start_date)
            print("\nend_date", end_date)'''
    date_last_3_days = datetime.now() - timedelta(days=3)
    start_date_default = (date_last_3_days).replace(microsecond=0).strftime('%Y-%m-%d')
    
    if request.GET.get("all_start_date") and request.GET.get("all_end_date"):
        # print('Selected All Request')
        # print('\nrequest.GET.get("all_end_date"): ', request.GET.get("all_end_date"))
        all_start_date = request.GET.get("all_start_date", start_date_default)
        all_end_date = request.GET.get("all_end_date", datetime.now().replace(microsecond=0).strftime('%Y-%m-%d'))
        all_start_time = request.GET.get("all_start_time", "00:00:00")
        all_end_time = request.GET.get("all_end_time", "23:59:00")
        all_start_datetime = all_start_date + " " + all_start_time
        all_end_datetime = all_end_date + " " + all_end_time
        all_start_datetime_object = datetime.strptime(all_start_datetime, '%Y-%m-%d %H:%M:%S')
        all_end_datetime_object = datetime.strptime(all_end_datetime, '%Y-%m-%d %H:%M:%S')
        im_start_datetime_object = sm_start_datetime_object = sys_start_datetime_object = all_start_datetime_object
        im_end_datetime_object = sm_end_datetime_object = sys_end_datetime_object = all_end_datetime_object
    else:
        # print('Selected Single Request')
        im_start_date = request.GET.get("im_start_date", start_date_default)
        im_end_date = request.GET.get("im_end_date", datetime.now().replace(microsecond=0).strftime('%Y-%m-%d'))
        im_start_time = request.GET.get("im_start_time", "00:00:00")
        im_end_time = request.GET.get("im_end_time", "23:59:00")
        im_start_datetime = im_start_date + " " + im_start_time
        im_end_datetime = im_end_date + " " + im_end_time

        # print("\nim_start_date", im_start_date)
        # print("\nim_end_date", im_end_date)
        # print("\nim_start_time: ", im_start_time)
        # print("\nim_end_time: ", im_end_time)
        # print("\nim_start_datetime: ", im_start_datetime)
        # print("\nim_end_datetime: ", im_end_datetime)
        im_start_datetime_object = datetime.strptime(im_start_datetime, '%Y-%m-%d %H:%M:%S')
        im_end_datetime_object = datetime.strptime(im_end_datetime, '%Y-%m-%d %H:%M:%S')

        sm_start_date = request.GET.get("sm_start_date", start_date_default)
        sm_end_date = request.GET.get("sm_end_date", datetime.now().replace(microsecond=0).strftime('%Y-%m-%d'))
        sm_start_time = request.GET.get("sm_start_time", "00:00:00")
        sm_end_time = request.GET.get("sm_end_time", "23:59:00")
        sm_start_datetime = sm_start_date + " " + sm_start_time
        sm_end_datetime = sm_end_date + " " + sm_end_time
        sm_start_datetime_object = datetime.strptime(sm_start_datetime, '%Y-%m-%d %H:%M:%S')
        sm_end_datetime_object = datetime.strptime(sm_end_datetime, '%Y-%m-%d %H:%M:%S')

        sys_start_date = request.GET.get("sys_start_date", start_date_default)
        sys_end_date = request.GET.get("sys_end_date", datetime.now().replace(microsecond=0).strftime('%Y-%m-%d'))
        sys_start_time = request.GET.get("sys_start_time", "00:00:00")
        sys_end_time = request.GET.get("sys_end_time", "23:59:00")
        sys_start_datetime = sys_start_date + " " + sys_start_time
        sys_end_datetime = sys_end_date + " " + sys_end_time
        sys_start_datetime_object = datetime.strptime(sys_start_datetime, '%Y-%m-%d %H:%M:%S')
        sys_end_datetime_object = datetime.strptime(sys_end_datetime, '%Y-%m-%d %H:%M:%S')

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
    if services: 
        services_info_list = zip(services, service_events)
    else:
        services_info_list = []
    
    if systems:
        systems_events = [SystemsLogs.objects.order_by('-id').filter(system_id=system.id, ignored=False, solved=False)[0] if SystemsLogs.objects.filter(system_id=system.id, ignored=False, solved=False) else systems_events_nlist('', '') for system in systems]
        systems_info_list = zip(systems, systems_events)
        systems_metrics = [SystemsMetrics.objects.order_by('-id').filter(system_id=system.id)[0] if SystemsMetrics.objects.filter(system_id=system.id) else systems_metrics_nlist('', '', '', '', '', '', '') for system in systems]
        systems_metrics_list = zip(systems, systems_metrics)
    else:
        systems_info_list = []
        systems_metrics_list = []
    
    if iservices:
        iservices_events = [InternetAvailability.objects.order_by('-id').filter(iservice_id=iservice.id)[0] if InternetAvailability.objects.filter(iservice_id=iservice.id) else iservices_events_nlist('', '', '', '', '') for iservice in iservices]
        iservices_info_list = zip(iservices, iservices_events)
    else:
        iservices_info_list = []

    datapoints_metrics = []
    datapoints_internet_check = []
    datapoints_service_check = []
    datapoints_service_check_query_set_list = []
    datapoints_metrics_query_set_list = []
    datapoints_internet_check_query_set_list = []
    
    # month_now = datetime.strftime(datetime.now().replace(microsecond=0), '%Y-%m-%d %H:%M:%S')
    # date_before_month = datetime.now() - timedelta(months=1)
    # date_before_week = datetime.now() - timedelta(weeks=1)
    # print('Today: ',datetime.now().replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S'))
    # print('After Month:', date_before_month.replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S'))
    # print('\nmonth_now: ', month_now, '\n')
    # print("\nsystems_active_qset= ", systems_active_qset, "\n")
    
    # Get all internet check events
    for isrc_item in iservices:
        datapoints_internet_check_query_set_list.append(InternetAvailability.objects.all().filter(iservice=isrc_item.id, check_time__gte=im_start_datetime_object, check_time__lte=im_end_datetime_object).order_by('-id')[::-1])
        # datapoints_internet_check_query_set_list.append(InternetAvailability.objects.all().filter(iservice=isrc_item.id, check_time__gte=date_before_month).order_by('-id')[:100][::-1])

    # Prepare internet check events for charts
    for i, isrc_item in enumerate(datapoints_internet_check_query_set_list):
        if isrc_item:
            # print("\nisrc_item= ", isrc_item, "\n")
            datapoints_internet_check.append(json.loads(serializers.serialize('json', isrc_item)))
        else:
            datapoints_internet_check.append([{'model': '', 'pk': '', 'fields': {'iservice': iservices[i].id, 'check_time': 'No data', 'availability': '0', 'destination': 'No data', 'packet_transmit': 'No data', 'packet_receive': 'No data', 'packet_loss_count': 'No data', 'packet_loss_rate': 'No data', 'rtt_min': 'No data', 'rtt_avg': 'No data', 'rtt_max': 'No data', 'rtt_mdev': 'No data', 'packet_duplicate_count': 'No data', 'packet_duplicate_rate': 'No data'}}])
    # print("\ndatapoints_internet_check= ", datapoints_internet_check, "\n")
    for i, data in enumerate(datapoints_internet_check):
            for rec in data:
                if rec['fields']['availability']: 
                    rec['fields']['availability'] = 1
                else:
                    rec['fields']['availability'] = 0
                    rec['fields']['rtt_min'] = 'No data'
                    rec['fields']['rtt_avg'] = 'No data'
                    rec['fields']['rtt_max'] = 'No data'
                    rec['fields']['rtt_mdev'] = 'No data'
                    rec['fields']['packet_duplicate_rate'] = 'No data'
                rec['fields']['service_name'] = iservices[i].service_name

    # Get all systems metrics
    for sys_item in systems:
        datapoints_metrics_query_set_list.append(SystemsMetrics.objects.all().filter(system=sys_item.id, check_time__gte=sys_start_datetime_object, check_time__lte=sys_end_datetime_object).order_by('-id')[::-1])
        # datapoints_metrics_query_set_list.append(SystemsMetrics.objects.all().filter(system=sys_item.id).order_by('-id')[:10][::-1])
    # print("\ndatapoint_query_set_list= ", datapoint_query_set_list[0], "\n")

    # Prepare metrics data for charts
    for i, sys_item in enumerate(datapoints_metrics_query_set_list):
        if sys_item:
            datapoints_metrics.append(json.loads(serializers.serialize('json', sys_item)))
        else:
            datapoints_metrics.append([{'model': '', 'pk': '', 'fields': {'system': systems[i].id, 'check_time': 'No data', 'uptime': '0', 'cpu_load_1': '0', 'cpu_load_5': '0', 'cpu_load_15': '0', 'mem_used': '0', 'disk_usage': '0'}}])
    
    for i, data in enumerate(datapoints_metrics):
            for rec in data:
                #print('rec[j]=', rec)
                # rec['fields']['mem_used'] = float(rec['fields']['mem_used'])
                rec['fields']['RAM'] = systems[i].RAM
                rec['fields']['HDD'] = systems[i].HDD
                rec['fields']['CPU_cores'] = systems[i].CPU_cores
                rec['fields']['system_name'] = systems[i].system_name

    # print('\ndatapoints= ', datapoints, '\n')
    # print('\nservices_info_list= ', services_info_list, '\n')

    # Get all service availability check events
    for src_item in services:
        datapoints_service_check_query_set_list.append(ServiceAvailability.objects.all().filter(service=src_item.id,  check_time__gte=sm_start_datetime_object, check_time__lte=sm_end_datetime_object).order_by('-id')[::-1])
        # datapoints_service_check_query_set_list.append(ServiceAvailability.objects.all().filter(service=src_item.id,).order_by('-id')[:10][::-1])

    # Prepare internet check events for charts
    for i, src_item in enumerate(datapoints_service_check_query_set_list):
        if src_item:
            datapoints_service_check.append(json.loads(serializers.serialize('json', src_item)))
        else:
            datapoints_service_check.append([{'model': '', 'pk': '', 'fields': {'service': services[i].id, 'check_time': 'No data', 'availability': '0'}}])
    
    for i, data in enumerate(datapoints_service_check):
        for rec in data:
            if rec['fields']['availability']: 
                rec['fields']['availability'] = 1
            else:
                rec['fields']['availability'] = 0
            rec['fields']['service_name'] = services[i].service_name

    context = {
        "services_info_list": services_info_list,
        "systems_info_list": systems_info_list,
        "iservices_info_list": iservices_info_list,
        "systems_metrics_list": systems_metrics_list,
        "datapoints_metrics": datapoints_metrics,
        "datapoints_internet_check": datapoints_internet_check,
        "datapoints_service_check": datapoints_service_check,
        "form": SelectDateForm(),
        "im_start_datetime_object": im_start_datetime_object.strftime("%d-%m-%Y, %H:%M:%S"),
        "im_end_datetime_object": im_end_datetime_object.strftime("%d-%m-%Y, %H:%M:%S"),
        "sm_start_datetime_object": sm_start_datetime_object.strftime("%d-%m-%Y, %H:%M:%S"),
        "sm_end_datetime_object": sm_end_datetime_object.strftime("%d-%m-%Y, %H:%M:%S"),
        "sys_start_datetime_object": sys_start_datetime_object.strftime("%d-%m-%Y, %H:%M:%S"),
        "sys_end_datetime_object": sys_end_datetime_object.strftime("%d-%m-%Y, %H:%M:%S"),
    }

    #return render(request, 'monitor/monitor-index.html', {'context': context, 'datapoints': datapoints})
    return render(request, 'monitor/charts.html', context=context)

def login_view(request: HttpRequest):
    if request.method == "GET":
        if request.user.is_authenticated:
            return redirect("/monitor/")
        
        return render(request, "monitor/login.html")
    username = request.POST["username"]
    password = request.POST["password"]

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return redirect("/monitor")

    return render(request, "monitor/login.html", {"error": "Invalid login credentials"})

def logout_view(request: HttpRequest):
    logout(request)
    return redirect(reverse("monitor:login"))

def set_cookie_view(request: HttpRequest):
    response = HttpResponse("Cookie set")
    response.set_cookie("fizz", "buzz", max_age=3600)
    response.set_cookie("PING", "PONG", max_age=60)
    return response

def get_cookie_view(request: HttpRequest):
    value = request.COOKIES.get("fizz", "default value")
    return HttpResponse(f"Cookie value: {value!r}")

def set_session_view(request: HttpRequest):
    value = request.session["foobar"] ="spameggs"
    return HttpResponse("Session set!")

def get_session_view(request: HttpRequest):
    value = request.session.get("foobar", "default")
    return HttpResponse(f"Session value: {value!r}")
