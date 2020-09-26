import datetime
import sqlite3
from config import settings, band_crib, file_urls
from threading import Thread
import time
import telebot
import keyboard


class Logger:
    def __init__(self):
        self.log_file = 'log.txt'
        self.info_file = 'info.txt'

    def add_bot(self, bot):
        self.bot = bot

    def info(self, text, user):
        try:
            now = datetime.datetime.now()
            date = now.strftime("%d.%m %H:%M")
            with open(self.info_file, "a", encoding='utf-8') as file:
                if user is not False:
                    file.write(f"{date} {user.first_name} {user.id} {text}\n")
                else:
                    file.write(f"{date} {text}\n")
        except Exception as ex:
            self.error('add_info(): ' + str(ex), user)

    def error(self, error, user):
        try:
            now = datetime.datetime.now()
            date = now.strftime("%d.%m %H:%M")
            if user is False:
                with open(self.log_file, "a", encoding='utf-8') as file:
                    file.write(f"{date} {error}\n")
            else:
                with open(self.log_file, "a", encoding='utf-8') as file:
                    file.write(f"{date} {user.first_name} {user.id} {error}\n")
        except Exception as ex:
            print(user)
            self.bot.send_message(settings["service_chat"], '🆘 Critical Error: Не удалось добавить запись в лог\n' + str(ex))


log = Logger()


class Band_crib:
    def __init__(self, id):
        self.life = True
        self.id = id
        self.bot = telebot.TeleBot(settings['TOKEN'])

    def run_crib(self, message):
        self.crib = message.text
        log.info('Запустил Crib' + self.crib, message.from_user)
        self.crib_th = Thread(target=self.crib_func)
        self.crib_th.start()

    def crib_func(self):
        self.bot.send_message(self.id, 'Band_crib будет запущен через 20 секунд')
        i = 0
        time.sleep(band_crib['run_time_out'])
        while i < band_crib['num_of_cribs'] and self.life is True:
            if i > 0:
                self.bot.delete_message(self.id, self.last_msg.message_id)
            self.last_msg = self.bot.send_message(self.id, self.crib)
            i = i + 1
            time.sleep(band_crib['interval'])
        self.bot.send_message(self.id, 'Band_crib Остановлен', reply_markup=keyboard.main_key)


class DB:
    def __init__(self):
        self.conn = sqlite3.connect(file_urls['database'], check_same_thread=False)
        self.base = self.conn.cursor()

    def add_bot(self, bot):
        self.bot = bot

    def add_marks_user(self, id):
        sql = "SELECT * FROM mark where id=?"
        self.base.execute(sql, [(id)])
        if self.base.fetchone() is None:
            try:
                sql = "INSERT INTO mark (id) VALUES (?)"
                self.base.execute(sql, [(id)])
                self.conn.commit()
            except Exception:
                log.error(f'Cant add {id} in marks, maybe user has already been added', False)

    def change_auth(self, id, state):
        try:
            sql = f"UPDATE auth SET auth={state} WHERE id={id}"
            self.base.execute(sql)
            self.conn.commit()
        except Exception:
            log.error(f'Cant change user {id} state ', False)

    def check_auth(self, id):
        try:
            id = int(id)
            sql = "SELECT * FROM auth WHERE id=?"
            self.base.execute(sql, [(id)])
            state = self.base.fetchone()[1]
            if state == 1:
                return True
            else:
                return False
        except Exception:
            return False

    def add_user(self, id):
        try:
            sql = "SELECT * FROM auth WERE id=?"
            self.base.execute(sql, [(id)])
        except Exception:
            try:
                sql = "INSERT INTO auth VALUES (?, 1)"
                self.base.execute(sql, [(id)])
                self.conn.commit()
            except Exception:
                log.error(f'Cant add {id} in auth, maybe user has already been added', False)

    def get_marks(self, id):
        try:
            sql = f'SELECT * FROM mark WHERE id={id}'
            self.base.execute(sql)
            raw_marks = self.base.fetchone()
            marks = {
                'Русский язык': raw_marks[1],
                'Русская литература': raw_marks[2],
                'Беллоруский язык': raw_marks[3],
                'Белорусская литература': raw_marks[4],
                'Химия': raw_marks[5],
                'Математика': raw_marks[6],
                'Информатика': raw_marks[7],
                'География': raw_marks[8],
                'Биология': raw_marks[9],
                'Английский язык': raw_marks[10],
                'Труд': raw_marks[11],
                'Физика': raw_marks[12]
            }
        except Exception as ex:
            log.error(f'Cant get {id} marks: {ex} {sql}', False)
        return marks

    def add_mark(self, id, field, mark):
        try:
            mark = str(mark)
            sql = f"SELECT {field} FROM mark WHERE id={id}"
            self.base.execute(sql)
            old_str = self.base.fetchone()
            if str(old_str[0]).find('Нет') == 0:
                new_str = mark
            else:
                new_str = f"{old_str[0]}, {mark}"
            sql = f"UPDATE mark SET {field}='{new_str}' WHERE id={id}"
            self.base.execute(sql)
            self.conn.commit()
        except Exception as ex:
            log.error(f'Cant add {id} marks: {ex}', False)


database = DB()
