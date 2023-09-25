
import bs4
import datetime
import requests
from concurrent.futures import ThreadPoolExecutor


def check_web_service(service_list):
    limit = len(service_list)
    results = []
    with ThreadPoolExecutor(max_workers=limit) as executor:
        futures = [executor.submit(requests.get, service.protocol + '://' + service.host + ':' + str(service.port) + service.path) for service in service_list]
        for i, future in enumerate(futures):
            try:
                # print('serv_check future.result().text= ', future.result().text)
                html = bs4.BeautifulSoup(future.result().text, features='lxml')
                if future.result().status_code == 200 and str(html.title) == service_list[i].correct_http_response:
                    # print(f'\nService {service_list[i].service_name} available! =)')
                    results.append(
                        {'service_id': service_list[i].id, 
                        'check_time': datetime.datetime.strftime(datetime.datetime.now().replace(microsecond=0), '%Y-%m-%d %H:%M:%S'),
                        'availability': True})
                else:
                    # print(f'\nService {service_list[i].service_name} NOT available! =()')
                    results.append(
                        {'service_id': service_list[i].id, 
                         'check_time': datetime.datetime.strftime(datetime.datetime.now().replace(microsecond=0), '%Y-%m-%d %H:%M:%S'),
                         'availability': False})
            except requests.exceptions.ConnectionError as error:
                # print(f'\nService {service_list[i].service_name} NOT available! =()')
                results.append(
                        {'service_id': service_list[i].id, 
                         'check_time': datetime.datetime.strftime(datetime.datetime.now().replace(microsecond=0), '%Y-%m-%d %H:%M:%S'),
                         'availability': False})

    # print('\nresults_services_check= ', results)
    return results