
import requests
import json
from requests.auth import HTTPBasicAuth
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from test_add_netapp_selenium import api_netapp_etalon
from utils_tests.config import logger


# для таблицы svm n - начальная ячейка, m - конечная ячейка (для netapp-ssd n=45, m=78)
def replace_boolean(obj):
    if isinstance(obj, str):
        if obj.lower() == 'true':
            return True
        elif obj.lower() == 'false':
            return False
    return obj


def parse_data(data):
    result = []
    current_svm = None

    for item in data:
        if isinstance(item, bool):
            if 'nfs_allowed' not in current_svm:
                current_svm['nfs_allowed'] = item
            elif 'nfs_enabled' not in current_svm:
                current_svm['nfs_enabled'] = item
            elif 'cifs_allowed' not in current_svm:
                current_svm['cifs_allowed'] = item
            elif 'cifs_enabled' not in current_svm:
                current_svm['cifs_enabled'] = item
        elif item.startswith('svm'):
            if current_svm:
                result.append(current_svm)
            current_svm = {'name': item}
        elif item == 'running' or item == 'stopped':
            current_svm['state'] = item
        elif ':' in item:
            ip_interfaces_data = item.split('\n')
            current_svm['ip_interfaces'] = []

            for ip_data in ip_interfaces_data:
                ip, services = ip_data.split(': ')
                services_list = services.split(', ')
                ip_interface = {'ip': {'address': ip}, 'services': services_list}
                current_svm['ip_interfaces'].append(ip_interface)
        elif item.startswith('NA-SSD'):
            current_svm['cifs_name'] = item
        elif item == 'QA.LAB':
            current_svm['cifs_ad_domain'] = {'fqdn': item}
            current_svm['cifs_ad_domain_fqdn'] = item

    if current_svm:
        result.append(current_svm)

    return result


def find_differences(list1, list2):
    diff = []

    for dict1, dict2 in zip(list1, list2):
        for key in dict1.keys() | dict2.keys():
            if dict1.get(key) != dict2.get(key):
                diff.append({
                    'key': key,
                    'dict1_value': dict1.get(key),
                    'dict2_value': dict2.get(key)
                })

    return diff


def netapp_parsing_api():
    url = f"https://{}/api/.services"
    auth = HTTPBasicAuth("", "")
    response = requests.get(url, auth=auth, verify=False)
    object_name_to_delete = ""

    if response.status_code == 401:
        logger.info("Authentication required")
        return

    if response.status_code != 200:
        logger.info(f"Failed to retrieve data. Status code: {response.status_code}")
        return

    data = json.loads(response.text)
    data_dict = json.loads(json.dumps(data, default=replace_boolean))

    result_dict_list = []
    for record in data['records']:
        cifs_ad_domain = record.get('cifs', {}).get('ad_domain', {})
        result_dict = {
            'name': record['name'],
            'state': record['state'],
            'ip_interfaces': record['ip_interfaces'],
            'svm_observed': record['uuid'],
            'nfs_allowed': record['nfs']['allowed'],
            'nfs_enabled': record['nfs']['enabled'],
            'cifs_allowed': record['cifs']['allowed'],
            'cifs_enabled': record['cifs']['enabled'],
            'cifs_name': record['name'],
            'cifs_ad_domain': cifs_ad_domain,
            'cifs_ad_domain_fqdn': cifs_ad_domain.get('fqdn', ''),
        }
        result_dict_list.append(result_dict)
        return result_dict_list


def netapp_parsing_svm(result_dict_list, driver, n, m):
    svms = []

    for i in range(n, m):
        css_expression = (f"#overlay > flow-component-renderer > div > div > div:nth-child(2) "
                          f"> vaadin-vertical-layout > vaadin-grid > vaadin-grid-cell-content:nth-child({i})")
        elements = driver.find_elements(By.CSS_SELECTOR, css_expression)

        if elements:
            for element in elements:
                txt = element.text
                if txt != "":
                    if txt != 'Не наблюдается\nДобавить':
                        if txt == "Да":
                            txt = True
                        elif txt == "Нет":
                            txt = False
                        svms.append(txt)
                else:
                    try:
                        label_element = element.find_element(By.XPATH, ".//label[@title]")
                        title_text = label_element.get_attribute("title")
                        if title_text == "Да":
                            title_text = True
                        elif title_text == "Нет":
                            title_text = False
                        svms.append(title_text)
                    except NoSuchElementException:
                        pass

    result_data = parse_data(svms)

    differences = find_differences(result_dict_list, result_data)

    if differences:
        logger.info("Различия:")
        for diff in differences:
            logger.info(
                f"Ключ: {diff['key']}, Значение в result_dict_list: {diff['dict1_value']}, "
                f"Значение в result_data: {diff['dict2_value']}")
    else:
        logger.info("Списки словарей идентичны.")
