## Транспортное Агентство

Веб-приложение для поиска и бронирования билетов на различные виды транспорта (авиа, ж/д, речной).
- Поиск рейсов с фильтрацией по городу, дате, компании, типу транспорта.
- Регистрация и авторизация пользователей.
- Бронирование билетов (с таймером 15 минут на оплату).
- Имитация оплаты банковской картой.
- Скачивание электронного билета в PDF.
- Личный кабинет с историей бронирований.
- Админ-панель для управления бронированиями.
- Страницы: Популярные направления, Партнёры, FAQ, Поддержка, О нас.
- Интерактивная карта с обслуживаемыми городами.

##  Структура проекта
project/

main.py # Точка входа, регистрация Blueprint

config.py # Конфигурация подключения к БД

requirements.txt # Зависимости Python

service/ # Backend логика

common.py # Общие функции (хеширование, БД)

init.py # Подключение к PostgreSQL

routes/ # Основные маршруты

search.py # Поиск рейсов, бронирование

 account/ # Личный кабинет
 
profile.py # Авторизация, регистрация, брони

payment.py # Имитация оплаты

download.py # Генерация PDF билета

admin/ # Админ-панель

panel.py # Управление бронями, логами, обращениями

any_services/ # Вспомогательные страницы

about.py # О нас + API городов с координатами

cities.py # Список обслуживаемых городов

popular.py # Популярные направления

partners.py # Компании-партнёры

faq.py # Часто задаваемые вопросы

hotels.py # Бронирование отелей

vip.py # VIP-партнёры

cargo.py # Грузоперевозки

vacancy.py # Вакансии

ruls.py # Правила перевозки

howtobuy.py # Как купить билет

advertisement.py # Реклама на сайте

connect_to_partner.py # Сотрудничество

politica_conf.py # Политика конфиденциальности 

whereisplane.py # Отслеживание рейса

reports/ # Обратная связь

support.py # Обращения в поддержку

templates/ # HTML шаблоны

travel.html # Главная страница поиска

account.html # Личный кабинет

admin.html # Админ-панель

payment.html # Страница оплаты

about.html # О нас с картой

cities.html # Список городов с поиском

partners.html # Карточки компаний-партнёров

popular.html # Популярные направления

support.html # Служба поддержки

status.html # Отслеживание рейса

faq.html # FAQ

 _navbar.html # Навигационная панель
 
 _footer.html # Подвал сайта
 
[заглушки].html # Остальные страницы в разработке

static/ # Статические файлы

css/

style.css # Основные стили

images/

logo.png # Логотип

logos/ # Логотипы компаний

destinations/ # Фото городов для раздела "Популярное"

txt/

partners_urls.txt # Ссылки на сайты партнёров (id|url)

favicon.ico

Для установки необходимых библиотек требуется прописать в консоли: `pip install -r requirements.txt`

Для корректной работы необходимо прописать пароль и секретный ключ в файле config.py и .env.

Для запуска необходимо запустить main.py.


## Структура БД:
-- Таблица пользователей
```
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    login VARCHAR(50) UNIQUE NOT NULL, 
    password VARCHAR(128) NOT NULL,
    email VARCHAR(100),
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    admin BOOLEAN DEFAULT FALSE
);
```

-- Таблица направлений (города)
```
CREATE TABLE directions (
    id SERIAL PRIMARY KEY,
    country VARCHAR(100),
    city VARCHAR(100),
    latitude NUMERIC(10,8),
    longitude NUMERIC(11,8),
    code VARCHAR(10)
);
```

-- Таблица компаний-перевозчиков
```
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50)  -- avia / railway / river
);
```

-- Таблица рейсов
```
CREATE TABLE routes (
    id SERIAL PRIMARY KEY,
    number VARCHAR(20) NOT NULL,
    company_id INTEGER REFERENCES companies(id),
    departure_id INTEGER REFERENCES directions(id),
    arrival_id INTEGER REFERENCES directions(id),
    data DATE NOT NULL,
    departure_time TIME NOT NULL,
    arrival_time TIME NOT NULL,
    travel_time TIME NOT NULL,
    price NUMERIC(10,2)
);
```

-- Таблица бронирований
```
CREATE TABLE ticket_booking (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    route_id INTEGER REFERENCES routes(id),
    status VARCHAR(20) DEFAULT 'забронирован',  -- забронирован / оплачен / отменен
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

-- Таблица логов входов
```
CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

-- Таблица обращений в поддержку
```
CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    route_id INTEGER REFERENCES routes(id),
    report VARCHAR(400) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
