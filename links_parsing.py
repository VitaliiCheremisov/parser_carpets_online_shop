"""Парсинг ссылок ковров на сайте Авалона с внесением этих ссылок в таблицу.
   После завершения запускает файл Avalon_non_admin."""
import sqlite3
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

"""Настраиваем драйвер браузера"""
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()


def get_first_page_links_for_country(country: str) -> None:
    """Эта функция найдет все ссылки на ковры первой страницы заданной страны и внесет их в базу данных ссылок на
    ковры """
    driver.get(f"https://avalon-carpet.ru/{country}/")
    link_list = list()
    country_link_list = list()
    # Создаем словарь с одним элементом. Нужен для временного хранения данных. Значение этого элемента и будет ссылкой
    # на ковер, которая будет вноситься в базу
    carpet_link_dict = {'carpet_link': ''}
    resp = driver.page_source
    soup = BeautifulSoup(resp, 'lxml')
    # Фильтруем строки от ненужной информации и получаем ссылку на страничку каждого конкретного ковра, вносим её в
    # список
    for a in soup.find_all('a', attrs={'rel': "nofollow"}, href=True):
        link_list.append(a['href'])
    for link in link_list:
        if link.find('/product/') != -1:
            country_link_list.append(link)

    for carpet_link in country_link_list:
        carpet_link_dict['carpet_link'] = carpet_link
        con = sqlite3.connect('venera_carpets_v_2.0.db')
        cur = con.cursor()
        cur.execute("INSERT INTO avalon_carpets_links (carpet_link) VALUES (?)", [carpet_link_dict['carpet_link']])
        # [carpet_link_dict['carpet_link']] специально приходится брать в квадратные скобки, что значение словаря не
        # воспринималось как итерируемый объект
        con.commit()
    # Вносим все полученные ссылки в базу данных. В результате получаем таблицу ссылок на все ковры на сайте Авалона


def get_other_pages_links_for_country(country: str, page_max_number: int) -> None:
    """Эта функция найдет все ссылки на ковры последующих страниц заданной страны и внесет их в базу данных ссылок на
    ковры """
    for i in range(1, page_max_number):
        driver.get(f"https://avalon-carpet.ru/{country}/page-{i}/")
        link_list = list()
        country_link_list = list()
        # Создаем словарь с одним элементом. Нужен для временного хранения данных.
        # Значение этого элемента и будет ссылкой на ковер, которая будет вноситься в базу
        carpet_link_dict = {'carpet_link': ''}
        resp = driver.page_source
        soup = BeautifulSoup(resp, 'lxml')
        # Фильтруем строки от ненужной информации и получаем ссылку на страничку каждого конкретного ковра, вносим её в
        # список
        for a in soup.find_all('a', attrs={'rel': "nofollow"}, href=True):
            link_list.append(a['href'])
        for link in link_list:
            if link.find('/product/') != -1:
                country_link_list.append(link)

        for carpet_link in country_link_list:
            carpet_link_dict['carpet_link'] = carpet_link
            con = sqlite3.connect('venera_carpets_v_2.0.db')
            cur = con.cursor()
            cur.execute("INSERT INTO avalon_carpets_links (carpet_link) VALUES (?)", [carpet_link_dict['carpet_link']])
            # [carpet_link_dict['carpet_link']] специально приходится брать в квадратные скобки, что значение словаря не
            # воспринималось как итерируемый объект
            con.commit()
        # Вносим все полученные ссылки в базу данных. В результате получаем таблицу ссылок на все ковры на сайте Авалона


def get_carpet_links(country: str, page_max_number: int) -> None:
    """Эта функция вызывает парсинг ссылок ковров главной страницы указанной страны производителя, а затем всех
       последующих ковров этой страны на следующих страницах, число страниц принимает на вход как аргумент."""
    get_first_page_links_for_country(country=country)
    get_other_pages_links_for_country(country=country, page_max_number=page_max_number)


# Нужно только вызвать функцию с нужной страной и количеством страниц.
get_carpet_links('tureckie-kovry', 30)
get_carpet_links('iranskie-kovry', 7)
get_carpet_links('rossijskie-kovry', 1)
country_list = ['tureckie-kovry', 'belorusskie-kovry', 'belgijskie-kovry', 'iranskie-kovry', 'kitajskie-kovry',
                'rossijskie-kovry', 'uzbekskie-kovry']

"""Когда все записи успешно внесены, закрываем браузер"""
driver.close()

"""Делаем запрос в базу данных, чтобы знать ожидаемое количество ковров"""
con = sqlite3.connect('venera_carpets_v_2.0.db')
cur = con.cursor()
cur.execute("SELECT COUNT(avalon_carpet_links_id) FROM avalon_carpets_links")
avalon_carpets_number = cur.fetchone()[0]
print(f"Получено число ссылок ковров 'Avalon': {avalon_carpets_number}")
# Запускаем файл non_authorized_parsing.py для начала парсинга ковров
exec(open('non_authorized_parsing.py', encoding='utf8').read())
