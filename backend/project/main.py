import asyncio
import argparse
import datetime
import yaml
import os
import re
import time
import db_query
from icmp_check import ping_ip_addresses
from initialization import initialization
from send_cmd_to_systems import send_commands_to_devices
from service_check import check_web_service


parser = argparse.ArgumentParser(description="Webmonitor backend")
parser.add_argument("-ci", dest="check_interval_internet", default=0, type=int)
parser.add_argument("-cs", dest="check_interval_services", default=0, type=int)
parser.add_argument("-cm", dest="check_interval_metrics", default=0, type=int)
parser.add_argument("-cj", dest="check_interval_journals", default=0, type=int)
args = parser.parse_args()


def main(iservices_all_list, 
        iservices_active_IPs, 
        systems_all_list, 
        active_systems_list_of_dicts,
        services_result_list, 
        db, 
        check_interval_internet=30,
        check_interval_serivces=30,
        check_interval_metrics=30,
        check_interval_journals=30
        ):
    # print("systems_all_list= ", systems_all_list)
    loop = asyncio.get_event_loop()
    if iservices_active_IPs:
        loop.create_task(check_iservices_availability(
                                    iservices_all_list=iservices_all_list,
                                    iservices_active_IPs=iservices_active_IPs, 
                                    db=db,
                                    check_interval=check_interval_internet
                                    )
                                )

    if active_systems_list_of_dicts:    
        loop.create_task(get_systems_metrics(
                                    active_systems_list_of_dicts=active_systems_list_of_dicts,
                                    systems_all_list=systems_all_list,
                                    db=db,
                                    check_interval=check_interval_metrics
                                    )
                                )

    if services_result_list:
        loop.create_task(check_service_availability(
                                services_result_list=services_result_list,
                                db=db,
                                check_interval=check_interval_serivces
                                )
                            )
    if active_systems_list_of_dicts:
        loop.create_task(get_system_journal(
                                    active_systems_list_of_dicts=active_systems_list_of_dicts,
                                    systems_all_list=systems_all_list,
                                    db=db,
                                    check_interval=check_interval_journals
                                    )
                                )
    try:
        loop.run_forever()
    except KeyboardInterrupt as e:
        pass
    finally:
        loop.close()

    # os._exit(1)

async def check_iservices_availability(iservices_all_list, iservices_active_IPs, db, check_interval):
    while True:
        print("(1) Doing the check_iservices_availability")
        internet_check_result = ping_ip_addresses(iservices_active_IPs, iservices_all_list, limit=len(iservices_active_IPs))
        # print("internet_check_result = ", internet_check_result)
        db_query.add_data_in_table(db=db, data=internet_check_result, table='monitor_internetavailability')
        await asyncio.sleep(check_interval)

async def check_service_availability(services_result_list, 
                                     db,
                                     check_interval
                                     ):
        active_services = []
        for srv in services_result_list:
            if srv.enabled == 1:
                active_services.append(srv)
        # print('\nactive_services= ', active_services)
        
        while True:
            print("(2) Doing the check services availability")
            service_check_result = check_web_service(service_list=active_services)
            db_query.add_data_in_table(db=db, 
                                       data=service_check_result, 
                                       table='monitor_serviceavailability')
            await asyncio.sleep(check_interval)

async def get_systems_metrics(active_systems_list_of_dicts, systems_all_list, db, check_interval):
    regex_top = re.compile(r'.+top \D+(?P<check_time>\S+) up\D+(?P<uptime>\S+\s\S+\s+\d+.\d+).+average:\s(?P<cpu_load_1>\d.\d+)\S\s(?P<cpu_load_5>\d+.\d+)\S\s(?P<cpu_load_15>\d+.\d+).+(?P<wa>\d+\.\d+).+wa,.+MiB Mem :...\s(?P<mem_total>\d+.\d+).+total...\s+(?P<mem_free>\d+.\d+).+free\S+\s+(?P<mem_used>\d+.\d+).+used\S+\s+(?P<mem_buff>\d+.\d+).+Swap:...\s(?P<swap_total>\d+.\d+).+total\S+\s+(?P<swap_free>\d+.\d+).+free\S+\s+(?P<swap_used>\d+.\d+).+used\S+\s+(?P<swap_avail>\d+.\d+)', re.MULTILINE)
    # regex_df =re.compile(r'.+(?P<hdd_dev>\/dev\/\w+)\s+(?P<size>\d+\w)\s+(?P<used>\d+\w)\s+(?P<avail>\d+\w)\s+(?P<use_percent>\d+%)\s\/', re.MULTILINE)
    regex_df =re.compile(r'.+(?P<hdd_dev>\/dev\/\w+)\s+(?P<size>\d+\.?\d+\w)\s+(?P<used>\d+\.?\d+\w)\s+(?P<avail>\d+\.?\d+\w)\s+(?P<use_percent>\d+\.?\d+%)\s\/', re.MULTILINE)
    while True:
        print("(3) Doing the get_systems_metrics")
        # print("\nactive_systems_list_of_dicts= ", active_systems_list_of_dicts)
        result_top = send_commands_to_devices(
                devices=active_systems_list_of_dicts,
                prepared_dict=False, 
                limit=len(active_systems_list_of_dicts),
                command='top -n1',
                regex=regex_top
                )
        # print("\nresult_top= ", result_top)
        result_df = send_commands_to_devices(
                devices=active_systems_list_of_dicts,
                prepared_dict=False, 
                limit=len(active_systems_list_of_dicts),
                command='df -h',
                regex=regex_df
                )
        # print("\nresult_df= ", result_df)

        for i, _ in enumerate(result_top):
            # print("result_top[i]= ", result_top[i])
            if result_top[i]:
                result_top[i]['check_time'] = datetime.datetime.strftime(datetime.datetime.now().replace(microsecond=0), '%d-%m-%Y %H:%M:%S')
                result_top[i].pop('wa')
                result_top[i].pop('mem_total')
                result_top[i].pop('mem_free')
                result_top[i].pop('mem_buff')
                result_top[i].pop('swap_total')
                result_top[i].pop('swap_free')
                result_top[i].pop('swap_used')
                result_top[i].pop('swap_avail')
                for z, _ in enumerate(result_df):
                    if result_df[z]:
                        if result_top[i]['system_name'] == result_df[z]['system_name']:
                            result_top[i]['disk_usage'] = result_df[z]['use_percent'][:-1]
                            break
                for j, _ in enumerate(systems_all_list):
                    if result_top[i]['system_name'] == systems_all_list[j].system_name:
                        result_top[i]['system_id'] = systems_all_list[j].id
                        result_top[i].pop('system_name')
                        break

        result = result_top
        # print("\nresult_final= ", result)
        # print("\nresult_top= ", result_top)
        db_query.add_data_in_table(
                db=db,
                data=result,
                table="monitor_systemsmetrics"
                )
        await asyncio.sleep(check_interval)

async def get_system_journal(active_systems_list_of_dicts,
                             systems_all_list,
                             db,
                             check_interval
                             ):
    period_get_journal_for_query = 1024
    # period_get_journal_for_query = round(check_interval / 3600 , 1) + 1
    # print("\nperiod_get_journal_for_query= ", period_get_journal_for_query)
    while True:
        print("(4) Doing the get_system_journal")
        result_journal = send_commands_to_devices(
                devices=active_systems_list_of_dicts,
                prepared_dict=False, 
                limit=len(active_systems_list_of_dicts),
                regex=re.compile(r'''
                                \x1B  # ESC
                                (?:   # 7-bit C1 Fe (except CSI)
                                    [@-Z\\-_]
                                |     # or [ for CSI, followed by a control sequence
                                    \[
                                    [0-?]*  # Parameter bytes
                                    [ -/]*  # Intermediate bytes
                                    [@-~]   # Final byte
                                )
                                ''', re.VERBOSE),
                command=f'journalctl -p4 --since "{period_get_journal_for_query} hour ago" -o json --no-page',
                cmd_type='journalctl'
                )
        # print("\nresult_journal= ", result_journal)  
        empty_records = []
        for i, res in enumerate(result_journal):
            if not res:
                empty_records.insert(0, i)
        # print("\nempty_records_in_journal_result= ", empty_records)
        for i in empty_records:
            result_journal.pop(i)
            
        if result_journal:
            for i, _ in enumerate(result_journal):
                # print("result_top[i]= ", result_top[i])
                result_journal[i]['priority'] = result_journal[i].pop('PRIORITY')
                result_journal[i]['pid'] = result_journal[i].pop('_PID')
                result_journal[i]['realtime_timestamp'] = datetime.datetime.utcfromtimestamp(int(str(result_journal[i].pop('__REALTIME_TIMESTAMP'))[:10])).strftime('%d-%m-%Y %H:%M:%S')
                result_journal[i]['message'] = result_journal[i].pop('MESSAGE')
                result_journal[i]['hostname'] = result_journal[i].pop('_HOSTNAME')
                result_journal[i]['code_func'] = result_journal[i].pop('CODE_FUNC')
                result_journal[i]['cmdline'] = result_journal[i].pop('_CMDLINE')
                result_journal[i].pop('SYSLOG_IDENTIFIER')
                result_journal[i].pop('_SOURCE_REALTIME_TIMESTAMP')
                result_journal[i].pop('_BOOT_ID')
                result_journal[i].pop('_SYSTEMD_SLICE')
                result_journal[i].pop('_SELINUX_CONTEXT')
                result_journal[i].pop('__CURSOR')
                result_journal[i].pop('_GID')
                result_journal[i].pop('_EXE')
                result_journal[i].pop('SYSLOG_FACILITY')
                result_journal[i].pop('_TRANSPORT')
                result_journal[i].pop('_COMM')
                result_journal[i].pop('_CAP_EFFECTIVE')
                result_journal[i].pop('CODE_FILE')
                result_journal[i].pop('_SYSTEMD_OWNER_UID')
                result_journal[i].pop('_SYSTEMD_USER_UNIT')
                result_journal[i].pop('_AUDIT_LOGINUID')
                result_journal[i].pop('_SYSTEMD_USER_SLICE')
                result_journal[i].pop('_UID')
                result_journal[i].pop('_AUDIT_SESSION')
                result_journal[i].pop('TID')
                result_journal[i].pop('_MACHINE_ID')
                result_journal[i].pop('__MONOTONIC_TIMESTAMP')
                result_journal[i].pop('CODE_LINE')
                result_journal[i].pop('_SYSTEMD_UNIT')
                result_journal[i].pop('_SYSTEMD_CGROUP')
                for j, _ in enumerate(systems_all_list):
                    if result_journal[i]['system_name'] == systems_all_list[j].system_name:
                        result_journal[i]['system_id'] = systems_all_list[j].id
                        result_journal[i].pop('system_name')
                        break
            dublicate_records_in_db = []
            for i, _ in enumerate(result_journal):
                jquery = f"SELECT realtime_timestamp, message, system_id FROM monitor_systemslogs WHERE message = '{result_journal[i]['message']}' AND realtime_timestamp = '{result_journal[i]['realtime_timestamp']}' AND system_id = '{result_journal[i]['system_id']}'"
                # print(jquery)
                check_exist_record_in_db = db_query.select_query_all(db=db, query=jquery)
                if check_exist_record_in_db:
                    dublicate_records_in_db.insert(0, i)
            for i in dublicate_records_in_db:
                result_journal.pop(i)
            # print("\ndublicate_records_in_db= ", dublicate_records_in_db)
            #print("\nresult_journal_final= ", result_journal)
            # print("\nresult_top= ", result_top)
            result = result_journal
            # print("\nresult= ", result)
            if result:
                db_query.add_data_in_table(
                        db=db,
                        data=result,
                        table="monitor_systemslogs"
                        )
        await asyncio.sleep(check_interval)

def check_config_files(systems_file, services_file, internet_services_file):
    if not os.path.exists(systems_file):
        with open(systems_file, 'w') as f:
            f.write('''- system_name: OPIZ2
  device_type: linux
  host: 192.168.1.203
  username: python
  key_file: /ssh_key/id_rsa
  timeout: 5
  enabled: 1
- system_name: Debian_PyNeng
  device_type: linux
  host: 192.168.1.203
  username: python
  key_file: /ssh_key/id_rsa
  timeout: 5
  enabled: 1
'''
            )
    if not os.path.exists(services_file):
        with open(services_file, 'w') as f:
            f.write('''- service_name: Home Assistant
  protocol: http
  host: 192.168.1.201
  port: 8123
  path: ''
  correct_http_response_code: 200
  correct_http_response: <title>Home Assistant</title>
  enabled: 1
- service_name: Pi-hole
  protocol: http
  host: 192.168.1.201
  port: 80
  path: /admin/
  correct_http_response_code: 200
  correct_http_response: <title>Pi-hole - orangepizero2</title>
  enabled: 0
- service_name: Zigbee2MQTT
  protocol: http
  host: 192.168.1.201
  port: 8080
  path: ''
  correct_http_response_code: 200
  correct_http_response: <title>Zigbee2MQTT</title>
  enabled: 0
- service_name: mosquitto
  protocol: http
  host: 192.168.1.201
  port: 1883
  path: ''
  correct_http_response_code: 200
  correct_http_response: 
  enabled: 0
- service_name: lipsum.com
  protocol: https
  host: en.lipsum.com
  port: 443
  path: /feed/html
  correct_http_response_code: 200
  correct_http_response: <title>Lorem Ipsum - All the facts - Lipsum generator</title>
  enabled: 1'''
            )
    if not os.path.exists(internet_services_file):
        with open(internet_services_file, 'w') as f:
            f.write('''- service_name: google_dns
  IPv4: 8.8.8.8
  enabled: 1
- service_name: yandex_dns
  IPv4: 77.88.8.8
  enabled: 1
- service_name: not_found_srv
  IPv4: 192.168.1.249
  enabled: 1
- service_name: new_test_srv2
  IPv4: 169.172.127.10
  enabled: 0'''
            )

def load_main_settings(check_interval_internet=0,
                       check_interval_services=0,
                       check_interval_metrics=0,
                       check_interval_journals=0
                       ):
    settings_file_exist = os.path.exists(r"/webmonitor_backend/config/settings.yaml")
    if settings_file_exist:
        with open(r'/webmonitor_backend/config/settings.yaml', 'r') as f:
            settings_dict = yaml.safe_load(f)
    else:
        print("Warning! File 'settings.yaml' not found! Will be used default settings.")
        settings = '''WORK_DIR: /webmonitor_backend
DB_PATH: /webmonitor_backend/DB/monitor_db.sqlite3
SYSTEMS_FILE: /webmonitor_backend/config/systems.yaml
SERVICES_FILE: /webmonitor_backend/config/services.yaml
INTERNET_SERVICES_FILE: /webmonitor_backend/config/internet_services.yaml
CHECK_INTERVAL_INTERNET: 5
CHECK_INTERVAL_SERVICES: 15
CHECK_INTERVAL_METRICS: 25
CHECK_INTERVAL_JOURNALS: 35'''
        with open(r'/webmonitor_backend/config/settings.yaml', 'w') as f:
            f.write(settings)
        with open(r'/webmonitor_backend/config/settings.yaml', 'r') as f:
            settings_dict = yaml.safe_load(f)

    if check_interval_internet:
        settings_dict['CHECK_INTERVAL_INTERNET'] = check_interval_internet
    elif check_interval_services:
        settings_dict['CHECK_INTERVAL_SERVICES'] = check_interval_services
    elif check_interval_metrics:
        settings_dict['CHECK_INTERVAL_METRICS'] = check_interval_metrics
    elif check_interval_journals:
        settings_dict['CHECK_INTERVAL_JOURNALS'] = check_interval_journals
    
    return settings_dict


if __name__ == "__main__":
    # Load main config
    settings_dict = load_main_settings(check_interval_internet=args.check_interval_internet,
                                       check_interval_services=args.check_interval_services,
                                       check_interval_metrics=args.check_interval_metrics,
                                       check_interval_journals=args.check_interval_journals
                                       )
    
    # Check config files
    check_config_files(systems_file=settings_dict['SYSTEMS_FILE'],
                       services_file=settings_dict['SERVICES_FILE'],
                       internet_services_file=settings_dict['INTERNET_SERVICES_FILE'],
    )

    # Check DB exist
    while True:
        time.sleep(5) # Waiting for the database to be created by the frontend
        db_exists = os.path.exists(settings_dict['DB_PATH'])
        if db_exists:
            break
        else:
            print("Database not found! Waiting for database creation...")
    
    # Initialization
    iservices_all_list, iservices_active_IPs, systems_actual_list, active_systems_list_of_dicts, services_result_list = initialization(
    db_path=settings_dict['DB_PATH'],
    internet_services_file=settings_dict['INTERNET_SERVICES_FILE'],
    systems_file=settings_dict['SYSTEMS_FILE'],
    services_file=settings_dict['SERVICES_FILE'],
    force_init=False
    )

    # Start main process
    main(iservices_all_list=iservices_all_list, 
         iservices_active_IPs=iservices_active_IPs, 
         systems_all_list=systems_actual_list,
         active_systems_list_of_dicts=active_systems_list_of_dicts,
         services_result_list=services_result_list,
         check_interval_internet=settings_dict['CHECK_INTERVAL_INTERNET'],
         check_interval_serivces=settings_dict['CHECK_INTERVAL_SERVICES'],
         check_interval_metrics=settings_dict['CHECK_INTERVAL_METRICS'],
         check_interval_journals=settings_dict['CHECK_INTERVAL_JOURNALS'],
         db=settings_dict['DB_PATH']
        )