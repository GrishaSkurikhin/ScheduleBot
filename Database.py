import sqlite3 as sq

'''
База данных хранит в себе 3 таблицы:
1) Пользователи (id, номер группы)
2) Расписание занятий(номер группы, неделя, дата, день недели, время, 
              тип занятия, предмет, преподаватель, аудитория)
3) Расписание сессии(номер группы, дата, время, предмет, преподаватель, аудитория)
'''

# Декоратор для подключения к базе данных при запросах
def db_connect(func):
    def wrapped(self, *args, **kwargs):
        with sq.connect(self.db_name) as con:
            cur = con.cursor()
            result = func(self, *args, **kwargs, cur=cur)
            con.commit()
            return result

    return wrapped

class Database:
    def __init__(self, db_name):
        self.db_name = db_name
        self.tables = self.get_tables()
        # Если таблицы отсутствуют в базе данных, то они создаются
        if len(self.tables) <= 3:
            self.create_users_table()
            self.create_schedule_table()
            self.create_session_table()

    # Возвращает данные из таблиц
    @db_connect
    def get_tables(self, cur):
        cur.execute("SELECT name FROM sqlite_master " +
                    "WHERE type = 'table';")
        result = cur.fetchall()
        return result

    '''
    Методы для работы с таблицей пользователей
    '''

    # Создание таблицы пользователей
    @db_connect
    def create_users_table(self, cur) -> None:
        cur.execute("""CREATE TABLE IF NOT EXISTS Users(
                     id INTEGER PRIMARY KEY, 
                     group_name CHAR(20)
                     )""")

    # Создает нового пользователя
    @db_connect
    def insert_user(self, user_id: int, group_name: str, cur) -> None:
        cur.execute("""INSERT INTO Users (id, group_name)
                    VALUES (?, ?)""",
                    (user_id, group_name))

    # Проверка наличия пользователя в таблице по его id
    @db_connect
    def check_id(self, user_id: int, cur) -> bool:
        cur.execute("SELECT * FROM Users WHERE id=?", (user_id,))
        result = cur.fetchone()
        return True if (result != None) else False

    # Возвращает группу пользователя
    @db_connect
    def get_user_group(self, user_id: int, cur) -> str:
        cur.execute("SELECT group_name FROM Users WHERE id=?", (user_id,))
        group = cur.fetchone()
        if group is not None:
            group = group[0]
        return group

    # Удаление пользователя из таблицы
    @db_connect
    def del_user(self, user_id: int, cur) -> None:
        cur.execute('DELETE FROM Users WHERE id=?', (user_id,))

    '''
    Методы для работы с таблицей расписания занятий
    '''

    # Создание таблицы расписания
    @db_connect
    def create_schedule_table(self, cur) -> None:
        cur.execute("""CREATE TABLE IF NOT EXISTS Schedule(
                    id INTEGER  NOT NULL PRIMARY KEY AUTOINCREMENT,
                    group_name CHAR(20),
                    week INTEGER,
                    date CHAR(10),
                    day CHAR(15),
                    time CHAR(15),
                    lesson_type CHAR(5),
                    subject CHAR(70),
                    teacher CHAR(70),
                    location CHAR(25))""")

    # Заполнение таблицы расписания
    @db_connect
    def insert_schedule_table(self, schedule: list, cur) -> None:
        for subject in schedule:
            if subject[5] != "Экзамен ":
                cur.execute("""INSERT INTO Schedule 
                            (group_name, week, date, 
                            day, time, lesson_type, 
                            subject, teacher, location) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            subject)

    # Проверка наличия расписания группы в таблице
    @db_connect
    def check_schedule(self, group_name: str, cur) -> bool:
        cur.execute("SELECT * FROM Schedule WHERE group_name=?", (group_name,))
        result = cur.fetchone()
        return True if (result != None) else False

    # Возвращает расписание на указанную дату
    @db_connect
    def get_date_schedule(self, group_name: str, date: str, cur) -> list:
        result = []
        for subject in cur.execute("""SELECT date, day, time, lesson_type, subject,
                               teacher, location FROM Schedule WHERE
                               group_name=? AND date=?""",
                               (group_name, date)):
            result.append(list(subject))
        return result

    # Возвращает расписание на указанную неделю
    @db_connect
    def get_week_schedule(self, group_name: str, week: int, cur) -> list:
        result = []
        dates = []
        temp = []
        for subject in cur.execute("""SELECT date, day, time, lesson_type, subject,
                                teacher, location FROM Schedule WHERE
                                group_name=? AND week=?""",
                                (group_name, week)):
            subject = list(subject)
            if subject[0] not in dates:
                dates.append(subject[0])
            temp.append(subject)
        for date in dates:
            result.append([subject for subject in temp if subject[0] == date])

        return result

    # Удаление расписания группы из таблицы
    @db_connect
    def delete_group_schedule(self, group_name: str, cur) -> None:
        cur.execute('DELETE FROM Schedule WHERE group_name=?', (group_name,))

    '''
    Методы для работы с таблицей расписания сессии
    '''

    # Создание таблицы сессии
    @db_connect
    def create_session_table(self, cur) -> None:
        cur.execute("""CREATE TABLE IF NOT EXISTS Session(
                        id INTEGER  NOT NULL PRIMARY KEY AUTOINCREMENT,
                        group_name CHAR(20),
                        date CHAR(10),
                        time CHAR(15),
                        subject CHAR(70),
                        teacher CHAR(70),
                        location CHAR(25))""")

    # Заполнение таблицы расписания сессии
    @db_connect
    def insert_session_table(self, session: list, cur) -> None:
        for subject in session:
            cur.execute("""INSERT INTO Session
                        (group_name, date,
                        time, subject, teacher, location)
                        VALUES (?, ?, ?, ?, ?, ?)""",
                        subject)

    # Проверка наличия расписания сессии группы в таблице
    @db_connect
    def check_session(self, group_name: str, cur) -> bool:
        cur.execute("SELECT * FROM Session WHERE group_name=?", (group_name,))
        result = cur.fetchone()
        return True if (result != None) else False

    # Возвращает расписание на указанную дату
    @db_connect
    def get_session(self, group_name: str, cur) -> list:
        result = []
        dates = []
        temp = []
        for subject in cur.execute("""SELECT date, time, subject,
                                teacher, location FROM Session WHERE
                                group_name=?""", (group_name,)):
            subject = list(subject)
            if subject[0] not in dates:
                dates.append(subject[0])
            temp.append(subject)
        for date in dates:
            result.append([subject for subject in temp if subject[0] == date])
        return result

    # Удаление расписания сессии заданной группы из таблицы
    @db_connect
    def delete_group_session(self, group_name: str, cur) -> None:
        cur.execute('DELETE FROM Session WHERE group_name=?', (group_name,))