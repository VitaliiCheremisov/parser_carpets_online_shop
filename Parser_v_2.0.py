"""Парсинг ковров на сайте Venera. C авторизацией, ссылки на ковры собираются файлом Venera_links.py.
   Запускать файл Venera_links.py, который после завершения выполнения своей работы сам запустит данный файл.
   Т.е. парсинг происходит в два этапа."""
import sqlite3
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep

"""На сайте Венеры все характеристики ковров отображаются только после авторизации"""
username = "anatolii.cheremisov@gmail.com"
password = "5126787a1"

"""Настраиваем драйвер браузера"""
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()

"""Авторизуемся, заходим на страницу каждого ковра, работает для любого ковра"""
driver.get('https://venera-carpet.ru/user/auth.html')
driver.find_element(By.ID, "auth_email").send_keys(username)
driver.find_element(By.ID, "auth_password").send_keys(password)
sleep(5)
driver.find_element(By.CSS_SELECTOR, ".fancybox-close-small").click()
driver.find_element(By.CSS_SELECTOR, ".button.style-10").click()

"""Подключаемся к базе данных, к таблице с ссылками на ковер"""
con = sqlite3.connect('venera_carpets_v_2.0.db')
cur = con.cursor()
cur.execute(f"SELECT COUNT(venera_carpet_links_id) FROM venera_carpets_links")
con.commit()
carpet_max_number = cur.fetchone()[0]
for i in range(1, carpet_max_number + 1):
    con = sqlite3.connect('venera_carpets_v_2.0.db')
    cur = con.cursor()
    cur.execute(f"SELECT carpet_link FROM venera_carpets_links WHERE venera_carpet_links_id = {i}")
    # Подключаемся к базе данных, делаем запрос из таблицы ссылок, получаем ссылку. По этой ссылке переходим на
    # страничку и начинаем сбор данных о ковре
    carpet_link = cur.fetchone()[0]
    con.commit()
    url = f'https://venera-carpet.ru{carpet_link}'
    driver.get(f'{url}')
    resp = driver.page_source
    soup = BeautifulSoup(resp, 'lxml')

    """Получаем имя и цену ковра, преобразуем в подходящий для внесения в базу данных вид"""


    class CarpetVenera:
        """Базовый класс товара - "Ковёр" """
        carpet_venera_count = 0

        def __init__(self, name="Нет данных", price=000, country="Нет данных", composition="Нет данных", density=0000,
                     height_pile=000.0, provider="Venera"):
            self.name = name
            self.price = price
            self.country = country
            self.composition = composition
            self.density = density
            self.height_pile = height_pile
            self.provider = provider
            CarpetVenera.carpet_venera_count += 1

        def display_carpet_venera_count(self):
            print(f"Ковров от поставщика Venera: {CarpetVenera.carpet_venera_count}")

        def display_carpet_venera(self):
            print(f"Название: {self.name}, Цена_кв_м: {self.price} Страна: {self.country}, Состав: "
                  f"{self.composition}, Плотность: {self.density}, Высота ворса: {self.height_pile}")


    name = soup.find('h1').get_text()
    CarpetVenera.name = name
    # Убирает такие товары, как ковровые дорожки, они нам не нужны
    if name.find('Ковер') != -1:
        # На некоторых коврах приходят разные строки цены, поэтому два варианта обработки приходящей строки, также есть
        # ковры, у которых нет цены вообще
        try:
            price_ = str(soup.find('div', attrs={'class': "current"}).get_text())
            price = price_.split()
            CarpetVenera.price = int(price[0])
        except AttributeError:
            CarpetVenera.price = 0

        """Получаем подробные характеристики ковра, удаляем ненужные нам строки"""
        params = list()
        for param in soup.find_all('div', attrs={'class': "title"}):
            param_text = param.text
            param_text = param_text.split()
            param_text = ''.join(param_text)
            params.append(param_text)
        remove_list = ['Телефон88007700562', 'Кабинет:300Анатолий', 'Выход', '88007700562', '', 'info@venera-carpet.ru',
                       'Меню', '', 'Информацияотоваре']


        def func_remove(r_list: list) -> None:
            """Эта функция удаляет ненужные элементы из приходящего списка, остаются те, которые подходят для внесения в
            базу данных, но требуют дополнительной обработки"""
            for element in r_list:
                params.remove(element)


        func_remove(remove_list)

        """Здесь проходит анализ характеристик ковра. Проверяется наличие каждой характеристики. Если у ковра 
        отсутствует какая-то характеристика, то в базу данных будет вноситься строка 'Нет данных'"""
        CarpetVenera.country = "Нет данных"
        CarpetVenera.density = 0000
        CarpetVenera.height_pile = 000.0
        CarpetVenera.composition = "Нет данных"
        for k in range(len(params)):
            if params[k].find('Странапроизводства') != -1:
                CarpetVenera.country = params[k].partition(':')[2]
                break
        for k in range(len(params)):
            if params[k].find('Кодсостава') != -1:
                CarpetVenera.composition = params[k].partition(':')[2]
                break
        for k in range(len(params)):
            if params[k].find('Плотность') != -1:
                CarpetVenera.density = int((params[k].partition(':')[2]).partition('т')[0])
                break
        for k in range(len(params)):
            if params[k].find('Высотаворса') != -1:
                CarpetVenera.height_pile = float((params[k].partition(':')[2]).partition('м')[0])
                break
        # Создаем сущность 'carpet', которая представляет собой набор подготовленных для внесения свойств ковра
        CarpetVenera.provider = 'Venera'
        carpet = (CarpetVenera.name, CarpetVenera.price, CarpetVenera.country, CarpetVenera.composition,
                  CarpetVenera.density, CarpetVenera.height_pile, CarpetVenera.provider)

        """Получаем ссылки на фотографии к каждому ковру"""
        img_list = list()
        img_db = list()
        img_soup = soup.find_all('img', src=True)
        for link_img in img_soup:
            img_list.append(link_img['src'])
        for k in range(len(img_list)):
            if img_list[k].find('https://vnstatic.net/venera/big') != -1:
                img_db.append(img_list[k])

        """Получаем размеры ковров и дорожек"""
        size_list = list()
        for elem in soup.find_all('td', attrs={'class': "sizeCol"}):
            size_ = elem.get_text()
            size = size_.split()
            size_str = size[0]
            size_list.append(size_str)

        """Подключаемся к заранее созданной базе и вносим запись"""
        con = sqlite3.connect('venera_carpets_v_2.0.db')
        cur = con.cursor()
        # Вносим запись в первую таблицу с характеристиками ковра
        cur.execute(f"INSERT INTO carpets (name, price, country, composition, density, height_pile, provider) "
                    f"VALUES (?, ?, ?, ?, ?, ?, ?);", carpet)
        # Готовим внесение id текущего ковра для внесения в базу. При такой привязке каждое фото ковра будет иметь
        # зависимость с текущим ковром
        cur.execute(f"SELECT carpet_id FROM carpets WHERE name = '{CarpetVenera.name}' ")
        carpet_id = cur.fetchone()[0]


        def insert_or_create(table_name: str, table_foreign_name: str, table_colomn: str, table_foreign_colomn: str,
                             list_args: list, ) -> None:
            """Эта функция будет проверять наличие параметра ковра в таблице, делать запись элемента в таблицу и
            обновлять такие параметры, как фото, размеры ковров или дорожек"""
            for arg in list_args:
                rows_db = list()
                cur.execute(f"SELECT {table_colomn} FROM {table_name};")
                insert = (arg, carpet_id)
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


        # Вызываем функцию, которая вносит в базу фотографии каждого ковра, вне зависимости от их числа
        insert_or_create('images', 't_images', 'image', 't_image', img_db)

        # Вызываем функцию, которая вносит размеры каждого ковра, вне зависимости от их числа
        insert_or_create('carpet_sizes', 'c_sizes', 'carpet_size', 'c_size', size_list)

        # Записи внесены, отключаемся от базы данных, переходим к ссылке на следующий ковер и повторяем алгоритм
        con.commit()
    else:
        continue
"""Когда все записи успешно внесены, закрываем браузер"""
driver.close()
