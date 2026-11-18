# Foodgram («Фудграм»)

Сервис для публикации рецептов, подписок на авторов, избранного и
списка покупок. Проект состоит из готового фронтенда на React и
бэкенда на Django REST Framework.

## Стек

- Python 3.12, Django 4.2, Django REST Framework, Djoser
- PostgreSQL 13
- Gunicorn, nginx
- Docker и Docker Compose for сборки и запуска

## Структура проекта

```
backend/    — Django-проект и API
frontend/   — готовый React-фронтенд
data/       — CSV с ингредиентами
docs/       — OpenAPI-спецификация и Redoc
nginx/      — Dockerfile и конфигурация nginx
infra/      — Docker Compose и переменные окружения
tests.yml   — данные администратора для проверки проекта
```



## Тестовые пользователи

| Роль          | Email                | Пароль             |
|---------------|----------------------|--------------------|
| Администратор | admin@foodgram.ru    | FoodgramAdmin123   |
| Пользователь  | anna@foodgram.ru     | Foodgram123        |
| Пользователь  | ivan@foodgram.ru     | Foodgram123        |
| Пользователь  | maria@foodgram.ru    | Foodgram123        |

Логин выполняется по email. Администратор задаётся переменными
`ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_USERNAME`.

## Команды управления

- `python manage.py load_ingredients` — загружает ингредиенты из
- `python manage.py load_demo_data` — создаёт тестовых пользователей,
  рецепты и избранное (идемпотентно).
- `python manage.py create_admin` — создаёт или обновляет
  администратора из переменных окружения.



## Тесты и линтер

```bash
cd backend
python manage.py test
flake8 .
```