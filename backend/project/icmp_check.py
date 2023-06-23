import datetime
import pingparsing
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from textwrap import dedent


def ping_ip(ip):
    result = subprocess.run(["ping", "-c", "3", "-n", ip], stdout=subprocess.PIPE)
    ip_is_reachable = result.returncode == 0
    # print("print= ", result.stdout.decode("utf-8"))
    return ip_is_reachable, result.stdout.decode("utf-8")

def ping_ip_addresses(ip_list, iservices_list, limit=3):
    result_list = []
    parser = pingparsing.PingParsing()
    with ThreadPoolExecutor(max_workers=limit) as executor:
        futures = [executor.submit(ping_ip, ip) for ip in ip_list]
    
    for future in as_completed(futures):
        response_dict = parser.parse(dedent(future.result()[1])).as_dict()
        response_dict['check_time'] = datetime.datetime.strftime(datetime.datetime.now().replace(microsecond=0), '%d-%m-%Y %H:%M:%S')
        response_dict['availability'] = future.result()[0]
        for service in iservices_list:
            if response_dict['destination'] in service:
                response_dict['iservice_id'] = service.id
        result_list.append(response_dict)
    return result_list


if __name__ == "__main__":
    print(ping_ip_addresses(["8.8.8.8", "192.168.1.252"]))