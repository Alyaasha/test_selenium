import requests
from requests.auth import HTTPBasicAuth

name_file = open('name.txt', 'r', encoding="utf-8")
full_name_file = open('full_name.txt', 'r', encoding="utf-8")
description_file = open('description.txt', 'r', encoding="utf-8")
sid_file = open('sid.txt', 'r', encoding="utf-8")
for _ in range(50):
    name = name_file.readline().strip()
    full_name = full_name_file.readline().strip()
    description = description_file.readline().strip()
    sid = sid_file.readline().strip()
    # # Данные для запроса
    # data = {
    #     "name": name,
    #     "full_name": full_name,
    #     "description": description,
    #     "account_disabled": False,
    #     "password": "",
    #     "svm": {
    #         "uuid": ""
    #     }
    # }
    #
    # # URL и заголовки для запроса
    # url1 = f''
    auth = HTTPBasicAuth("", "")
    #
    # # Отправка POST запроса
    # response1 = requests.post(url1, auth=auth, json=data, verify=False)

    url2 = f""
    data2 = {"name": name}
    response2 = requests.post(url2, auth=auth, json=data2, verify=False)

    # Печать результатов
    print(f"Iteration: {_ + 1}")
    # print(response1.status_code)
    # print(response1.text)
    print(response2.status_code)
    print(response2.text)
name_file.close()
full_name_file.close()
description_file.close()
sid_file.close()