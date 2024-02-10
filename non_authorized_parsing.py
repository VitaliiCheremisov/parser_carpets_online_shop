"""Парсинг ковров на сайте Avalon. Без авторизации, ссылки на ковры собираются файлом links_parsing.py.
   После завершения запускает файл authorized_parsing.py"""
import sqlite3
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

"""Настраиваем драйвер браузера"""
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()

"""Заходим на страничку ковра"""
carpet_link = ""
con = sqlite3.connect('venera_carpets_v_2.0.db')
cur = con.cursor()
cur.execute(f"SELECT COUNT(avalon_carpet_links_id) FROM avalon_carpets_links")
con.commit()
carpet_max_number = cur.fetchone()[0]
for i in range(1, carpet_max_number + 1):
    # Подключаемся к базе данных, делаем запрос из таблицы ссылок, получаем ссылку. По этой ссылке переходим на
    # страничку и начинаем сбор данных о ковре
    con = sqlite3.connect('venera_carpets_v_2.0.db')
    cur = con.cursor()
    cur.execute(f"SELECT carpet_link FROM avalon_carpets_links WHERE avalon_carpet_links_id = {i}")
    carpet_link = cur.fetchone()[0]
    con.commit()
    driver.get(f"https://avalon-carpet.ru/{carpet_link}")
    resp = driver.page_source
    soup = BeautifulSoup(resp, 'lxml')

    class CarpetAvalon:
        """Базовый класс товара - "Ковёр" """
        carpet_avalon_count = 0

        def __init__(self, name="Нет данных", price=000, country="Нет данных", composition="Нет данных", density=0000,
                     height_pile=000.0, provider="Avalon"):
            self.name = name
            self.price = price
            self.country = country
            self.composition = composition
            self.density = density
            self.height_pile = height_pile
            self.provider = provider
            CarpetAvalon.carpet_avalon_count += 1

        def display_carpet_venera(self):
            print(f"Название: {self.name}, Цена_кв_м: {self.price} Страна: {self.country}, Состав: "
                  f"{self.composition}, Плотность: {self.density}, Высота ворса: {self.height_pile}")
    """Получаем имя название ковра"""
    CarpetAvalon.name = soup.find('h1').get_text()
    CarpetAvalon.price = 000

    """Получаем ссылку на главное фото ковра"""
    elem_set = set()
    pict_link = ""
    for elem in soup.find_all('img', alt=True, src=True):
        if elem.find(f'{CarpetAvalon.name}') != -1:
            elem_set.add(elem['src'])
    for elem in elem_set:
        if elem.find('/cache/523x895') != -1:
            pict_link = f'https://avalon-carpet.ru/{elem}'

    """Получаем характеристики ковра"""
    elem_list = list()
    features_list = list()
    for elem in soup.find_all('dl'):
        elem_list.append(''.join(elem.text.split()))
    add_list = ['Странапроизводитель', 'Производитель', 'Коллекция', 'Дизайн', 'Материал', 'Основа', 'Размещение',
                'Форма', 'Фактура', 'Плотностьворса', 'Высотаворса', 'Методпроизводства']


    def add_func(arg_list: list) -> None:
        """Эта функция проверяет наличие нужных нам элементов в приходящем списке, затем добавляем проверенные элементы в
        другой список"""
        for arg in arg_list:
            for element in elem_list:
                if element.find(arg) != -1 and element.find('Размеры') == -1:
                    features_list.append(element)


    add_func(add_list)

    """Здесь проходит анализ характеристик ковра. Проверяется наличие каждой характеристики. Если у ковра отсутствует 
        какая-то характеристика, то в базу данных вносится строка 'нет данных'"""
    # Многие ковры имеют разный набор характеристик. По этому алгоритму определяется наличие текущей характеристики у
    # ковра, затем помещается в нужное места словаря, чтобы потом можно было вносить значения в базу данных
    CarpetAvalon.country = "Нет данных"
    CarpetAvalon.composition = "Нет данных"
    CarpetAvalon.density = 0000
    CarpetAvalon.height_pile = 000.0
    for feature in features_list:
        if feature.find('Странапроизводитель') != -1:
            CarpetAvalon.country = feature.removeprefix('Странапроизводитель')
            break
    for feature in features_list:
        if feature.find('Материал') != -1:
            CarpetAvalon.composition = feature.removeprefix('Материал')
            break
    for feature in features_list:
        if feature.find('Плотностьворса') != -1:
            CarpetAvalon.density = int((feature.removeprefix('Плотностьворса')).removesuffix('точек/м2'))
            break
    for feature in features_list:
        if feature.find('Высотаворса') != -1:
            CarpetAvalon.height_pile = float((feature.removeprefix('Высотаворса')).removesuffix('см')) * 10
            break
    CarpetAvalon.provider = 'Avalon'
    # Создаем сущность 'carpet', которая представляет собой набор подготовленных для внесения свойств ковра
    carpet = (CarpetAvalon.name, CarpetAvalon.price, CarpetAvalon.country, CarpetAvalon.composition,
              CarpetAvalon.density, CarpetAvalon.height_pile, CarpetAvalon.provider)

    """Подключаемся к заранее созданной базе данных"""
    con = sqlite3.connect('venera_carpets_v_2.0.db')
    cur = con.cursor()

    cur.execute(f"INSERT INTO carpets (name, price, country, composition, density, height_pile, provider) "
                f"VALUES (?, ?, ?, ?, ?, ?, ?);", carpet)
    con.commit()
    # Запись успешно внесена

"""Когда все записи успешно внесены, закрываем браузер"""
driver.close()
print("Ковры поставщика Avalon внесены")
# Запускаем файл authorized_parsing.py для начала парсинга ковров под авторизацией
exec(open('authorized_parsing.py', encoding='utf8').read())
