import re
import yaml
import db_query
from collections import namedtuple
from getpass import getpass
from tqdm import tqdm
from send_cmd_to_systems import send_commands_to_devices


def initialization(db_path, internet_services_file, systems_file, services_file, force_init=False):
    print("Start initialization...")
    iservices_result_list, systems_result_list, services_result_list = [[], [], []]
    func_list = [_sync_iservices_with_DB, _sync_systems_with_DB, _sync_services_with_DB]
    value_list = [[db_path, internet_services_file], 
                  [db_path, systems_file, force_init],
                  [db_path, services_file]                  
                  ]
    result_list = [iservices_result_list,
                   systems_result_list,
                   services_result_list
                   ]
    progress_list = zip(func_list, value_list, result_list)
    number_of_operations = len(func_list)
    # print("\nprogress_list= ", list(progress_list))  

    for func, values, results in tqdm(progress_list, desc='Initialization progress:', total=number_of_operations):
       results.append(func(*values))

    # print("\niservices_result_list= ", iservices_result_list) 
    # print("\nsystems_result_list= ", systems_result_list) 
    # print("\nservices_result_list= ", services_result_list) 
    iservices_actual_list,  iservices_active_IPs = iservices_result_list[0][0], iservices_result_list[0][1]
    systems_actual_list, active_systems_list_of_dicts = systems_result_list[0][0], systems_result_list[0][1]
    # print('\nservices_result_list= ', services_result_list[0])
    
    print("\nInitialization finished!")
    # print("\niservices_actual_list= ", iservices_actual_list)
    # print("\niservices_active_IPs= ", iservices_active_IPs)
    # print("\nsystems_actual_list= ", systems_actual_list)
    # print("\nactive_systems_list_of_dicts= ", active_systems_list_of_dicts)
    
    return iservices_actual_list, iservices_active_IPs, systems_actual_list, active_systems_list_of_dicts, services_result_list[0]

def _sync_iservices_with_DB(db, internet_services_file):
    with open(internet_services_file) as f:
        iservices_list_f = yaml.safe_load(f)
    db_query.sync_db_records(db=db,
                                 data=iservices_list_f,
                                 table='monitor_iservices',
                                 )
    
    iservices_actual_list = _forming_actual_list(db=db, table='monitor_iservices')
    iservices_active_IPs = [iserv.IPv4 for iserv in iservices_actual_list if iserv.enabled]
    
    return iservices_actual_list, iservices_active_IPs

def _sync_systems_with_DB(db, systems_file, force_init):
    with open(systems_file) as f:
        systems_list_f = yaml.safe_load(f)
    db_query.sync_db_records(db=db,
                             data=systems_list_f,
                             table='monitor_systems',
                             )
    systems_actual_list = _forming_actual_list(db=db, table="monitor_systems")
    active_systems = [srv for srv in systems_actual_list if srv.enabled]
    # print('\nactive_systems= ', active_systems)
    active_systems_list_of_dicts = []
    if active_systems:
        active_systems_list_of_dicts = _systems_data_update(active_systems=active_systems,
                                                             db=db,
                                                             force_init=force_init)
        # print("active_systems_list_of_dicts= ", active_systems_list_of_dicts)
        _add_empty_fields_to_list_of_dicts(active_systems_list_of_dicts)
        # print("\nactive_systems_list_of_dicts= ", active_systems_list_of_dicts)

    if active_systems_list_of_dicts:
        if not force_init:
            lsb_upd_list = []
            for row in active_systems_list_of_dicts:
                if 'os' in row.get('empty_fields'):
                    lsb_upd_list.append(row)
        else:
            lsb_upd_list = active_systems_list_of_dicts
        # print("lsb_upd_list = ", lsb_upd_list)
        if lsb_upd_list:
            result_lsb_release = send_commands_to_devices(
            devices=lsb_upd_list,
            prepared_dict=False, 
            limit=len(lsb_upd_list),
            command='lsb_release -a',
            regex=re.compile(r'.*Distributor ID:\W+(?P<distributor_id>\w+.+)\sDescription:\W+(?P<description>\w+.+)\sRelease:\W+(?P<release>\w+.+)\sCodename:\W+(?P<codename>\w+)\s', re.MULTILINE)
            )
            # print("result_lsb_release= ", result_lsb_release)
        if not force_init:
            top_upd_list = []
            for row in active_systems_list_of_dicts:
                if 'RAM' in row.get('empty_fields'):
                    top_upd_list.append(row)
        else:
            top_upd_list = active_systems_list_of_dicts
        # print("top_upd_list = ", top_upd_list)
        if top_upd_list:
            result_top = send_commands_to_devices(
                devices=top_upd_list,
                prepared_dict=False, 
                limit=len(top_upd_list),
                command='top -n1',
                regex=re.compile(r'.+top \D+(?P<time>\S+) up\D+(?P<up>\S+\s\S+\s+\d+.\d+).+average:\s(?P<average_1>\d.\d+)\S\s(?P<average_5>\d+.\d+)\S\s(?P<average_15>\d+.\d+).+(?P<wa>\d+\.\d+).+wa,.+MiB Mem :...\s(?P<mem_total>\d+.\d+).+total...\s+(?P<mem_free>\d+.\d+).+free\S+\s+(?P<mem_used>\d+.\d+).+used\S+\s+(?P<mem_buff>\d+.\d+).+Swap:...\s(?P<swap_total>\d+.\d+).+total\S+\s+(?P<swap_free>\d+.\d+).+free\S+\s+(?P<swap_used>\d+.\d+).+used\S+\s+(?P<swap_avail>\d+.\d+)', re.MULTILINE)
                )
            # print("\n\nresult_top= ", result_top)
        if not force_init:
            hostname_upd_list = []
            for row in active_systems_list_of_dicts:
                if 'hostname' in row.get('empty_fields'):
                    hostname_upd_list.append(row)
        else:
            hostname_upd_list = active_systems_list_of_dicts
        # print("hostname_upd_list = ", hostname_upd_list)
        if hostname_upd_list:
            result_hostname = send_commands_to_devices(
                devices=hostname_upd_list,
                prepared_dict=False, 
                limit=len(hostname_upd_list),
                command='hostname',
                regex=re.compile(r'(?P<hostname>\S+)')
                )
            # print("\n\nresult_hostname= ", result_hostname)
        if not force_init:
            HDD_upd_list = []
            for row in active_systems_list_of_dicts:
                if 'HDD' in row.get('empty_fields'):
                    HDD_upd_list.append(row)
        else:
            HDD_upd_list = active_systems_list_of_dicts
        # print("HDD_upd_list = ", HDD_upd_list)
        if HDD_upd_list:
            result_hdd = send_commands_to_devices(
                devices=HDD_upd_list,
                prepared_dict=False, 
                limit=len(HDD_upd_list),
                command='df -h',
                regex=re.compile(r'.+(?P<hdd_dev>\/dev\/\w+)\s+(?P<size>\d+\w)\s+(?P<used>\d+\w)\s+(?P<avail>\d+\w)\s+(?P<use_percent>\d+%)\s\/', re.MULTILINE)
                )
            # print("\n\nresult_hdd= ", result_hdd)

        if lsb_upd_list:
            # print('\n========Hint to lsb if=========\n')
            for i in range(len(result_lsb_release)):
                for j in range(len(active_systems_list_of_dicts)):
                    if result_lsb_release[i] and result_lsb_release[i].get('system_name') == active_systems_list_of_dicts[j]['system_name']:
                        # print('Hint to lsb for/n')
                        active_systems_list_of_dicts[j]['os'] = result_lsb_release[i].get('description', None)
        if top_upd_list:
            # print('\n========Hint to top if=========\n')
            for i in range(len(result_top)):
                for j in range(len(active_systems_list_of_dicts)):
                    if result_top[i] and result_top[i].get('system_name') == active_systems_list_of_dicts[j]['system_name']:
                        # print('Hint to top for/n')
                        active_systems_list_of_dicts[j]['RAM'] = result_top[i].get('mem_total', None)
        
        if hostname_upd_list:
            # print('\n========Hint to hostname if=========\n')
            for i in range(len(result_hostname)):
                for j in range(len(active_systems_list_of_dicts)):
                    if result_hostname[i] and result_hostname[i].get('system_name') == active_systems_list_of_dicts[j]['system_name']:
                        # print('Hint to hostname for/n')
                        active_systems_list_of_dicts[j]['hostname'] = result_hostname[i].get('hostname', None)
        
        if HDD_upd_list:
            # print('\n========Hint to HDD if=========\n')
            for i in range(len(result_hdd)):
                for j in range(len(active_systems_list_of_dicts)):
                    if result_hdd[i] and result_hdd[i].get('system_name') == active_systems_list_of_dicts[j]['system_name']:
                        # print('Hint to HDD for/n')
                        active_systems_list_of_dicts[j]['HDD'] = result_hdd[i].get('size', None)
        
        for i in range(len(active_systems_list_of_dicts)):
            active_systems_list_of_dicts[i].pop('empty_fields')

        # print("final active_systems_list_of_dicts= ", active_systems_list_of_dicts)
        
        db_query.update_data_in_table(
                        db=db,
                        data=active_systems_list_of_dicts,
                        table="monitor_systems", 
                        condition='system_name'
        )
    # print('systems_actual_list= ', active_systems_list_of_dicts)
    # print('active_systems_list_of_dicts= ', active_systems_list_of_dicts)
    return systems_actual_list, active_systems_list_of_dicts

def _sync_services_with_DB(db, services_file):
    with open(services_file) as f:
        services_list_f = yaml.safe_load(f)
    # print('\nservices_list_f= ', services_list_f)
    db_query.sync_db_records(db=db,
                             data=services_list_f,
                             table='monitor_services',
                             )
    # = db_query.get_all_fields_from_table(db=db, table='monitor_services')
    services = _forming_actual_list(db=db, table='monitor_services')
    return services

def _forming_actual_list(db, table):
    table_fields_info = db_query.select_query_all(db, "PRAGMA table_info({})".format(table))
    list_db = db_query.get_all_fields_from_table(db=db, table=table)
    table_field_names = []
    for row in table_fields_info:
        table_field_names.append(row[1])
    active_list_obj = namedtuple(table, " ".join(table_field_names))
    actual_named_list = []
    for row in list_db:
        actual_named_list.append(active_list_obj(*row))
    return actual_named_list

def _systems_data_update(active_systems, db, force_init):
    active_systems_dict_list = []
    for row in active_systems:
        drow = row._asdict()
        drow.pop('id')
        if not drow['key_file'] and force_init:
            drow['username'], drow['password'] = _set_system_credential(drow, mode='all')
        elif not drow['username']:
            drow['username'] = _set_system_credential(drow, mode='username')
        if not drow['key_file'] and not drow['password']:
            drow['password'] = _set_system_credential(drow, mode='password')
        active_systems_dict_list.append(drow)
    
    # print("active_systems_dict_list= ", active_systems_dict_list)
    db_query.update_data_in_table(db=db, data=active_systems_dict_list, table=type(active_systems[0]).__name__, condition=list(active_systems_dict_list[0].keys())[0])
    return active_systems_dict_list

def _set_system_credential(system, mode=''):
    username, password = [None, None]
    while True:
        if mode == 'username':
            username = input(f"\nEnter login for service '{system['system_name']}': ")
            break
        if mode == 'password':
            # print(f"Enter password for service '{system['system_name']}'")
            password = getpass(f"\nEnter password for service '{system['system_name']}': ")
            password_check = getpass("Repeat password: ")
            if password == password_check:
                break
            print("The entered values password do not match. Please repeat." + "\n")
        if mode == 'all':
            username = input(f"\nEnter login for service '{system['system_name']}': ")
            password = getpass(f"\nEnter password for service '{system['system_name']}': ")
            password_check = getpass("Repeat password: ")
            if password == password_check:
                break
            print("The entered values password do not match. Please repeat." + "\n")
    
    if username and password:
        return username, password
    elif username:
        return username
    else:
        return password

def _add_empty_fields_to_list_of_dicts(list_of_dicts):
    keys = list_of_dicts[0].keys()
    # print("\nkeys= ", keys)
    for row in list_of_dicts:
        row['empty_fields'] = []
        for key in keys:
            if not row[key] and key != 'empty_fields':
                row['empty_fields'].append(key)
    # print("list_of_dicts= ", list_of_dicts)