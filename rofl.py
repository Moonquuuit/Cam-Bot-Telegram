import os
import time
import cv2
import telebot
from tempfile import NamedTemporaryFile
from telebot import types

bot = telebot.TeleBot("You TOKEN")
ADMIN_ID = ID Admin

last_message_time = {}
last_photos = {}
cam_usage_count = {}
usernames = {}

is_bot_active = True
user_commands = ['/start', '/status', '/cam', '/help', '/menu']

# Функция для применения фильтра к фотографии
def apply_filter(image):
    return image
    
def save_to_cloud(photo):
    pass

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я бот для съемки и отправки фотографий. Просто отправь мне команду /cam, чтобы сделать фото и получить его. 😊")

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "Напиши команду /menu, и выбери, что тебе нужно! 😊")

@bot.message_handler(commands=['cam'])
def take_photo(message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Проверяем время последнего сообщения пользователя
    if user_id in last_message_time:
        current_time = time.time()
        if current_time - last_message_time[user_id] < 60:
            bot.reply_to(message, "Подождите, перед отправкой нового сообщения должно пройти минута. ⏳")
            return

    # Включаем первую камеру
    cap = cv2.VideoCapture(0)

    # Устанавливаем более высокое разрешение камеры
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    # Уменьшаем количество "прогревающих" кадров
    for i in range(20):
        cap.read()
   
    ret, frame = cap.read()

    # Проверяем успешность считывания кадра
    if ret:
        filtered_frame = apply_filter(frame)
        with NamedTemporaryFile(delete=False, suffix='.png') as temp_photo:
            cv2.imwrite(temp_photo.name, filtered_frame, [cv2.IMWRITE_PNG_COMPRESSION, 0])
            photo = open(temp_photo.name, 'rb')
            bot.send_photo(message.chat.id, photo)
            last_message_time[user_id] = time.time()
            last_photos[user_id] = temp_photo.name
            cam_usage_count[(user_id, username)] = cam_usage_count.get((user_id, username), 0) + 1
            usernames[user_id] = username
            save_to_cloud(temp_photo.name)
            user_info = f"Команду вызвал: {message.from_user.first_name} (@{username})"
            bot.send_message(ADMIN_ID, user_info)

    else:
        bot.reply_to(message, "Не удалось сделать снимок. Пожалуйста, попробуйте еще раз. ❌")

    # Отключаем камеру
    cap.release()

@bot.message_handler(commands=['menu'])
def show_menu(message):
    if message.from_user.id != ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for command in user_commands:
            markup.add(types.KeyboardButton(command))
        bot.send_message(message.chat.id, "Выберите команду из меню:", reply_markup=markup)
    else:
        bot.reply_to(message, "Эта команда доступна только пользователям. ❌")

@bot.message_handler(commands=['stop'])
def stop_bot(message):
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(message, "Бот остановлен.")
        global is_bot_active
        is_bot_active = False
    else:
        bot.reply_to(message, "У вас нет прав на выполнение этой команды. ❌")

@bot.message_handler(commands=['status'])
def bot_status(message):
    if is_bot_active:
        bot.reply_to(message, "Бот активен.")
    else:
        bot.reply_to(message, "Бот неактивен. ❌")

@bot.message_handler(commands=['panel'])
def show_stats(message):
    if message.from_user.id == ADMIN_ID:
        stats_message = "Статистика использования команды /cam:\n"
        for (user_id, username), count in cam_usage_count.items():
            stats_message += f"@{usernames[user_id]}: {count} раз\n"
        bot.reply_to(message, stats_message)
    else:
        bot.reply_to(message, "У вас нет прав на выполнение этой команды. ❌")

# Запуск бота
bot.polling()
