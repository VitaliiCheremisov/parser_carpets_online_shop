"""Парсинг ссылок ковров на сайте Venera с внесением этих ссылок в таблицу.
   После завершения запускает файл Parser.py"""
import sqlite3
from bs4 import BeautifulSoup
import requests as req

"""Получаем ссылку для входа на страничку каждого ковра"""
for i in range(1, 29):
    resp = req.get(f'https://venera-carpet.ru/category/index.html?page={i}&categoryId=0')
    soup = BeautifulSoup(resp.text, 'lxml')
    for a in soup.find_all('a', attrs={'class': "title"}, href=True):
        carpet_link = a['href']

        """Подключаемся к базе данных и вносим ссылку в таблицу"""
        con = sqlite3.connect('venera_carpets_v_2.0.db')
        cur = con.cursor()
        cur.execute("INSERT INTO venera_carpets_links (carpet_link) VALUES (?)", [carpet_link])
        con.commit()

"""Делаем запрос в базу данных, чтобы знать ожидаемое количество ковров"""
con = sqlite3.connect('venera_carpets_v_2.0.db')
cur = con.cursor()
cur.execute("SELECT COUNT(venera_carpet_links_id) FROM venera_carpets_links")
venera_carpets_number = cur.fetchone()[0]
print(f"Получено число ссылок ковров 'Venera': {venera_carpets_number}")
exec(open('Parser_v_2.0.py', encoding='utf8').read())
