[![CI](https://github.com/yandex-praktikum/hw05_final/actions/workflows/python-app.yml/badge.svg?branch=master)](https://github.com/yandex-praktikum/hw05_final/actions/workflows/python-app.yml)

# Социальная сеть блогеров
Многостраничное приложение (Multi-Page App, MPA) преднозначено для публикации постов на различные темы, пользователи могут добавлять/редактировать посты, подписаться на любимых авторов, оставлять комментарии к постам.

## Описание
Это приложение преднозначено для публикации постов на различные темы, пользователи могут добавить/отредактировать пост, подписаться на любимых авторов, оставить комментарий к посту.

## Технологии
#### Архитектура MPA
|Language|Framework|Database|
|--------|---------|--------|
|Python 3.9 |Django 4.2  |SQLite3

## Установка и запуск проекта:

> #### _Команды для консоли могут отличаться, данная инструкция адаптирована под OS Windows с использованием командной строки Git Bash._

Для развертывания проекта локально необходимо предварительно создать директорию для проекта ```django_blog_projectproject```.

- Из локально созданой директории ```django_blog_projectproject``` необходимо выполнить команду для консоли:
```
git clone https://github.com/MendeIT/django_blog_projectproject
```
- В корневом репозитории создайте файл ```.env``` наполните данными, как указано в примере ```example.env```.
- Установите и активируйте виртуальное окружение:
```
python -m venv venv
source venv/Scripts/activate
``` 
- Установите зависимости из файла requirements.txt:
```
pip install -r requirements.txt
``` 
- В репозитории с файлом manage.py выполните команду:
```
python manage.py runserver
```
---
## Автор
Алдар Дорджиев  
dordzhiev.aldar@yandex.ru