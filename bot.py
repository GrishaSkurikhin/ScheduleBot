from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
import telebot
import datetime

import Parser, Database, config


bot = telebot.TeleBot(config.bot_token)

'''
Цепочка функций для регистрации
'''

@bot.message_handler(commands=['start'])
def start_command(message):
    id = message.chat.id
    if db.check_id(id):
        bot.send_message(message.chat.id, config.start_message1, reply_markup=telebot.types.ReplyKeyboardRemove())
        Menu(message)
    else:
        bot.send_message(message.chat.id, config.start_message2, reply_markup=telebot.types.ReplyKeyboardRemove())
        choose_course(message, False)

def choose_course(message, isReg):
    reply_markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for course in range(1, 6):
        reply_markup.add(telebot.types.KeyboardButton("Курс №" + str(course)))
    msg = bot.send_message(message.chat.id, "Выберите курс", reply_markup=reply_markup)
    bot.register_next_step_handler(msg, choose_institute, isReg=isReg)


def choose_institute(message, isReg):
    reply_markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for institute in range(1, 13):
        reply_markup.add(telebot.types.KeyboardButton("Институт №" + str(institute)))

    msg = bot.send_message(message.chat.id, "Выберите институт", reply_markup=reply_markup)
    bot.register_next_step_handler(msg, choose_group, course=message, isReg=isReg)

def choose_group(message, course, isReg):
    groups = Parser.ParseGroups(course.text[-1], message.text[-1])

    reply_markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for group in groups:
        reply_markup.add(telebot.types.KeyboardButton(group))

    msg = bot.send_message(message.chat.id, "Выберите группу", reply_markup=reply_markup)
    bot.register_next_step_handler(msg, end_registration, isReg=isReg)

def end_registration(message, isReg):
    if isReg:
        db.del_user(message.chat.id)
        db.insert_user(message.chat.id, message.text)
        bot.send_message(message.chat.id, "Перерегистрация прошла успешно")
        Menu(message)
    else:
        db.insert_user(message.chat.id, message.text)
        bot.send_message(message.chat.id, "Регистрация прошла успешно")
        Menu(message)

@bot.message_handler(commands=['ReReg'])
def ReRegistration(message):
    id = message.chat.id
    if db.check_id(id):
        bot.send_message(message.chat.id, "Перерегистрация:", reply_markup=telebot.types.ReplyKeyboardRemove())
        choose_course(message, True)
    else:
        bot.send_message(message.chat.id, config.no_reg_message)

'''
Функции, срабатывающие при нажатии кнопок меню
'''

@bot.message_handler(commands=['today'])
def Today(message):
    group = Group(message)
    if group == None: return

    if db.check_schedule(group):
        date = DateToDBdate(datetime.date.today())
        schedule = db.get_date_schedule(group, date)
        PrintSchedule(message, schedule, date)
    else:
        bot.send_message(message.chat.id, config.no_reg_message)

@bot.message_handler(commands=['tomorrow'])
def Tomorrow(message):
    group = Group(message)
    if group == None: return

    if db.check_schedule(group):
        date = DateToDBdate(datetime.date.today() + datetime.timedelta(days=1))
        schedule = db.get_date_schedule(group, date)
        PrintSchedule(message, schedule, date)
    else:
        bot.send_message(message.chat.id, config.no_reg_message)

@bot.message_handler(commands=['weekday'])
def WeekDay(message):
    group = Group(message)
    if group == None: return

    days = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб")
    keyboard = telebot.types.InlineKeyboardMarkup()
    Buttons = []
    for day in days:
        Buttons.append(telebot.types.InlineKeyboardButton(text=day, callback_data=day))
    keyboard.row(*Buttons)
    bot.send_message(message.chat.id, 'Выберите день недели', reply_markup=keyboard)

    @bot.callback_query_handler(lambda call: call.data in days)
    def callback_inline(call):
        if db.check_schedule(group):
            date = WeekDayToDate(call.data)
            schedule = db.get_date_schedule(group, date)
            PrintSchedule(message, schedule, date)
        else:
            bot.send_message(message.chat.id, config.no_reg_message)

@bot.message_handler(commands=['date'])
def Date(message):
    group = Group(message)
    if group == None: return

    if not db.check_schedule(group):
        bot.send_message(message.chat.id, config.no_reg_message)
        return

    calendar, step = DetailedTelegramCalendar().build()
    bot.send_message(message.chat.id,
                     f"Select {LSTEP[step]}",
                     reply_markup=calendar)

    @bot.callback_query_handler(func=DetailedTelegramCalendar.func())
    def call(c):
        result, key, step = DetailedTelegramCalendar().process(c.data)
        if not result and key:
            bot.edit_message_text(f"Select {LSTEP[step]}",
                                  c.message.chat.id,
                                  c.message.message_id,
                                  reply_markup=key)
        elif result:
            date = DateToDBdate(result)
            schedule = db.get_date_schedule(group, date)
            PrintSchedule(message, schedule, date)

@bot.message_handler(commands=['thisweek'])
def ThisWeek(message):
    group = Group(message)
    if group == None: return

    if not db.check_schedule(group):
        bot.send_message(message.chat.id, config.no_reg_message)
        return

    date = datetime.datetime.today() # текущая дата
    today = date.weekday() # текущий день недели (цифра от 0 до 6)
    week_start = date - datetime.timedelta(days=today) # дата начала недели
    for i in range(6):
        date = DateToDBdate(week_start)
        schedule = db.get_date_schedule(group, date)
        PrintSchedule(message, schedule, date)
        week_start += datetime.timedelta(days=1)

@bot.message_handler(commands=['session'])
def Session(message):
    group = Group(message)
    if group == None: return

    schedule = db.get_session(group)
    text = ""
    if len(schedule) == 0:
        text += "Нет расписания сессии"
    else:
        for day in schedule:
            text += "====== " + day[0][0] + " ======""\n"
            for subject in day:
                text += "⌚ " + subject[1] + "\n"
                text += "📝 " + subject[2] + "\n"
                text += "👤 " + subject[3] + "\n"
                text += "📍 " + subject[4] + "\n\n"

    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['update'])
def UpdateSchedule(message):
    group = Group(message)
    if group == None:
        return

    bot.send_message(message.chat.id, "Начало загрузки")
    if db.check_schedule(group):
        db.delete_group_schedule(group)

    for week_num in range(1, 20):
        week_schedule = Parser.ParseScheduleWeek(group, week_num)
        db.insert_schedule_table(week_schedule)

    if db.check_session(group):
        db.delete_group_session(group)

    session_schedule = Parser.ParseSession(group)
    db.insert_session_table(session_schedule)

    bot.send_message(message.chat.id, "Загрузка прошла успешно")

@bot.message_handler(commands=['help',])
def Help(message):
    text =\
    """
    Регистрация - /start
    Перерегистрация - /ReReg
    Открыть меню - /Menu
    Расписание на сегодня - /today
    Расписание на завтра - /tomorrow
    Расписание по дню недели - /weekday
    Расписание по дате - /date
    Расписание на текущюю неделю - /thisweek
    Расписание на конкретную неделю - /week
    Расписание сессии - /session
    Загрузка/обновление расписания - /update
    """

    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['Menu'])
def Menu(message):
    markup = telebot.types.ReplyKeyboardMarkup()
    button1 = telebot.types.KeyboardButton("Сегодня")
    button2 = telebot.types.KeyboardButton("Завтра")
    button3 = telebot.types.KeyboardButton("По дню недели")
    button4 = telebot.types.KeyboardButton("По дате")
    button5 = telebot.types.KeyboardButton("На текущую неделю")
    button6 = telebot.types.KeyboardButton("Расписание сессии")
    button7 = telebot.types.KeyboardButton("Загрузить/обновить расписание")
    button8 = telebot.types.KeyboardButton("Помощь")
    markup.row(button1, button2, button3, button4)
    markup.row(button5, button6)
    markup.row(button7, button8)
    bot.send_message(message.chat.id, "Выберите действие", reply_markup=markup)

# Функция, отвечающая за контроль входящих сообщений из меню
@bot.message_handler(content_types=['text'])
def MenuController(message):
    choices_dict = {'Сегодня': Today, \
                    'Завтра': Tomorrow, \
                    'По дню недели': WeekDay,\
                    'По дате': Date,\
                    'На текущую неделю': ThisWeek,\
                    'Расписание сессии': Session,\
                    'Загрузить/обновить расписание': UpdateSchedule,\
                    'Помощь': Help}

    func = choices_dict.get(message.text, None)
    if func != None:
        func(message)

'''
Вспомогательные функции
'''

# Функция, проверяющая зарегестрирован ли пользователь и возвращающая его группу, если это так
def Group(message):
    id = message.chat.id
    if not db.check_id(id):
        bot.send_message(message.chat.id, config.no_reg_message)
        return None
    else:
        group = db.get_user_group(id)
        return group

# Преобразует дату из datetime в строку для базы данных
def DateToDBdate(date):
    day = str(date.day)
    month = str(date.month)
    if len(day) == 1:
        day = "0" + day
    if len(month) == 1:
        month = "0" + month
    return day + "." + month

def WeekDayToDate(day):
    d = {"Пн": 0, "Вт": 1, "Ср": 2, "Чт": 3, "Пт": 4, "Сб": 5}
    RequiredDay = d[day]
    today = datetime.datetime.today().weekday()
    if RequiredDay == today:
        return DateToDBdate(datetime.datetime.today())
    elif RequiredDay > today:
        return DateToDBdate(datetime.datetime.today() +\
                            datetime.timedelta(days=(RequiredDay-today)))
    else:
        return DateToDBdate(datetime.datetime.today() +\
                            datetime.timedelta(days=((6-today)+RequiredDay)))

def PrintSchedule(message, schedule, date):
    text = ""
    if len(schedule) == 0:
        text += "Расписание на " + date + "\n" + "=============" + "\n"
        text += "Занятий нет"
    else:
        text += "Расписание на " + schedule[0][0] + " (" + schedule[0][1] + ")" + "\n" + "=============" + "\n\n"
        for subject in schedule:
            text += "⌚ " + subject[2] + "\n"
            text += "📝 " + subject[4] + ", " + subject[3] + "\n"
            text += "👤 " + subject[5] + "\n"
            text += "📍 " + subject[6] + "\n\n"

    bot.send_message(message.chat.id, text)

if __name__ == "__main__":
    db = Database.Database(config.database_name)
    bot.polling(none_stop=True)