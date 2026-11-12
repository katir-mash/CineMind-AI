import sqlite3
from pathlib import Path

DB = Path(__file__).with_name('cinemind.db')
SEED = [
 ('Интерстеллар',2014,'Фантастика',8.7,169,'Космос путешествие семья любовь наука исследование'),
 ('Начало',2010,'Фантастика',8.8,148,'Сны сознание приключения тайна научная фантастика'),
 ('Матрица',1999,'Фантастика',8.7,136,'Виртуальная реальность технологии искусственный интеллект экшен'),
 ('Дюна',2021,'Фантастика',8.0,155,'Пустыня планета политика космос приключения'),
 ('Оппенгеймер',2023,'Драма',8.6,180,'Учёный физика история атомная бомба мораль'),
 ('Форрест Гамп',1994,'Драма',8.8,142,'Жизнь дружба любовь семья история'),
 ('Побег из Шоушенка',1994,'Драма',9.3,142,'Тюрьма надежда дружба свобода'),
 ('Зелёная миля',1999,'Драма',8.6,189,'Тюрьма чудо доброта справедливость'),
 ('Тёмный рыцарь',2008,'Боевик',9.0,152,'Герой преступность выбор мораль город'),
 ('Гладиатор',2000,'Боевик',8.5,155,'Древний Рим битва честь семья'),
 ('Головоломка',2015,'Мультфильм',8.1,95,'Эмоции ребёнок семья дружба'),
 ('Тайна Коко',2017,'Мультфильм',8.4,105,'Музыка семья память традиции'),
 ('1+1',2011,'Комедия',8.5,112,'Дружба поддержка юмор жизнь'),
 ('Отель Гранд Будапешт',2014,'Комедия',8.1,99,'Отель приключения юмор дружба'),
 ('Паразиты',2019,'Триллер',8.5,132,'Семья общество тайны неравенство'),
 ('Остров проклятых',2010,'Триллер',8.2,138,'Детектив расследование психология тайна'),
 ('Ла-Ла Ленд',2016,'Мелодрама',8.0,128,'Музыка любовь мечта искусство'),
 ('Гордость и предубеждение',2005,'Мелодрама',7.8,129,'Любовь общество семья история'),
]

def connect():
    c=sqlite3.connect(DB, timeout=10)
    c.row_factory=sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    return c

def setup():
    with connect() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, pw_hash TEXT NOT NULL, salt TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS movies (id INTEGER PRIMARY KEY, title TEXT NOT NULL, year INTEGER NOT NULL, genre TEXT NOT NULL, rating REAL NOT NULL, duration INTEGER NOT NULL, description TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS favorites (user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, movie_id INTEGER NOT NULL REFERENCES movies(id) ON DELETE CASCADE, PRIMARY KEY(user_id,movie_id));
        CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, action TEXT NOT NULL, detail TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS reset_codes (user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE, token_hash TEXT NOT NULL, expires_at REAL NOT NULL);
        ''')
        if c.execute('SELECT COUNT(*) FROM movies').fetchone()[0] == 0:
            c.executemany('INSERT INTO movies(title,year,genre,rating,duration,description) VALUES(?,?,?,?,?,?)',SEED)

def log(uid,action,detail=''):
    if uid is None: return
    with connect() as c: c.execute('INSERT INTO history(user_id,action,detail) VALUES(?,?,?)',(uid,action,str(detail)[:500]))

def movies(search='',genre='Все',sort='Рейтинг ↓'):
    wh=['(title LIKE ? OR description LIKE ?)']; params=[f'%{search}%',f'%{search}%']
    if genre!='Все':wh.append('genre=?');params.append(genre)
    order={'Рейтинг ↓':'rating DESC','Рейтинг ↑':'rating ASC','Год ↓':'year DESC','Год ↑':'year ASC','Название':'title COLLATE NOCASE ASC'}.get(sort,'rating DESC')
    with connect() as c:return c.execute('SELECT * FROM movies WHERE '+' AND '.join(wh)+' ORDER BY '+order,params).fetchall()
