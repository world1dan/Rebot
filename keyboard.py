from telebot import types
from config import wb_urls, settings


def create_allow_dinamic_key(id):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    btn = types.InlineKeyboardButton(text='Разрешить доступ', callback_data=f'allow{id}')
    keyboard.add(btn)
    return keyboard


def pract_inline_b_maker(dict):
    keyboard = types.InlineKeyboardMarkup()
    for key in dict:
        btn = types.InlineKeyboardButton(text=f'Номер {key}', url=dict[key])
        keyboard.row(btn)
    return keyboard


main_key = types.ReplyKeyboardMarkup(True, True)
main_key.row('Тетради')
main_key.row('Оценки', 'Добавить оценку')

wb_menu = types.InlineKeyboardMarkup(row_width=1)
pr_phisBtn = types.InlineKeyboardButton(text='Физика', callback_data='pr_phis')
wb_englBtn = types.InlineKeyboardButton(text='Английский', url=wb_urls['engl'])
wb_menu.row(pr_phisBtn, wb_englBtn)

send_allow_key = types.InlineKeyboardMarkup(row_width=1)
send_allow_Btn = types.InlineKeyboardButton(text='Отправить заявку на доступ', callback_data='send_allow')
send_allow_key.add(send_allow_Btn)

marks_key = types.InlineKeyboardMarkup(row_width=2)
add_mark_Btn = types.InlineKeyboardButton(text='Добавить оценку', callback_data='add_mark')
marks_key.row(add_mark_Btn)


git_key = types.InlineKeyboardMarkup(row_width=2)
git_Btn = types.InlineKeyboardButton(text='Github', url=settings['git'])
git_key.row(git_Btn)


admin_key = types.InlineKeyboardMarkup(row_width=2)
users_Btn = types.InlineKeyboardButton(text='Users', callback_data='adm_users')
protocol_Btn = types.InlineKeyboardButton(text='PROTOTCOL', callback_data='adm_protocol')
checking_Btn = types.InlineKeyboardButton(text='Тесты', callback_data='adm_checking')
admin_key.row(checking_Btn)
admin_key.row(protocol_Btn, checking_Btn)
