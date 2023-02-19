"""Парсинг ковров на сайте Avalon, с авторизацией.
   Обновляет базу данных, вносит сведения о цене, размерах и фото ковров, собранных файлом Avalon_non_admin.py.
   Запускать сначала файл Avalon_links.py, который отработав запустит Avalon_non_admin.py. Avalon_non_admin.py, 
   отработав, в свою очередь запустит данный файл, т.е. парсинг происходит в три этапа.       """
import sqlite3
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep

"""На сайте Венеры все характеристики ковров отображаются только после авторизации"""
username = "anatolii.cheremisov@gmail.ru"
password = "hapkido161"

"""Настраиваем драйвер браузера"""
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()

"""Настраиваем авторизацию на сайте"""
driver.get(f'https://avalon-carpet.ru/')
# Текущее окно назначается главной страницей для webdriver
main_page = driver.current_window_handle
# Прожимаем кнопку входа, для активации всплывающего окна авторизации
driver.find_element(By.CSS_SELECTOR, "#mm-0 > div.site-box > div.a3-fixed-container > header > div.a3-static-header > "
                                     "div > div.a3-rselector > div > a.trigger-login").click()
sleep(5)
# Приходится заранее создать пустую строку, чтобы webdriver потом смог переключиться на всплывающее окно авторизации
login_page = ""
# Переключаем webdriver на всплывающее окно авторизации
for handle in driver.window_handles:
    if handle != main_page:
        login_page = handle
driver.switch_to.window(login_page)
# Вводим логин и пароль, авторизуемся
driver.find_element(By.CSS_SELECTOR, "#infobox-content > div > form > dl > dd:nth-child(2) > input[type=text]"). \
    send_keys(username)
driver.find_element(By.CSS_SELECTOR, "#infobox-content > div > form > dl > dd:nth-child(4) > input[type=password]"). \
    send_keys(password)
driver.find_element(By.CSS_SELECTOR, "#infobox-content > div > form > button").click()
sleep(5)
# Выбираем склад товара Ростов-на-Дону, авторизация выполнена
driver.find_element(By.CSS_SELECTOR, "#infobox-content > div > form > p > input[type=checkbox]:nth-child(3)").click()
driver.find_element(By.CSS_SELECTOR, "#infobox-content > div > form > input.button").click()
sleep(5)


def admin_first_page_country_parser(country: str) -> None:
    """Эта функция собирает данные на все ковры первой страницы заданной страны и внесет их в базу данных"""
    driver.get(f"https://avalon-carpet.ru/{country}/")
    for i in range(1, 25):
        """Настраиваем поочередный клик по каждому ковру на странице"""
        carpet_XPath = f"""//*[@id="mm-0"]/div[2]/section/div/div[2]/ul/li[{i}]"""
        driver.find_element(By.XPATH, carpet_XPath).click()
        sleep(5)
        resp = driver.page_source
        soup = BeautifulSoup(resp, 'lxml')

        class CarpetAvalonAdmin:
            """Базовый класс товара - "Ковёр" """
            carpet_avalon_admin_count = 0

            def __init__(self, name="Нет данных", price=000):
                self.name = name
                self.price = price

                CarpetAvalonAdmin.carpet_avalon_admin_count += 1

            def display_carpet_venera(self):
                print(f"Название: {self.name}, Цена_кв_м: {self.price}")

        """Получаем имя ковра"""
        name = soup.find('h3').get_text()
        CarpetAvalonAdmin.name = f"Ковер {name}"

        """Получаем цену ковра"""
        price_list = list()
        for price in soup.find_all('b'):
            price_list.append(price.get_text())
        remove_list = ['Корзина', '0.0 м2', '0.0 кг', '0 шт', '0 руб.', 'Отображаются склады']

        def clear_price_list(r_list: list) -> None:
            for elem in r_list:
                price_list.remove(elem)

        clear_price_list(remove_list)
        CarpetAvalonAdmin.price = int(price_list[0])

        """Получаем ссылки на фото ковра"""
        parsing_foto_list = list()
        foto_list = list()
        for foto in soup.find_all('img', src=True):
            parsing_foto_list.append(foto['src'])
        for elem in parsing_foto_list:
            if elem.find('/cache/450x600/') != -1:
                foto_list.append(f'https://avalon-carpet.ru{elem}')
                break
        for elem in parsing_foto_list:
            if elem.find('/cache/49x65/') != -1:
                foto_list.append(f"https://avalon-carpet.ru{elem}")

        """Получаем размеры каждого ковра, имеющиеся в наличии"""
        full_size_list = list()
        size_list = list()
        for elem in soup.find_all('td'):
            full_size_list.append(elem.get_text())
        for size in full_size_list:
            if size.find('м.') != -1:
                size_list.append(size)

        """Подключаемся к базе данных"""
        con = sqlite3.connect('venera_carpets_v_2.0.db')
        cur = con.cursor()
        # Обновляем цену в базе данных
        cur.execute(f"UPDATE carpets SET price = {CarpetAvalonAdmin.price} WHERE name = '{CarpetAvalonAdmin.name}' ")
        # Готовим внесение id текущего ковра для внесения в базу. При такой привязке размер каждого ковра будет иметь
        # зависимость с текущим ковром
        cur.execute(f"SELECT carpet_id FROM carpets WHERE name = '{CarpetAvalonAdmin.name}' ")
        # Ковры без цены пропускаются
        try:
            avalon_carpet_id = cur.fetchone()[0]
        except TypeError:
            continue

        def insert_or_create(table_name: str, table_foreign_name: str, table_colomn: str, table_foreign_colomn: str,
                             list_args: list, ) -> None:
            """Эта функция будет проверять наличие параметра ковра в таблице, делать запись элемента в таблицу и
            обновлять такие параметры, как фото, размеры ковров или дорожек"""
            for arg in list_args:
                rows_db = list()
                cur.execute(f"SELECT {table_colomn} FROM {table_name};")
                insert = (arg, avalon_carpet_id)
                rows = cur.fetchall()
                for element in rows:
                    rows_db.append(element[0])  # Метод .fetchall() отдает список с кортежами из одного элемента,
                    # поэтому для поиска наличия аргумента преобразуем сохраняем аргумент в другой список уже
                    # преобразованные в строку.
                if arg in rows_db:
                    # Если аргумент имеется в таблице, то тогда просто делаем запись в связующую таблицу, тем самым
                    # избегаем дублирования записей в таблице
                    cur.execute(f"INSERT INTO {table_foreign_name} ({table_foreign_colomn}, carpet_id) "
                                f"VALUES (?, ?);", insert)
                else:
                    # Если аргумента в таблице нет, то заносим его в таблицу, а потом делаем запись в связующую таблицу
                    cur.execute(f"INSERT INTO {table_name} ({table_colomn}) VALUES (?);", [arg])
                    cur.execute(f"INSERT INTO {table_foreign_name} ({table_foreign_colomn}, carpet_id) "
                                f"VALUES (?, ?);", insert)
        # Вызываем функцию, которая вносит в базу размеры каждого ковра, вне зависимости от их числа
        insert_or_create('images', 't_images', 'image', 't_image', foto_list)
        # Вызываем функцию, которая вносит в базу фото ковра
        insert_or_create('carpet_sizes', 'c_sizes', 'carpet_size', 'c_size', size_list)
        con.commit()


def admin_other_page_country_parser(country: str, page_max_number: int) -> None:
    """Эта функция собирает данные на все ковры следующих страниц заданной страны и внесет их в базу данных.
       Алгоритм такой же, как и в функции парсинг первой страницы выбранной страны."""
    for k in range(1, page_max_number + 1):
        driver.get(f"https://avalon-carpet.ru/{country}/page-{k}/")
        for i in range(1, 25):
            """Настраиваем поочередный клик по каждому ковру на странице"""
            carpet_XPath = f"""//*[@id="mm-0"]/div[2]/section/div/div[2]/ul/li[{i}]"""
            try:
                driver.find_element(By.XPATH, carpet_XPath).click()
            except:
                return
            sleep(5)
            resp = driver.page_source
            soup = BeautifulSoup(resp, 'lxml')

            class CarpetAvalonAdmin:
                """Базовый класс товара - "Ковёр" """
                carpet_avalon_admin_count = 0

                def __init__(self, name="Нет данных", price=000):
                    self.name = name
                    self.price = price

                    CarpetAvalonAdmin.carpet_avalon_admin_count += 1

                def display_carpet_venera(self):
                    print(f"Название: {self.name}, Цена_кв_м: {self.price}")

            """Получаем имя ковра"""
            name = soup.find('h3').get_text()
            CarpetAvalonAdmin.name = f"Ковер {name}"

            """Получаем цену ковра"""
            price_list = list()
            for price in soup.find_all('b'):
                price_list.append(price.get_text())
            remove_list = ['Корзина', '0.0 м2', '0.0 кг', '0 шт', '0 руб.', 'Отображаются склады']

            def clear_price_list(r_list: list) -> None:
                for elem in r_list:
                    price_list.remove(elem)

            clear_price_list(remove_list)
            try:
                CarpetAvalonAdmin.price = int(price_list[0])
            except IndexError:
                return

            """Получаем ссылки на фото ковра"""
            parsing_foto_list = list()
            foto_list = list()
            for foto in soup.find_all('img', src=True):
                parsing_foto_list.append(foto['src'])
            for elem in parsing_foto_list:
                if elem.find('/cache/450x600/') != -1:
                    foto_list.append(f'https://avalon-carpet.ru{elem}')
                    break
            for elem in parsing_foto_list:
                if elem.find('/cache/49x65/') != -1:
                    foto_list.append(f"https://avalon-carpet.ru{elem}")

            """Получаем размеры каждого ковра, имеющиеся в наличии"""
            full_size_list = list()
            size_list = list()
            for elem in soup.find_all('td'):
                full_size_list.append(elem.get_text())
            for size in full_size_list:
                if size.find('м.') != -1:
                    size_list.append(size)

            """Подключаемся к базе данных"""
            con = sqlite3.connect('venera_carpets_v_2.0.db')
            cur = con.cursor()
            # Готовим внесение id текущего ковра для внесения в базу. При такой привязке размер каждого ковра будет
            # иметь зависимость с текущим ковром
            cur.execute(f"UPDATE carpets SET price = {CarpetAvalonAdmin.price} WHERE name = '{CarpetAvalonAdmin.name}'")
            cur.execute(f"SELECT carpet_id FROM carpets WHERE name = '{CarpetAvalonAdmin.name}' ")
            try:
                avalon_carpet_id = cur.fetchone()[0]
            except TypeError:
                continue

            def insert_or_create(table_name: str, table_foreign_name: str, table_colomn: str, table_foreign_colomn: str,
                                 list_args: list, ) -> None:
                """Эта функция будет проверять наличие параметра ковра в таблице, делать запись элемента в таблицу и
                обновлять такие параметры, как фото, размеры ковров или дорожек"""
                for arg in list_args:
                    rows_db = list()
                    cur.execute(f"SELECT {table_colomn} FROM {table_name};")
                    insert = (arg, avalon_carpet_id)
                    rows = cur.fetchall()
                    for element in rows:
                        rows_db.append(element[0])  # Метод .fetchall() отдает список с кортежами из одного элемента,
                        # поэтому для поиска наличия аргумента преобразуем сохраняем аргумент в другой список уже
                        # преобразованные в строку.
                    if arg in rows_db:
                        # Если аргумент имеется в таблице, то тогда просто делаем запись в связующую таблицу, тем самым
                        # избегаем дублирования записей в таблице
                        cur.execute(f"INSERT INTO {table_foreign_name} ({table_foreign_colomn}, carpet_id) "
                                    f"VALUES (?, ?);", insert)
                    else:
                        # Если аргумента в таблице нет, то заносим его в таблицу, а потом делаем запись в связующую
                        # таблицу
                        cur.execute(f"INSERT INTO {table_name} ({table_colomn}) VALUES (?);", [arg])
                        cur.execute(f"INSERT INTO {table_foreign_name} ({table_foreign_colomn}, carpet_id) "
                                    f"VALUES (?, ?);", insert)
            # Вызываем функцию, которая вносит в базу размеры каждого ковра, вне зависимости от их числа
            insert_or_create('images', 't_images', 'image', 't_image', foto_list)
            # Вызываем функцию, которая вносит в базу фото ковра
            insert_or_create('carpet_sizes', 'c_sizes', 'carpet_size', 'c_size', size_list)
            con.commit()


def start_admin_carpet_parsing(country: str, page_max_number: int) -> None:
    """Эта функция вызывает парсинг главной страницы указанной страны производителя, а затем все последующие страницы
       этой страны, число страниц принимает на вход как аргумент."""
    admin_first_page_country_parser(country=country)
    admin_other_page_country_parser(country=country, page_max_number=page_max_number)


start_admin_carpet_parsing('tureckie-kovry', 30)
start_admin_carpet_parsing('iranskie-kovry', 7)
start_admin_carpet_parsing('rossijskie-kovry', 1)
country_list = ['tureckie-kovry', 'belorusskie-kovry', 'belgijskie-kovry', 'iranskie-kovry', 'kitajskie-kovry',
                'rossijskie-kovry', 'uzbekskie-kovry']

"""Когда все записи успешно внесены, закрываем браузер"""
driver.close()
print("Ковры производителя Avalon внесены, с ценой, размерами и ссылками на фото")
