import telebot
import keyboard
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import config
from classes import database, log, Band_crib
import time
from flask import Flask, request, abort


app = Flask(__name__)


bot = telebot.TeleBot(config.settings['TOKEN'], threaded=False)
database.add_bot(bot)
band_cribs = {}
log.add_bot(bot)

if config.PC is False:
    bot.remove_webhook()
    time.sleep(2)
    bot.set_webhook(url="https://wordl1dan.pythonanywhere.com/{}".format(config.settings['SECRET']))
    print("https://wordl1dan.pythonanywhere.com/{}".format(config.settings['SECRET']))
    print("Вебхук установлен")

    app = Flask(__name__)

    @app.route('/{}'.format(config.settings['SECRET']), methods=["POST"])
    def telegram_webhook():
        if request.headers.get('content-type') == 'application/json':
            json_string = request.stream.read().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return 'ok', 200
        else:
            print('dddd')
            abort(403)
else:
    bot.remove_webhook()


# Decorators
def private(func):
    def check(message):
        if database.check_auth(message.from_user.id) is True:
            func(message)
        else:
            bot.send_message(message.from_user.id, 'Доступ к боту запрещен', reply_markup=keyboard.send_allow_key)
            bot.send_sticker(message.from_user.id, config.stickers['blocked'])
    return check


# Helper func
def send_answer(subject, num, bot, message):
    try:
        for keyword in config.subject_urls:
            if subject.find(keyword) == 0:
                if keyword == 'ф' or keyword == 'х':
                    i = 1
                    num = int(num) - 1
                    while i <= 20:
                        url = config.subject_urls[keyword].format(num, i)
                        i = i + 1
                        try:
                            bot.send_document(message.chat.id, url, disable_notification=True, reply_markup=keyboard.main_key)
                        except Exception:
                            if i == 2:
                                bot.send_message(message.chat.id, 'Номер не найден на сервере', reply_markup=keyboard.main_key)
                            return
                else:
                    try:
                        url = config.subject_urls[keyword].format(num)
                        bot.send_document(message.chat.id, url, disable_notification=True, reply_markup=keyboard.main_key)
                    except Exception:
                        bot.send_message(message.chat.id, 'Номер не найден на сервере', reply_markup=keyboard.main_key)
    except Exception as ex:
        log.error('send_answer(): ' + str(ex), message.from_user)


def add_mark_helper(message):
    text = message.text.lower()
    try:
        for word in config.keywords:
            split = text.split(' ')
            if text.find(word) == 0:
                try:
                    num = split[2]
                except Exception:
                    num = split[1]
                database.add_mark(message.from_user.id, config.keywords[word], num)
                bot.send_message(message.chat.id, 'Оценка добавлена', reply_markup=keyboard.main_key)
                return
        bot.send_message(message.chat.id, 'Не удалось найти ключевое слово, попробуйте еще раз', reply_markup=keyboard.main_key)
    except Exception as ex:
        log.error(f"Не удалось добавить оценку: '{text}' {str(ex)}", message.from_user)


# Commands handlers
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}!\nДля доступа к боту нужно разрешение', reply_markup=keyboard.send_allow_key)
    bot.send_sticker(message.chat.id, config.stickers['hi'])
    bot.send_message(config.settings['service_chat'],
                     f"{message.from_user.id}\n{message.from_user.first_name} {message.from_user.last_name}\nНажал кнопку /start")


@bot.message_handler(commands=['reload'])
@private
def reload_key(message):
    bot.send_message(message.chat.id, 'Клавиатура обновлена', reply_markup=keyboard.main_key)
    log.info("Обновил клавиатуру", message.from_user)


@bot.message_handler(commands=['crib'])
@private
def create_crib(message):
    bot.send_message(message.chat.id, 'Crib', reply_markup=keyboard.main_key)
    band_cribs[message.chat.id] = Band_crib(message.chat.id)
    msg = bot.send_message(message.chat.id, 'Размер текста: 12x10\nТекст:', reply_markup=keyboard.main_key)
    bot.register_next_step_handler(msg, band_cribs[message.chat.id].run_crib)


@bot.message_handler(commands=['stop'])
@private
def stop_crib(message):
    try:
        band_cribs[message.chat.id].life = False
    except Exception:
        bot.send_message(message.chat.id, 'В этом чате не запущен Band crib', reply_markup=keyboard.main_key)


@bot.message_handler(commands=['id'])
@private
def send_id(message):
    bot.send_message(message.chat.id, f'Telegram id: {message.from_user.id}\nChat id: {message.chat.id}', reply_markup=keyboard.main_key)


@bot.message_handler(commands=['log'])
@private
def send_log(message):
    try:
        if message.from_user.id == config.settings['admin_id'] or message.chat.id == config.settings['service_chat']:
            with open('info.txt', "r") as file:
                bot.send_document(message.chat.id, file)
            with open('log.txt', "r") as file:
                bot.send_document(message.chat.id, file)
        else:
            bot.send_sticker(message.chat.id, config.stickers['blocked'])
    except Exception:
        pass


@bot.message_handler(commands=['code'])
@private
def send_code(message):
    bot.send_message(message.chat.id, 'Код:', reply_markup=keyboard.git_key)


# Callback handlers
@bot.callback_query_handler(func=lambda c: c.data == 'send_allow')
def send_allow(c):
    bot.answer_callback_query(callback_query_id=c.id, show_alert=False, text="Заявка отправлена!")
    bot.send_message(config.settings['service_chat'],
                     f"Запрос на доступ с ID {c.from_user.id}\n{c.from_user.first_name} {c.from_user.last_name}",
                     reply_markup=keyboard.create_allow_dinamic_key(c.from_user.id))
    bot.send_message(c.from_user.id, 'Заявка на доступ отправлена')
    try:
        bot.delete_message(c.chat.id, c.message.message_id)
    except Exception:
        pass
    bot.send_sticker(c.from_user.id, config.stickers['wait-1'])


@bot.callback_query_handler(func=lambda c: c.data.find('allow') == 0)
def allow(c):
    try:
        id = int(c.data.replace('allow', ''))
        database.add_user(id)
        database.add_marks_user(id)
        bot.answer_callback_query(callback_query_id=c.id, show_alert=True, text=f"{id} Получил доступ к боту")
        bot.send_sticker(c.from_user.id, config.stickers['wait-2'])
        bot.send_message(id, 'Заявка принята, доступ к боту разрешен!\nhttps://telegra.ph/Rebot-Guide-09-17', reply_markup=keyboard.main_key)
    except Exception as ex:
        bot.send_message(config.settings['service_chat'], 'Не удалось добавить пользователя' + str(ex))


@bot.callback_query_handler(func=lambda c: c.data.find('pr') == 0)
def send_pract_links(c):
    try:
        if c.data.find('phis') == 3:
            bot.send_message(c.from_user.id, 'Практические работы по физике:', reply_markup=keyboard.pract_inline_b_maker(config.pract_phisick_url))
        bot.answer_callback_query(callback_query_id=c.id, show_alert=False, text="Ссылки отправлены!")
    except Exception as ex:
        print(str(ex))


# Text handlers
@bot.message_handler(regexp='ре')
@private
def send_resheba(message):
    try:
        low = message.text.lower().replace('реш', '').replace('ре', '')
        log.info(message.text, message.from_user)
        if '-' in low:
            splited = low.split()
            subject = splited[0]
            num = splited[1].split('-')
            i = int(num[0])
            counter = 0
            while i in range(int(num[0]), int(num[1]) + 1):
                send_answer(subject, i, bot, message)
                i = i + 1
                counter = counter + 1
                if counter >= 15:
                    bot.send_message(message.chat.id, 'Превышен лимит запросов к серверу (15)')
                    break
        else:
            split = low.split()
            subject = split[0]
            num = split[1]
            send_answer(subject, num, bot, message)
    except Exception:
        bot.send_message(message.chat.id, 'Команда написана неверно или сервер недоступен', reply_markup=keyboard.main_key)


@bot.message_handler(regexp='Тетради')
@private
def send_pract_menu(message):
    bot.send_sticker(message.chat.id, config.stickers['like-tv'], reply_markup=keyboard.main_key)
    bot.send_message(message.chat.id, 'Тетради', reply_markup=keyboard.wb_menu)


@bot.message_handler(regexp='Оценки')
@private
def show_marks(message):
    try:
        marks = database.get_marks(message.from_user.id)
        table = ''
        extd = False
        for key in marks:
            line = f'{key}: {marks[key]}\n\n'
            table = table + line
            if len(line) > 48:
                extd = True
        font = ImageFont.truetype(config.file_urls['font1'], 28)
        if extd is True:
            img = Image.open(config.file_urls['mark_backgr_ext'])
            idraw = ImageDraw.Draw(img)
            idraw.text((80, 75), table, fill='white', font=font)
        else:
            img = Image.open(config.file_urls['mark_backgr'])
            idraw = ImageDraw.Draw(img)
            idraw.text((80, 65), table, fill='white', font=font)
        with BytesIO() as output:
            img.save(output, format="PNG")
            img = output.getvalue()
        bot.send_photo(message.chat.id, img, reply_markup=keyboard.main_key)
    except Exception as ex:
        log.error(f'Cant show marks by user {message.from_user.id} {str(ex)}', False)
        bot.send_message(message.chat.id, 'Не удалось показать оценки' + str(ex), reply_markup=keyboard.main_key)


@bot.message_handler(regexp='Добавить оценку')
@private
def add_mark(message):
    msg = bot.send_message(message.from_user.id, "Форма добавления оценки: предмет + оценка\nНапример: 'рус лит 9'",)
    bot.register_next_step_handler(msg, add_mark_helper)


if config.PC is True:
    bot.infinity_polling(True)
