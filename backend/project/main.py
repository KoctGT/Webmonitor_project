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
        check_interval_internet=180,
        check_interval_serivces=600,
        check_interval_metrics=3600,
        check_interval_journals=900
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
    regex_top = re.compile(r'.+top \D+(?P<check_time>\S+) up\D+(?P<uptime>\S+\s\S+\s+\d+.+),\s\s\d+.+average:\s(?P<cpu_load_1>\d.\d+)\S\s(?P<cpu_load_5>\d+.\d+)\S\s(?P<cpu_load_15>\d+.\d+).+(?P<wa>\d+\.\d+).+wa,.+MiB Mem :.?.?\s*(?P<mem_total>\d+.\d+).+total,.\s*(?P<mem_free>\d+.\d+).?.?free,.?.?\s*(?P<mem_used>\d+.\d+).+used,.?.?\s*(?P<mem_buff>\d+.\d+).*MiB Swap:.?.?\s*(?P<swap_total>\d+.\d+).+total,.?.?\s*(?P<swap_free>\d+.\d+).+free,.?.?\s*(?P<swap_used>\d+.\d+).+used..?.?\s*(?P<swap_avail>\d+.\d+)', re.MULTILINE)
    # regex_top = re.compile(r'.+top \D+(?P<check_time>\S+) up\D+(?P<uptime>\S+\s\S+\s+\d+.+),\s\s\d+.+average:\s(?P<cpu_load_1>\d.\d+)\S\s(?P<cpu_load_5>\d+.\d+)\S\s(?P<cpu_load_15>\d+.\d+).+(?P<wa>\d+\.\d+).+wa,.+MiB Mem :...\s(?P<mem_total>\d+.\d+).+total...\s+(?P<mem_free>\d+.\d+).+free\S+\s+(?P<mem_used>\d+.\d+).+used\S+\s+(?P<mem_buff>\d+.\d+).+Swap:...\s(?P<swap_total>\d+.\d+).+total\S+\s+(?P<swap_free>\d+.\d+).+free\S+\s+(?P<swap_used>\d+.\d+).+used\S+\s+(?P<swap_avail>\d+.\d+)', re.MULTILINE)
    # regex_top = re.compile(r'.+top \D+(?P<check_time>\S+) up\D+(?P<uptime>\S+\s\S+\s+\d+.\d+).+average:\s(?P<cpu_load_1>\d.\d+)\S\s(?P<cpu_load_5>\d+.\d+)\S\s(?P<cpu_load_15>\d+.\d+).+(?P<wa>\d+\.\d+).+wa,.+MiB Mem :...\s(?P<mem_total>\d+.\d+).+total...\s+(?P<mem_free>\d+.\d+).+free\S+\s+(?P<mem_used>\d+.\d+).+used\S+\s+(?P<mem_buff>\d+.\d+).+Swap:...\s(?P<swap_total>\d+.\d+).+total\S+\s+(?P<swap_free>\d+.\d+).+free\S+\s+(?P<swap_used>\d+.\d+).+used\S+\s+(?P<swap_avail>\d+.\d+)', re.MULTILINE)
    # regex_df =re.compile(r'.+(?P<hdd_dev>\/dev\/\w+)\s+(?P<size>\d+\w)\s+(?P<used>\d+\w)\s+(?P<avail>\d+\w)\s+(?P<use_percent>\d+%)\s\/', re.MULTILINE)
    regex_df =re.compile(r'.+(?P<hdd_dev>\/dev\/mmc\w+)\s+(?P<size>\d+\.?\d+\w)\s+(?P<used>\d+\.?\d+\w)\s+(?P<avail>\d+\.?\d+\w)\s+(?P<use_percent>\d+\.?\d+%)\s\/', re.MULTILINE)
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
                result_top[i]['check_time'] = datetime.datetime.strftime(datetime.datetime.now().replace(microsecond=0), '%Y-%m-%d %H:%M:%S')
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
        if result[0]:
            db_query.add_data_in_table(
                    db=db,
                    data=result,
                    table="monitor_systemsmetrics"
                    )
        else:
            print('\nNo data received for systemsmetrics table!')
        await asyncio.sleep(check_interval)

async def get_system_journal(active_systems_list_of_dicts,
                             systems_all_list,
                             db,
                             check_interval
                             ):
    # period_get_journal_for_query = 4096
    period_get_journal_for_query = round(check_interval / 3600 , 1) + 1
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
        
        result_journal_db = []
        if result_journal:
            for i, _ in enumerate(result_journal):
                result_journal_db.append({})
                # print("result_top[i]= ", result_top[i])
                if result_journal[i].get('PRIORITY', None): 
                    result_journal_db[i]['priority'] = result_journal[i].pop('PRIORITY')
                else:
                    result_journal_db[i]['priority'] = None
                if result_journal[i].get('_PID', None): 
                    result_journal_db[i]['pid'] = result_journal[i].pop('_PID')
                else:
                    result_journal_db[i]['pid'] = None
                if result_journal[i].get('__REALTIME_TIMESTAMP', None):
                    result_journal_db[i]['realtime_timestamp'] = datetime.datetime.utcfromtimestamp(int(str(result_journal[i].pop('__REALTIME_TIMESTAMP'))[:10])).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    result_journal_db[i]['realtime_timestamp'] = None
                if result_journal[i].get('MESSAGE', None):
                    result_journal_db[i]['message'] = result_journal[i].pop('MESSAGE')
                else:
                    result_journal_db[i]['_HOSTNAME'] = None
                if result_journal[i].get('hostname', None):
                    result_journal_db[i]['hostname'] = result_journal[i].pop('_HOSTNAME')
                else:
                    result_journal_db[i]['hostname'] = None
                if result_journal[i].get('CODE_FUNC', None): 
                    result_journal_db[i]['code_func'] = result_journal[i].pop('CODE_FUNC')
                else:
                    result_journal_db[i]['code_func'] = None
                if result_journal[i].get('_CMDLINE', None): 
                    result_journal_db[i]['cmdline'] = result_journal[i].pop('_CMDLINE')
                else:
                    result_journal_db[i]['cmdline'] = None
                '''if result_journal[i].get('SYSLOG_IDENTIFIER', None): result_journal[i].pop('SYSLOG_IDENTIFIER')
                if result_journal[i].get('_SOURCE_REALTIME_TIMESTAMP', None): result_journal[i].pop('_SOURCE_REALTIME_TIMESTAMP')
                if result_journal[i].get('_BOOT_ID', None): result_journal[i].pop('_BOOT_ID')
                if result_journal[i].get('_SYSTEMD_SLICE', None): result_journal[i].pop('_SYSTEMD_SLICE')
                if result_journal[i].get('_SELINUX_CONTEXT', None): result_journal[i].pop('_SELINUX_CONTEXT')
                if result_journal[i].get('__CURSOR', None): result_journal[i].pop('__CURSOR')
                if result_journal[i].get('_GID', None): result_journal[i].pop('_GID')
                if result_journal[i].get('_EXE', None): result_journal[i].pop('_EXE')
                if result_journal[i].get('SYSLOG_FACILITY', None): result_journal[i].pop('SYSLOG_FACILITY')
                if result_journal[i].get('_TRANSPORT', None): result_journal[i].pop('_TRANSPORT')
                if result_journal[i].get('_COMM', None): result_journal[i].pop('_COMM')
                if result_journal[i].get('_CAP_EFFECTIVE', None): result_journal[i].pop('_CAP_EFFECTIVE')
                if result_journal[i].get('CODE_FILE', None): result_journal[i].pop('CODE_FILE')
                if result_journal[i].get('_SYSTEMD_OWNER_UID', None): result_journal[i].pop('_SYSTEMD_OWNER_UID')
                if result_journal[i].get('_SYSTEMD_USER_UNIT', None): result_journal[i].pop('_SYSTEMD_USER_UNIT')
                if result_journal[i].get('_AUDIT_LOGINUID', None): result_journal[i].pop('_AUDIT_LOGINUID')
                if result_journal[i].get('_SYSTEMD_USER_SLICE', None): result_journal[i].pop('_SYSTEMD_USER_SLICE')
                if result_journal[i].get('_UID', None): result_journal[i].pop('_UID')
                if result_journal[i].get('_AUDIT_SESSION', None): result_journal[i].pop('_AUDIT_SESSION')
                if result_journal[i].get('TID', None): result_journal[i].pop('TID')
                if result_journal[i].get('_MACHINE_ID', None): result_journal[i].pop('_MACHINE_ID')
                if result_journal[i].get('__MONOTONIC_TIMESTAMP', None): result_journal[i].pop('__MONOTONIC_TIMESTAMP')
                if result_journal[i].get('CODE_LINE', None): result_journal[i].pop('CODE_LINE')
                if result_journal[i].get('_SYSTEMD_UNIT', None): result_journal[i].pop('_SYSTEMD_UNIT')
                if result_journal[i].get('_SYSTEMD_CGROUP', None): result_journal[i].pop('_SYSTEMD_CGROUP')'''
                for j, _ in enumerate(systems_all_list):
                    if result_journal[i]['system_name'] == systems_all_list[j].system_name:
                        result_journal_db[i]['system_id'] = systems_all_list[j].id
                        result_journal_db[i]['ignored'] = False
                        result_journal_db[i]['solved'] = False
                        # result_journal[i].pop('system_name')
                        break
            dublicate_records_in_db = []
            for i, _ in enumerate(result_journal_db):
                jquery = f"SELECT realtime_timestamp, message, system_id FROM monitor_systemslogs WHERE message = '{result_journal_db[i]['message']}' AND realtime_timestamp = '{result_journal_db[i]['realtime_timestamp']}' AND system_id = '{result_journal_db[i]['system_id']}'"
                # print(jquery)
                check_exist_record_in_db = db_query.select_query_all(db=db, query=jquery)
                if check_exist_record_in_db:
                    dublicate_records_in_db.insert(0, i)
            for i in dublicate_records_in_db:
                result_journal_db.pop(i)
            # print("\ndublicate_records_in_db= ", dublicate_records_in_db)
            # print("\nresult_journal_final= ", result_journal_db)
            # print("\nresult_top= ", result_top)
            result = result_journal_db
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
            f.write('''- system_name: orangepizero2
  device_type: linux
  host: 192.168.1.201
  username: root
  key_file: /ssh_key/id_rsa
  timeout: 5
  enabled: 1
- system_name: Debian_PyNeng
  device_type: linux
  host: 192.168.1.203
  username: python
  key_file: /ssh_key/id_rsa
  timeout: 5
  enabled: 0
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
  enabled: 1
- service_name: Zigbee2MQTT
  protocol: http
  host: 192.168.1.201
  port: 8080
  path: ''
  correct_http_response_code: 200
  correct_http_response: <title>Zigbee2MQTT</title>
  enabled: 1
- service_name: mosquitto
  protocol: http
  host: 192.168.1.201
  port: 1883
  path: ''
  correct_http_response_code: 200
  correct_http_response: 
  enabled: 1
- service_name: lipsum.com
  protocol: https
  host: en.lipsum.com
  port: 443
  path: /feed/html
  correct_http_response_code: 200
  correct_http_response: <title>Lorem Ipsum - All the facts - Lipsum generator</title>
  enabled: 0'''
            )
    if not os.path.exists(internet_services_file):
        with open(internet_services_file, 'w') as f:
            f.write('''- service_name: google_dns
  IPv4: 8.8.8.8
  enabled: 1
- service_name: yandex_dns
  IPv4: 77.88.8.8
  enabled: 1
- service_name: test_server
  IPv4: 192.168.1.249
  enabled: 0
- service_name: test_server_2
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
CHECK_INTERVAL_INTERNET: 180
CHECK_INTERVAL_SERVICES: 600
CHECK_INTERVAL_METRICS: 3600
CHECK_INTERVAL_JOURNALS: 900'''
        with open(r'/webmonitor_backend/config/settings.yaml', 'w') as f:
            f.write(settings)
        with open(r'/webmonitor_backend/config/settings.yaml', 'r') as f:
            settings_dict = yaml.safe_load(f)

    if check_interval_internet:
        settings_dict['CHECK_INTERVAL_INTERNET'] = check_interval_internet
    if check_interval_services:
        settings_dict['CHECK_INTERVAL_SERVICES'] = check_interval_services
    if check_interval_metrics:
        settings_dict['CHECK_INTERVAL_METRICS'] = check_interval_metrics
    if check_interval_journals:
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
        time.sleep(30) # Waiting for the database to be created by the frontend
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
