import json
import re
import paramiko
from concurrent.futures import ThreadPoolExecutor, as_completed
from netmiko import ConnectHandler, NetMikoTimeoutException


def send_command(device, command, shell=False):
    with ConnectHandler(**device) as ssh:
        result = ssh.send_command(command)
    return result

def send_commands_to_devices(devices, *, 
                             command,
                             cmd_type=None, 
                             regex=None, 
                             result_length=500, 
                             limit=3, 
                             prepared_dict=True,
                             ):
    result_list = []
    if not prepared_dict:
        devices_for_netmiko = _prepare_dict_for_netmiko(devices=devices)
    else:
        devices_for_netmiko = devices

    # print('devices_for_netmiko= ', devices_for_netmiko)
    with ThreadPoolExecutor(max_workers=limit) as executor:
        futures = [executor.submit(send_command, device, command) for device in devices_for_netmiko]
        for i, future in enumerate(futures):
            # with open('top_results', 'a') as f:
            #    f.write(" ".join(future.result()[:result_length].splitlines()))
            # print("future.result()= ", " ".join(future.result()[:result_length].splitlines()))
            try:
                if cmd_type == 'journalctl':
                    clean_res = regex.sub('', future.result()).splitlines()[1]
                    # print("pre_result_journal= ", clean_res)
                    # print("\njfuture= ", future.result())
                    # print("\nclean_res= ", clean_res)
                    if clean_res.startswith('{') and clean_res.endswith("}"):
                        result_list.append(json.loads(clean_res))
                    else:
                        result_list.append({})
                else:
                    # print("\njfuture= ", " ".join(future.result()[:result_length].splitlines()))
                    # with open('/webmonitor_backend/config/output_future', 'a') as f:
                       # f.write(" ".join(future.result()[:result_length].splitlines()))
                    match = regex.search(" ".join(future.result()[:result_length].splitlines()))
                    if match:
                        # print('\nmatch.groupdict()= ', match.groupdict())
                        result_list.append(match.groupdict())
                    else:
                        result_list.append({})
            except paramiko.ssh_exception.SSHException as error:
                print(f"\nFailed to connection to {devices[i]['system_name']} with IP {devices[i]['host']}")
                result_list.append({})
    
    if not prepared_dict:
        unique_key = list(devices[0].keys())[0]
        for i in range(len(result_list)):
            if result_list[i]:
                result_list[i][unique_key] = devices[i][unique_key]
    return result_list

def _prepare_dict_for_netmiko(devices):
    netmiko_list_of_dicts = []
    clear_dict = {}
    for row in devices:
        netmiko_list_of_dicts.append(clear_dict.copy())
    # print('devices = ', devices)
    for i in range(len(devices)):
        if devices[i]['key_file']:
            netmiko_list_of_dicts[i]['key_file'] = devices[i]['key_file']
        else:
            netmiko_list_of_dicts[i]['password'] = devices[i]['password']
        netmiko_list_of_dicts[i]['username'] = devices[i]['username']
        netmiko_list_of_dicts[i]['device_type'] = devices[i]['device_type']
        netmiko_list_of_dicts[i]['host'] = devices[i]['host']
        netmiko_list_of_dicts[i]['timeout'] = devices[i]['timeout']

    return netmiko_list_of_dicts


if __name__ == "__main__":
    devices = [{'device_type': 'linux',
         'host': '127.0.0.1',
         'username': 'python',
         'password': 'python',
         'timeout': '5',
         },
         {'device_type': 'linux',
         'host': '127.0.0.1',
         'username': 'python',
         'password': 'python',
         'timeout': '5',
         }
    ]
    result_length = 500
    # send_top_cmd(devices, result_length=result_length)
