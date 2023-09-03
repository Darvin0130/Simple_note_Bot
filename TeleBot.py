import telebot
from telebot import types
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

TOKEN = '6597731305:AAHHm32HczVqbFLK71TrJG-HDFVKwjuj8E8'
bot = telebot.TeleBot(TOKEN)


def load_data_from_json(file_name):
    try:
        with open(file_name, 'r') as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        return []


income_records = load_data_from_json('income.json')
expense_records = load_data_from_json('expense.json')
categories = ['щоденні', 'розваги', 'робота']


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton('Витрати')
    btn2 = types.KeyboardButton('Дохід')
    markup.row(btn1, btn2)
    bot.send_message(message.chat.id, f'Привіт, {message.from_user.first_name}', reply_markup=markup)

    global income_records
    global expense_records
    expense_records = load_data_from_json('expense.json')
    income_records = load_data_from_json('income.json')


@bot.message_handler(func=lambda message: message.text == 'Дохід')
def handle_income(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('Введіть дохід', callback_data='add_income_button')
    btn2 = types.InlineKeyboardButton('Інформація', callback_data='income')
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, 'Виберіть дію з доходами', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'add_income_button')
def handle_enter_income(call):
    msg = bot.send_message(call.message.chat.id, 'Введіть суму доходу та дату у форматі: сума дд.мм.рр')
    bot.register_next_step_handler(msg, lambda message: save_income(message, call.message.chat.id, income_records))


def save_income(message, chat_id, income_records):
    try:
        input_data = message.text.split()
        amount = float(input_data[0])
        date_text = input_data[1]
        date = datetime.strptime(date_text, '%d.%m.%y')
        income_records.append({'amount': amount, 'date': date.strftime('%d.%m.%y')})
        save_data_to_json('income.json', income_records)
        bot.send_message(chat_id, 'Дохід збережено!')
    except (ValueError, IndexError):
        bot.send_message(chat_id, 'Неправильний формат, спробуйте ще раз.')


@bot.callback_query_handler(func=lambda call: call.data == 'income')
def handle_income_info(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('Дохід за день', callback_data='Income за день')
    btn2 = types.InlineKeyboardButton('Дохід за тиждень', callback_data='Income за тиждень')
    btn3 = types.InlineKeyboardButton('Дохід за місяць', callback_data='Income за місяць')
    btn4 = types.InlineKeyboardButton('Дохід за весь період', callback_data='Income за весь період')
    markup.add(btn1, btn2, btn3, btn4)
    bot.send_message(call.message.chat.id, 'Виберіть дію з доходами', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'Income за день')
def handle_income_day(call):
    filtered_incomes = filter_income_by_date(income_records, 'day')
    total_income = sum(record['amount'] for record in filtered_incomes)
    response = f'Загальний дохід за день: {total_income}\n'
    bot.send_message(call.message.chat.id, response)


@bot.callback_query_handler(func=lambda call: call.data == 'Income за тиждень')
def handle_income_week(call):
    filtered_incomes = filter_income_by_date(income_records, 'week')
    total_income = sum(record['amount'] for record in filtered_incomes)
    response = f'Загальний дохід за тиждень: {total_income}\n'
    bot.send_message(call.message.chat.id, response)


@bot.callback_query_handler(func=lambda call: call.data == 'Income за місяць')
def handle_income_month(call):
    filtered_incomes = filter_income_by_date(income_records, 'month')
    total_income = sum(record['amount'] for record in filtered_incomes)
    response = f'Загальний дохід за місяць: {total_income}\n'
    bot.send_message(call.message.chat.id, response)


def filter_income_by_date(records, time_period):
    today = datetime.today().date()

    if time_period == 'day':
        return [record for record in records if datetime.strptime(record['date'], '%d.%m.%y').date() == today]
    elif time_period == 'week':
        week_start = today - timedelta(days=today.weekday())
        return [record for record in records if
                week_start <= datetime.strptime(record['date'], '%d.%m.%y').date() <= today]
    elif time_period == 'month':

        month_start = today.replace(day=1)
        month_end = today.replace(day=1, month=today.month + 1) - timedelta(days=1)
        return [record for record in records if
                month_start <= datetime.strptime(record['date'], '%d.%m.%y').date() <= month_end]
    else:
        return records


@bot.callback_query_handler(func=lambda call: call.data == 'total_income')
def handle_total_income(call):
    total_amount = sum(record['amount'] for record in income_records)
    bot.send_message(call.message.chat.id, f'Загальний дохід за весь період: {total_amount}')


@bot.callback_query_handler(func=lambda call: call.data.startswith('Income за '))
def handle_income_analysis(call):
    time_period = call.data.split('Income за ')[1].lower()
    filtered_incomes = filter_income_by_date(income_records, time_period)
    total_income = sum(record['amount'] for record in filtered_incomes)
    response = f'Загальний дохід за {time_period}: {total_income}\n'

    for i, record in enumerate(filtered_incomes):
        response += f'{i + 1}. {record["date"]} - {record["amount"]} грн '
        delete_button = types.InlineKeyboardButton('Видалити', callback_data=f'delete_income_{i}')
        response_markup = types.InlineKeyboardMarkup()
        response_markup.add(delete_button)
        bot.send_message(call.message.chat.id, response, reply_markup=response_markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_income_'))
def handle_delete_income(call):
    index = int(call.data.split('delete_income_')[1])
    delete_income_record(call.message.chat.id, index)


def delete_income_record(chat_id, index):
    try:
        deleted_record = income_records.pop(index)
        save_data_to_json('income.json', income_records)
        bot.send_message(chat_id, f'Запис про дохід {deleted_record["amount"]} видалено.')
    except IndexError:
        bot.send_message(chat_id, 'Неправильний індекс запису, спробуйте ще раз.')


@bot.message_handler(func=lambda message: message.text == 'Витрати')
def handle_expense(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('Введіть витрати', callback_data='add_expense')
    btn2 = types.InlineKeyboardButton('Інформація', callback_data='expense_info')
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, 'Виберіть дію з витратами', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'expense_info')
def handle_expense_info(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('Витрати за день', callback_data='expenses_day')
    btn2 = types.InlineKeyboardButton('Витрати за тиждень', callback_data='expenses_week')
    btn3 = types.InlineKeyboardButton('Витрати за місяць', callback_data='expenses_month')
    btn4 = types.InlineKeyboardButton('Витрати за весь період', callback_data='expenses_all')
    btn5 = types.InlineKeyboardButton('Видалити витрати', callback_data='delete_expenses')
    markup.add(btn1, btn2, btn3, btn4, btn5)
    bot.send_message(call.message.chat.id, 'Виберіть період для аналізу витрат', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('expenses_'))
def handle_expenses_analysis(call):
    time_period = call.data.split('expenses_')[1]
    filtered_expenses = filter_expenses_by_date(expense_records, time_period)
    total_amount = sum(int(record['amount']) for record in filtered_expenses)
    category_expenses = calculate_category_expenses(filtered_expenses)
    response = f'Загальні витрати за {time_period.capitalize()}:\n{total_amount}\n\n'
    response += 'Витрати за категоріями:\n'
    for category, amount in category_expenses.items():
        response += f'{category.capitalize()}: {amount}\n'
    bot.send_message(call.message.chat.id, response)


@bot.callback_query_handler(func=lambda call: call.data == 'add_expense')
def handle_enter_expense(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    category_buttons = [types.InlineKeyboardButton(category.capitalize(), callback_data=f'add_expense_{category}') for
                        category in categories]
    markup.add(*category_buttons)
    bot.send_message(call.message.chat.id, 'Виберіть категорію витрат:', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('add_expense_'))
def handle_enter_expense_category(call):
    selected_category = call.data.split('_')[2]
    msg = bot.send_message(call.message.chat.id, f'Введіть суму витрат у категорії "{selected_category}":')
    bot.register_next_step_handler(msg, lambda message: save_expense(message, selected_category))


@bot.callback_query_handler(func=lambda call: call.data == 'category')
def handle_enter_expense(call):
    msg = bot.send_message(call.message.chat.id, 'Виберіть категорію витрат:\n'
                                                 '1. Щоденні\n'
                                                 '2. Розваги\n'
                                                 '3. Робота')
    bot.register_next_step_handler(msg, handle_expense_category)


@bot.callback_query_handler(func=lambda call: call.data.startswith('total_expense_'))
def handle_total_expense_period(call):
    time_period = call.data.split('_')[2]
    filtered_expenses = filter_expenses_by_date(expense_records, time_period)
    total_amount = sum(int(record['amount']) for record in filtered_expenses)
    category_expenses = calculate_category_expenses(filtered_expenses)
    response = f'Загальні витрати за {time_period}:\n{total_amount}\n\n'
    response += 'Витрати за категоріями:\n'
    for category, amount in category_expenses.items():
        response += f'{category}: {amount}\n'
    bot.send_message(call.message.chat.id, response)


def handle_expense_category(message):
    expense_category = message.text
    msg = bot.send_message(message.chat.id, 'Введіть суму витрат та дату у форматі: сума дд.мм.рр')
    bot.register_next_step_handler(msg, save_expense, expense_category)


def save_expense(message, category):
    try:
        amount, date_text = message.text.split()
        date = datetime.strptime(date_text, '%d.%m.%y')
        expense_records.append({'category': category, 'amount': amount, 'date': date.strftime('%d.%m.%y')})
        bot.send_message(message.chat.id, 'Витрати збережено!')
        save_data_to_json('expense.json', expense_records)
    except ValueError:
        bot.send_message(message.chat.id, 'Неправильний формат, спробуйте ще раз.')


@bot.callback_query_handler(func=lambda call: call.data == 'expense_info')
def handle_expense_info(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('Витрати за день', callback_data='expenses_day')
    btn2 = types.InlineKeyboardButton('Витрати за тиждень', callback_data='expenses_week')
    btn3 = types.InlineKeyboardButton('Витрати за місяць', callback_data='expenses_month')
    btn4 = types.InlineKeyboardButton('Витрати за весь період', callback_data='expenses_all')
    btn5 = types.InlineKeyboardButton('Видалити витрати', callback_data='delete_expenses')
    markup.add(btn1, btn2, btn3, btn4, btn5)
    bot.send_message(call.message.chat.id, 'Виберіть період для аналізу витрат', reply_markup=markup)


def filter_expenses_by_date(records, time_period):
    today = datetime.today().date()
    if time_period == 'day':
        return [record for record in records if datetime.strptime(record['date'], '%d.%m.%y').date() == today]
    elif time_period == 'week':
        week_start = today - timedelta(days=today.weekday())
        return [record for record in records if
                week_start <= datetime.strptime(record['date'], '%d.%m.%y').date() <= today]
    elif time_period == 'month':
        month_start = today.replace(day=1)
        month_end = today.replace(day=1, month=today.month + 1) - timedelta(days=1)
        return [record for record in records if
                month_start <= datetime.strptime(record['date'], '%d.%m.%y').date() <= month_end]
    else:
        return records


def calculate_category_expenses(expense_records):
    category_expenses = {}
    for record in expense_records:
        category = record['category']
        amount = int(record['amount'])
        if category in category_expenses:
            category_expenses[category] += amount
        else:
            category_expenses[category] = amount
    return category_expenses


@bot.callback_query_handler(func=lambda call: call.data == 'total_expense')
def handle_total_expense(call):
    total_amount = sum(int(record['amount']) for record in expense_records)
    category_expenses = calculate_category_expenses(expense_records)
    response = f'Загальні витрати за весь період: {total_amount}\n\n'
    response += 'Витрати за категоріями:\n'
    for category, amount in category_expenses.items():
        response += f'{category.capitalize()}: {amount}\n'
    bot.send_message(call.message.chat.id, response)


@bot.callback_query_handler(func=lambda call: call.data.startswith('Витрати за '))
def handle_expenses_analysis(call):
    time_period = call.data.split('Витрати за ')[1].lower()
    filtered_expenses = filter_expenses_by_date(expense_records, time_period)
    total_expenses = sum(int(record['amount']) for record in filtered_expenses)
    category_expenses = calculate_category_expenses(filtered_expenses)
    response = f'Загальні витрати за {time_period}: {total_expenses}\n\n'
    response += 'Витрати за категоріями:\n'
    for category, amount in category_expenses.items():
        response += f'{category}: {amount}\n'
    bot.send_message(call.message.chat.id, response)


def save_data_to_json(file_name, data):
    with open(file_name, 'w') as json_file:
        json.dump(data, json_file)


@bot.callback_query_handler(func=lambda call: call.data == 'delete_expenses')
def handle_delete_expenses(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    delete_buttons = [types.InlineKeyboardButton('Видалити всі витрати', callback_data='delete_all_expenses')]
    markup.add(*delete_buttons)
    bot.send_message(call.message.chat.id, 'Оберіть опцію видалення витрат:', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'delete_all_expenses')
def handle_delete_all_expenses(call):
    global expense_records
    expense_records = []
    save_data_to_json('expense.json', expense_records)
    bot.send_message(call.message.chat.id, 'Всі витрати були видалені.')


bot.polling(none_stop=True)
