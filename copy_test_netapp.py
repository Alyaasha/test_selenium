import json
import sys
import time
import requests
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth
from selenium.webdriver import ActionChains
from selenium.webdriver.support import expected_conditions as EC
import allure
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, \
    ElementClickInterceptedException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
import psycopg2

chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument('--ignore-certificate-errors')
# chrome_options.add_argument("--headless")
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--no-sandbox')

driver = webdriver.Chrome(options=chrome_options)

wait = WebDriverWait(driver, 10)




url = ""
def set_config(db_config, url):
   # Установка настроек бд
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    try:
        cur.execute(f"""
                   update config.process 
                   set config = '{{
                       
                   }}'
                   where id=0;
               """)
        conn.commit()
        print("Пароль был сброшен")
    except Exception as e:
        print(f"Ошибка при обновлении конфигурации: {e}")
    finally:
        cur.close()
        conn.close()

def update_password(db_config):
    # Установка пароля в бд
    conn = psycopg2.connect(*db_config)
    cur = conn.cursor()

    try:
        cur.execute("""
            update ui."user"
            set "password" = ''
            where id = 1;
        """)
        conn.commit()
        print("Пароль был установлен")
    except Exception as e:
        print(f"Ошибка при обновлении пароля пользователя: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    # Замените значения на ваши данные подключения к базе данных
    db_config = {
        "host": "",
        "database": "",
        "user": "",
        "password": ""
    }

    set_config(db_config, url)
    update_user_password(db_config, password_hash)


def open_webpage(url):
    try:
        # Вход на страницу
        driver.get(url=url + '/login')
        driver.implicitly_wait(10)
        login_input = driver.find_element(By.XPATH, '//*[@id="vaadinLoginUsername"]/input')
        login_input.send_keys("orlanadmin")
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys('admin')
        password_input.send_keys(Keys.ENTER)
        driver.implicitly_wait(10)
        # Настройка пароля
        try:
            password_change_window = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Изменение пароля')]"))
            )
            new_password_input = password_change_window.find_element(By.XPATH,
                                                                     "//td[contains(text(), 'Новый пароль:')]/following-sibling::td//vaadin-password-field")
            confirm_password_input = password_change_window.find_element(By.XPATH,
                                                                         "//td[contains(text(), 'Подтверждение пароля:')]/following-sibling::td//vaadin-password-field")
            new_password_input.send_keys("admin")
            confirm_password_input.send_keys("admin")
            time.sleep(3)
            wait.until(EC.element_to_be_clickable((By.XPATH, "//vaadin-button[text()='OK']"))).click()
            time.sleep(3)
        except NoSuchElementException:
            pass
        except TimeoutException:
            pass

    except NoSuchElementException as nse:
        print(f"Элемент не найден из-за ошибки - {nse}")
        driver.refresh()

# Обновление страницы
def restart_driver(url):
    global driver
    if driver:
        driver.refresh()


# Открытие страницы, ввод логина и пароля
print(url)
open_webpage(url)

# Переходим на вкладку Настройки администратора
driver.get(url=url + '/adminsettings')
driver.implicitly_wait(10)
print("Настройки админимстратора")

api_address, username_api, pwd_api = "", "", ""

# ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ ИНФОРМАЦИИ ИЗ АПИ
@allure.step("Получение информации ")
def netapp_parsing_api(url_api, url_cluster, svm_name):
    with allure.step("Отправка запросов к API"):
        auth = HTTPBasicAuth("", "")
        response_svm = requests.get(url_api, auth=auth, verify=False)
        response_cluster = requests.get(url_cluster, auth=auth, verify=False)

    with allure.step("Проверка ответа от API"):
        if response_svm.status_code == 401:
            print("Authentication required")
            return

        if response_svm.status_code != 200:
            print(f"Failed to retrieve data. Status code: {response_svm.status_code}")
            return

    with allure.step("Обработка данных от API"):
        data_svm = json.loads(response_svm.text)
        data_cluster = json.loads(response_cluster.text)

        netapp_release = data_cluster['version']['full']
        netapp_name = data_cluster['name']

        for record in data_svm['records']:
            if record['name'] == '':
                UUID = record['uuid']
                name = record['cifs']['name']
                ad_domain = record['cifs']['ad_domain']['fqdn']
                break

        url_nfs = f"https://{api_address}/api"
        url_cifs = f"https://{api_address}/api"

        response_nfs = requests.get(url_nfs, auth=auth, verify=False)
        response_cifs = requests.get(url_cifs, auth=auth, verify=False)

        data_nfs = json.loads(response_nfs.text)
        data_cifs = json.loads(response_cifs.text)

    with allure.step("Сбор информации"):
        # Получение информации о каждом SVM
        svm_info_list = []
        for record in data_svm.get('records', []):
            svm_info = {
                "Имя": record.get('name'),
                "Состояние": record.get('state'),
            }
            svm_info_list.append(svm_info)

    return svm_info_list, netapp_release, netapp_name, name, ad_domain, data_nfs, data_cifs



@allure.step("Добавление")
def add_cluster(address, username, pwd, name_cluster):
    try:
        with allure.step("Переход к странице добавления"):
            # Переходим на вкладку
            driver.find_element(By.XPATH, "//*[contains(text(), '')]").click()
            driver.implicitly_wait(10)
            print('')

            group_servers = driver.find_element(By.XPATH, '//vaadin-tab[text()=""]')
            driver.execute_script("arguments[0].scrollIntoView(true);", group_servers)
            group_servers.click()
            driver.implicitly_wait(10)
            print('')

            try:
                # На случай, если не настроена
                if not (driver.find_element(By.XPATH, "//vaadin-grid-cell-content[text()='']")):
                    print(f"")
                    flag = True
                    while flag:
                        try:
                            button = driver.find_element(By.XPATH, "//*[contains(text(), 'Создать')]")
                            driver.implicitly_wait(10)
                            button.click()
                            flag = False
                        except ElementNotInteractableException as ex:
                            flag = True
                            print(f"fail - {ex}")
                            driver.refresh()
                            print("Нажали на Создать")

                    # Заполняем поле
                    name_field = driver.find_element(By.XPATH, "//vaadin-text-field")
                    name_field.send_keys("")
                    print("Заполняем поле названия")

                    # Нажимаем на кнопку "Сохранить"
                    save_button = driver.find_element(By.XPATH, "//vaadin-button[text()='Сохранить']")
                    save_button.click()
                    print("Нажали на Сохранить")
            except NoSuchElementException:
                pass
                
            tab_elem = driver.find_element(By.XPATH, '//vaadin-tab[text()=""]')
            driver.execute_script("arguments[0].scrollIntoView(true);", tab_elem)
            tab_elem.click()
            driver.implicitly_wait(10)
            print('')

            driver.find_element(By.XPATH, "//*[contains(text(), '')]").click()
            driver.implicitly_wait(10)
            print('')

            # Добавляем
            driver.find_element(By.XPATH, "//*[contains(text(), '')]").click()
            driver.implicitly_wait(10)
            print('')

            try:
                driver.find_element(By.XPATH, f'//label[contains(text(), "{name_cluster}")]')
                print(f"Ошибка при добавлении.")
                return
            except NoSuchElementException:
                pass

            driver.find_element(By.XPATH, "//*[contains(text(), 'Добавить')]").click()
            print('Добавить')
            time.sleep(2)

    # Предполагаю, что элемент может не найтись на странице, отлавливаю эту ошибку
    # На всякий случай буду перезагружать драйвер при ошибке ненайденного элемента
    except NoSuchElementException as nse:
        print(f"Элемент не найден из-за ошибки - {nse}")
        restart_driver(url)
    except ElementClickInterceptedException as nse:
        print(f"Элемент не найден из-за ошибки - {nse}")
        restart_driver(url)

    with allure.step("Ввод данных"):
        ip_label = driver.find_element(By.XPATH,
                                       "//*[contains(text(), '')]/following-sibling::td")
        ip_label.click()
        ActionChains(driver).send_keys(f"{address}").perform()
        print('')

        driver.find_element(By.XPATH,
                            "//*[contains(text(), '')]/following-sibling::td").click()
        ActionChains(driver).send_keys(username).perform()
        print('')

        driver.find_element(By.XPATH,
                            "//*[contains(text(), '')]/following-sibling::td").click()
        ActionChains(driver).send_keys(pwd).perform()
        driver.implicitly_wait(10)
        print('')

        ip_label.click()

    try:
        with allure.step("Проверка кластера"):
            driver.find_element(By.XPATH,
                                '//div[@class="draggable draggable-leaf-only"]//vaadin-button[text()="Проверить"]')
            check_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//div[@class="draggable draggable-leaf-only"]//vaadin-button[text()="Проверить"]')))
            check_btn.click()
            print('Проверить')

            time.sleep(10)

            driver.find_element(By.XPATH, "//vaadin-button[text()='Закрыть']").click()

            print("")
            name_cl_btn = driver.find_element(By.XPATH,
                                              '//tr[td[text()=""]]/td/vaadin-text-field')
            name_cl_txt = name_cl_btn.get_attribute('value')
            print(name_cl_txt)

            print("")
            version_cl_btn = driver.find_element(By.XPATH,
                                                 '//tr[td[text()=""]]/td/vaadin-text-field')
            version_cl_txt = version_cl_btn.get_attribute('value')
            print(version_cl_txt)

    # Предполагаю, что элемент может не найтись на странице, отлавливаю эту ошибку
    except NoSuchElementException as nse:
        print(f"Элемент не найден из-за ошибки - {nse}")
        restart_driver(url)
    except ElementClickInterceptedException as nse:
        print(f"Элемент не найден из-за ошибки - {nse}")
        restart_driver(url)

    with allure.step("Проверка корректности добавления кластера"):
        # Проверяем, что добавился верно (верно указаны имя кластера и версия), после чего сохраняем
        if not (version_cl_txt == "") and not (
                name_cl_txt == ""):
            print('произошла ошибка при добавлении')
            exit()

        save_btn = driver.find_element(By.XPATH,
                                       '//div[@class="draggable draggable-leaf-only"]//vaadin-button[text()="Сохранить"]')
        driver.execute_script("arguments[0].scrollIntoView(true);", save_btn)
        wait.until(EC.element_to_be_clickable(save_btn))
        save_btn.click()
        driver.implicitly_wait(10)
        print('Сохранить')


if __name__ == "__main__":
    url_api = f''
    url_cluster = f""

    short_name_cluster = ""

    # Запуск
    add_cluster(address=api_address, username=username_api, pwd=pwd_api, name_cluster=short_name_cluster)

    name_of_cluster, servers, svm_name = f"", "", ""


    # Получаем необхожимые для проверок переменные
    nettap_txt_api, netapp_release, netapp_name, name, ad_domain, data_nfs, data_cifs = netapp_parsing_api(
        url_api, url_cluster, svm_name)
    # Запуск добавления
    restart_driver(url)

    print('тест завершился без ошибок')

    # Выходим из драйвера
    driver.quit()

