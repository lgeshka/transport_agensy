from flask import Flask, render_template, request, session, redirect, url_for, jsonify, send_file
from flask import send_from_directory
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import psycopg2
import tempfile
import tempfile
import os
from datetime import datetime, date, time

app = Flask(__name__)
app.secret_key = ''


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

def get_db_connection():
    return psycopg2.connect(
        host="-",
        database="-", 
        user="-",
        password="-"
    )


def search_routes(departure_city, arrival_city, departure_date, transport_type, company_id, route_number):
    conn = get_db_connection()
    cur = conn.cursor()
    current_datetime = datetime.now()
    current_date = current_datetime.date()
    current_time = current_datetime.time()
    query = """SELECT r.route_number, c.name, d1.city, d2.city, 
           r.departure_date, r.departure_time, r.arrival_time, 
           r.duration, r.price, r.transport_type FROM routes r
    JOIN companies c ON r.company_id = c.id
    JOIN directions d1 ON r.departure_city_id = d1.id
    JOIN directions d2 ON r.arrival_city_id = d2.id WHERE 1=1"""
    params = []
    if departure_date:
        query += " AND r.departure_date = %s"
        params.append(departure_date)
        if departure_date == current_date.isoformat():
            query += " AND r.departure_time >= %s"
            params.append(current_time)
    else:
        query += " AND (r.departure_date > %s OR (r.departure_date = %s AND r.departure_time >= %s))"
        params.extend([current_date, current_date, current_time])
    if route_number:
        query += " AND r.route_number ILIKE %s"
        params.append(f'%{route_number}%')
    if departure_city:
        query += " AND (d1.city ILIKE %s OR d1.code ILIKE %s)"
        params.extend([f'%{departure_city}%', f'%{departure_city.upper()}%'])
    if arrival_city:
        query += " AND (d2.city ILIKE %s OR d2.code ILIKE %s)"
        params.extend([f'%{arrival_city}%', f'%{arrival_city.upper()}%'])
    if transport_type and transport_type != 'any':
        query += " AND r.transport_type = %s"
        params.append(transport_type)
    if company_id and company_id != 'any':
        query += " AND r.company_id = %s"
        params.append(int(company_id))
    query += " ORDER BY r.departure_date, r.departure_time"
    cur.execute(query, params)
    routes = cur.fetchall()
    cur.close()
    conn.close()
    return routes

def get_companies():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM companies ORDER BY name")
    companies = cur.fetchall()
    cur.close()
    conn.close()
    return companies

def check_user_credentials(login, password):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE login = %s AND password = %s", (login, password))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user is not None

@app.route('/', methods=['GET', 'POST'])
def travel():
    companies = get_companies()
    cities = get_cities()
    today = date.today()
    default_date = today.strftime('%Y-%m-%d')
    if request.method == 'POST':
        departure_city = request.form['departure_city'].strip()
        arrival_city = request.form['arrival_city'].strip()
        departure_date = request.form['departure_date']
        transport_type = request.form.get('transport_type', 'any')
        company_id = request.form.get('company_id', 'any')
        route_number = request.form.get('route_number', '').strip()
        routes = search_routes(departure_city, arrival_city, departure_date, 
                                transport_type, company_id, route_number) 
        return render_template('travel.html', routes=routes, departure_city=departure_city,
                            arrival_city=arrival_city, departure_date=departure_date,
                            transport_type=transport_type, company_id=company_id,
                            route_number=route_number, companies=companies, cities=cities,
                            default_date=default_date)
    return render_template('travel.html', routes=None, companies=companies, cities=cities,
                          default_date=default_date)

@app.route('/account', methods=['GET', 'POST'])
def account():
    if 'logged_in' in session and session['logged_in']:
        if session.get('is_admin'):
            return redirect(url_for('admin_panel'))
        user_id = session.get('user_id')
        bookings = get_user_bookings(user_id)
        if request.method == 'POST':
            if 'register' in request.form:
                first_name = request.form['first_name'].strip()
                last_name = request.form['last_name'].strip()
                document = request.form['document'].strip()
                login = request.form['reg_login'].strip()
                password = request.form['reg_password'].strip()
                if not all([first_name, last_name, document, login, password]):
                    return render_template('account.html', reg_error='Заполните все поля', bookings=bookings)
                if check_user_exists(login):
                    return render_template('account.html', reg_error='Пользователь с таким логином уже существует', bookings=bookings)
                if create_user(first_name, last_name, document, login, password):
                    return render_template('account.html', reg_success='Регистрация успешна', bookings=bookings)
                else:
                    return render_template('account.html', reg_error='Ошибка при регистрации', bookings=bookings)
        return render_template('account.html', bookings=bookings)
    else:
        if request.method == 'POST':
            if 'register' in request.form:
                first_name = request.form['first_name'].strip()
                last_name = request.form['last_name'].strip()
                document = request.form['document'].strip()
                login = request.form['reg_login'].strip()
                password = request.form['reg_password'].strip()
                if not all([first_name, last_name, document, login, password]):
                    return render_template('account.html', reg_error='Заполните все поля')
                if check_user_exists(login):
                    return render_template('account.html', reg_error='Пользователь с таким логином уже существует')
                if create_user(first_name, last_name, document, login, password):
                    return render_template('account.html', reg_success='Регистрация успешна')
                else:
                    return render_template('account.html', reg_error='Ошибка при регистрации')
            else:
                login = request.form['login'].strip()
                password = request.form['password'].strip()
                user = get_user_id_and_admin(login, password)
                if user:
                    user_id, is_admin = user
                    add_login_log(user_id, is_admin)
                    session['logged_in'] = True
                    session['username'] = login
                    session['user_id'] = user_id
                    session['is_admin'] = is_admin
                    if is_admin:
                        return redirect(url_for('admin_panel'))
                    bookings = get_user_bookings(user_id)
                    return render_template('account.html', success='Успешный вход', bookings=bookings)
                else:
                    return render_template('account.html', error='Неверный логин или пароль')
        return render_template('account.html')
    
def get_cities():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT city FROM directions WHERE city IS NOT NULL ORDER BY city")
    cities = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return cities

@app.route('/api/cities_with_coords')
def get_cities_with_coords():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""SELECT city, country, code, latitude, longitude 
        FROM directions WHERE latitude IS NOT NULL 
        AND longitude IS NOT NULL ORDER BY country, city""")
    cities = cur.fetchall()
    cur.close()
    conn.close()
    cities_list = []
    for city in cities:
        cities_list.append({
            'city': city[0],
            'country': city[1],
            'code': city[2],
            'lat': float(city[3]),
            'lng': float(city[4])
        })
    return jsonify({'success': True, 'cities': cities_list})

def get_user_id_and_admin(login, password):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, admin FROM users WHERE login = %s AND password = %s", (login, password))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def add_login_log(user_id, is_admin):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO logs (user_id, is_admin, login_time) VALUES (%s, %s, CURRENT_TIMESTAMP)", (user_id, is_admin))
    conn.commit()
    cur.close()
    conn.close()

def check_user_exists(login):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE login = %s", (login,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user is not None

def create_user(first_name, last_name, document, login, password):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""INSERT INTO users (first_name, last_name, document, login, password, admin) 
                      VALUES (%s, %s, %s, %s, %s, false)""", 
                   (first_name, last_name, document, login, password))
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        return False
    finally:
        cur.close()
        conn.close()

def book_ticket(user_id, route_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM routes WHERE route_number = %s", (route_id,))
        route_row = cur.fetchone()
        if route_row:
            route_db_id = route_row[0]
            cur.execute("""INSERT INTO ticket_booking (route_id, user_id, status) VALUES (%s, %s, 'забронирован') RETURNING id""", (route_db_id, user_id))
            booking_id = cur.fetchone()[0]
            conn.commit()
            return booking_id
        else:
            return None
    except Exception as e:
        print(f"Ошибка при бронировании: {e}")
        return None
    finally:
        cur.close()
        conn.close()

@app.route('/book_ticket/<route_number>', methods=['POST'])
def book_ticket_route(route_number):
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({'success': False, 'error': 'Требуется авторизация'})
    user_id = session.get('user_id')
    booking_id = book_ticket(user_id, route_number)
    if booking_id:
        return jsonify({'success': True, 'booking_id': booking_id})
    else:
        return jsonify({'success': False, 'error': 'Ошибка бронирования'})

def get_user_bookings(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    query = """SELECT 
        tb.id as booking_id,
        r.route_number,
        c.name as company_name,
        d1.city as departure_city,
        d1.code as departure_code,
        d2.city as arrival_city,
        d2.code as arrival_code,
        r.departure_date,
        r.departure_time,
        r.arrival_time,
        r.duration,
        r.price,
        tb.status,
        tb.created_at
    FROM ticket_booking tb
    JOIN routes r ON tb.route_id = r.id
    JOIN companies c ON r.company_id = c.id
    JOIN directions d1 ON r.departure_city_id = d1.id
    JOIN directions d2 ON r.arrival_city_id = d2.id
    WHERE tb.user_id = %s  -- Теперь фильтруем по user_id
    AND tb.status IN ('забронирован', 'оплачен')
    ORDER BY tb.created_at DESC"""
    cur.execute(query, (user_id,))
    bookings = cur.fetchall()
    cur.close()
    conn.close()
    return bookings

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('account'))

@app.route('/popular')
def popular():
    return render_template('popular.html')

def get_all_companies():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM companies ORDER BY name")
    companies = cur.fetchall()
    cur.close()
    conn.close()
    return companies

def load_partner_urls():
    urls = {}
    
    possible_paths = [
        os.path.join(app.root_path, 'partners_urls.txt.txt'),
    ]
    
    for file_path in possible_paths:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = line.split('|')
                            if len(parts) == 2:
                                company_id = parts[0].strip()
                                url = parts[1].strip()
                                urls[company_id] = url
                break
            except:
                pass
    
    return urls

@app.route('/partners')
def partners():
    companies = get_all_companies()
    partner_urls = load_partner_urls()
    return render_template('partners.html', companies=companies, partner_urls=partner_urls)
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/support', methods=['GET', 'POST'])
def support():
    if request.method == 'POST':
        if 'logged_in' not in session or not session['logged_in']:
            return render_template('support.html', error='Для отправки обращения необходимо авторизоваться')
        user_id = session.get('user_id')
        report_text = request.form['report'].strip()
        if not report_text:
            return render_template('support.html', error='Пожалуйста, введите текст обращения')
        report_id = create_report(user_id, report_text)
        if report_id:
            return render_template('support.html', success='Ваше обращение успешно отправлено! Номер обращения: {}'.format(report_id))
        else:
            return render_template('support.html', success='Ваше обращение успешно отправлено!')
    return render_template('support.html')

@app.route('/payment')
def payment():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('account'))
    booking_id = request.args.get('booking_id')
    if not booking_id:
        return redirect(url_for('account'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""SELECT tb.id FROM ticket_booking tb WHERE tb.id = %s AND tb.status = 'забронирован'""", (booking_id,))
    booking = cur.fetchone()
    cur.close()
    conn.close()
    if not booking:
        return redirect(url_for('account'))
    return render_template('payment.html', booking_id=booking_id)

@app.route('/pay_booking', methods=['POST'])
def pay_booking():
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({'success': False, 'error': 'Требуется авторизация'})
    try:
        data = request.get_json()
        booking_id = data.get('booking_id')
        card_number = data.get('card_number')
        expiry_date = data.get('expiry_date')
        cvv = data.get('cvv')
        if not all([booking_id, card_number, expiry_date, cvv]):
            return jsonify({'success': False, 'error': 'Заполните все поля'})
        user_id = session.get('user_id')
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM ticket_booking WHERE id = %s AND user_id = %s AND status = 'забронирован'", 
                   (booking_id, user_id))
        booking = cur.fetchone()
        if not booking:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Бронирование не найдено, уже оплачено или нет прав для оплаты'})
        cur.execute("""UPDATE ticket_booking SET status = 'оплачен' WHERE id = %s""", (booking_id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Оплата прошла успешно'})
    except Exception as e:
        print(f"Ошибка при оплате: {e}")
        return jsonify({'success': False, 'error': f'Внутренняя ошибка сервера: {str(e)}'})

def create_user(first_name, last_name, document, login, password):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""INSERT INTO users (first_name, last_name, document, login, password, admin) 
                      VALUES (%s, %s, %s, %s, %s, false)""", 
                   (first_name, last_name, document, login, password))
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        return False
    finally:
        cur.close()
        conn.close()

def get_booking_stats():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM ticket_booking")
    total_bookings = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM ticket_booking WHERE status != 'отменен'")
    active_bookings = cur.fetchone()[0]
    cur.close()
    conn.close()
    return total_bookings, active_bookings

def get_all_logs():
    conn = get_db_connection()
    cur = conn.cursor()
    query = """SELECT l.id,
        COALESCE(u.first_name, '') as first_name,
        COALESCE(u.last_name, '') as last_name,
        COALESCE(u.login, '') as login,
        u.id as user_id,
        l.is_admin,
        l.login_time
    FROM logs l JOIN users u ON l.user_id = u.id ORDER BY l.login_time DESC"""
    cur.execute(query)
    logs = cur.fetchall()
    cur.close()
    conn.close()
    return logs

@app.route('/admin')
def admin_panel():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('account'))
    if not session.get('is_admin'):
        return redirect(url_for('account'))
    bookings = get_all_bookings()
    logs = get_all_logs()
    reports = get_all_reports()
    return render_template('admin.html', bookings=bookings, logs=logs, reports=reports)

@app.route('/cancel_booking', methods=['POST'])
def cancel_booking():
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({'success': False, 'error': 'Требуется авторизация'})
    data = request.get_json()
    booking_id = data.get('booking_id')
    if not booking_id:
        return jsonify({'success': False, 'error': 'Не указан ID бронирования'})
    user_id = session.get('user_id')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM ticket_booking WHERE id = %s", (booking_id,))
    booking_exists = cur.fetchone()
    if not booking_exists:
        cur.close()
        conn.close()
        return jsonify({'success': False, 'error': 'Бронирование не найдено'})
    if not session.get('is_admin'):
        cur.execute("SELECT id FROM ticket_booking WHERE id = %s AND user_id = %s", 
                   (booking_id, user_id))
        user_booking = cur.fetchone()
        if not user_booking:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Нет прав для отмены этого бронирования'})
    cur.execute("UPDATE ticket_booking SET status = 'отменен' WHERE id = %s", (booking_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'success': True, 'message': 'Бронирование успешно отменено'})

def create_report(user_id, report_text):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""INSERT INTO reports (user_id, report, status, created_at) VALUES (%s, %s, 'отправлен', CURRENT_TIMESTAMP) RETURNING id""", (user_id, report_text))
    report_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

def get_all_bookings():
    conn = get_db_connection()
    cur = conn.cursor()
    query = """SELECT tb.id as booking_id, u.first_name, u.last_name, u.login, u.id as user_id,
        r.route_number, d1.code as departure_code, d2.code as arrival_code, r.departure_date, r.departure_time,
        r.arrival_time, r.price, tb.status, tb.created_at
    FROM ticket_booking tb JOIN routes r ON tb.route_id = r.id
    JOIN users u ON tb.user_id = u.id
    JOIN directions d1 ON r.departure_city_id = d1.id
    JOIN directions d2 ON r.arrival_city_id = d2.id ORDER BY tb.created_at DESC"""
    cur.execute(query)
    bookings = cur.fetchall()
    cur.close()
    conn.close()
    return bookings

def get_all_reports():
    conn = get_db_connection()
    cur = conn.cursor()
    query = """SELECT r.id as report_id, u.id as user_id,
        r.report, r.status, r.created_at, r.resolved_at
    FROM reports r JOIN users u ON r.user_id = u.id ORDER BY r.created_at DESC"""
    cur.execute(query)
    reports = cur.fetchall()
    cur.close()
    conn.close()
    return reports


pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
@app.route('/download_ticket/<int:booking_id>')
def download_ticket(booking_id):
    user_id = session.get('user_id')
    conn = get_db_connection()
    cur = conn.cursor()
    query = """SELECT tb.id, r.route_number, c.name, d1.city, d1.code, d2.city, d2.code, r.departure_date, r.departure_time, r.arrival_time, r.duration, r.price
    FROM ticket_booking tb
    JOIN routes r ON tb.route_id = r.id
    JOIN companies c ON r.company_id = c.id
    JOIN directions d1 ON r.departure_city_id = d1.id
    JOIN directions d2 ON r.arrival_city_id = d2.id
    WHERE tb.id = %s AND tb.user_id = %s AND tb.status = 'оплачен'"""
    cur.execute(query, (booking_id, user_id))
    booking = cur.fetchone()
    cur.close()
    conn.close()
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf_path = temp_file.name
    c = canvas.Canvas(pdf_path, pagesize=A4)
    c.setFont("Arial", 12)
    logo_path = os.path.join(app.root_path, 'static', 'images', 'logo')
    possible_extensions = ['.png', '.jpg', '.jpeg', '.gif']
    logo_found = False
    width, height = A4
    photo_width = 180
    photo_height = 90
    photo_x = 0
    photo_y = height - photo_height - 5
    for ext in possible_extensions:
        logo_file = logo_path + ext
        if os.path.exists(logo_file):
            img = ImageReader(logo_file)
            c.drawImage(img, photo_x, photo_y, width=photo_width, height=photo_height, preserveAspectRatio=True)
            logo_found = True
            break
    y = photo_y - 50
    text_x = 140
    text_y = photo_y + photo_height - 40
    stripe_height = 2
    stripe_y = photo_y - 10
    stripe_x = 0
    stripe_width = width
    corner_radius = 12
    c.setFillColorRGB(33/255, 150/255, 243/255)
    c.setStrokeColorRGB(33/255, 150/255, 243/255)
    c.roundRect(stripe_x, stripe_y, stripe_width, stripe_height, corner_radius, fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0)
    c.setStrokeColorRGB(0, 0, 0)
    c.setFont("Arial", 26)
    c.drawString(text_x, text_y, "Транспортное")
    text_y -= 25
    c.drawString(text_x, text_y, "Агентство")
    electronic_x = text_x + 275 
    electronic_y = photo_y + photo_height - 40
    c.setFont("Arial", 10)
    c.drawString(electronic_x, electronic_y, "ЭЛЕКТРОННЫЙ БИЛЕТ")
    electronic_y -= 20
    c.drawString(electronic_x, electronic_y, "(МАРШРУТ/КВИТАНЦИЯ)")
    c.setFont("Arial", 12)
    y = photo_y - 25
    bg_x = 20
    bg_width = width - 40
    c.setFillColorRGB(0.87, 0.92, 1.0)
    c.setStrokeColorRGB(0.87, 0.92, 1.0)
    c.roundRect(bg_x, 528, bg_width, 182, 15, fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0)
    c.setStrokeColorRGB(0, 0, 0)
    c.setFont("Arial", 12)
    y -= 30
    c.drawString(100, y, f"Билет №{booking[0]}")
    c.drawString(400, y, f"Номер рейса: {booking[1]}")
    y -= 30
    c.drawString(245, y, f"Компания: {booking[2]}")
    y -= 30
    c.drawString(170, y, f"{booking[3]} ({booking[4]}) -> {booking[5]} ({booking[6]})")
    y -= 30
    c.drawString(245, y, f"Дата: {booking[7]}")
    y -= 30
    c.drawString(100, y, f"Вылет: {booking[8]}")
    c.drawString(235, y, f"Длительность: {booking[10]}")
    c.drawString(400, y, f"Прилет: {booking[9]}")
    y -= 30
    c.drawString(245, y, f"Цена: {booking[11]} руб.")
    footer_height = 360
    footer_y = 0
    for i in range(footer_height):
        ratio = i / footer_height
        r = 33/255 + (1 - 33/255) * ratio
        g = 150/255 + (1 - 150/255) * ratio
        b = 243/255 + (1 - 243/255) * ratio
    
        c.setFillColorRGB(r, g, b)
        c.setStrokeColorRGB(r, g, b)
        c.rect(0, footer_y + i, width, 1, fill=1, stroke=0)
    red_bg_x = 20
    red_bg_y = 528 - 120
    red_bg_width = width - 40
    red_bg_height = 105
    c.setFillAlpha(0.54)
    c.setStrokeAlpha(0.54)
    c.setFillColorRGB(1.0, 0.2, 0.2)
    c.setStrokeColorRGB(1.0, 0.2, 0.2)
    c.roundRect(red_bg_x, red_bg_y, red_bg_width, red_bg_height, 15, fill=1, stroke=0)
    c.setFillAlpha(1.0)
    c.setStrokeAlpha(1.0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Arial", 11)
    text_x = red_bg_x + 20
    text_y = red_bg_y + red_bg_height - 30
    c.drawString(text_x, text_y, "Для внутренних рейсов рекомендуем прибыть в аэропорт/вокзал/порт за 1,5 часа до отправления.")
    text_y -= 25
    c.drawString(text_x, text_y, "Для международных рейсов рекомендуем прибыть за 3 часа для прохождения паспортного контроля.")
    text_y -= 25
    c.drawString(135, text_y, "При изменении ваших планов обратитесь в службу поддержки.")
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Arial", 14)
    footer_text1 = "ООО «Транспортная агентство»"
    text1_width = len(footer_text1) * 7
    text1_x = (width - text1_width) / 2
    c.drawString(text1_x, 30, footer_text1)
    footer_text2 = "Возникли вопросы? Служба поддержки 8-800-555-35-35"
    text2_width = len(footer_text2) * 7
    text2_x = (width - text2_width) / 2
    c.drawString(text2_x, 50, footer_text2)
    c.save()
    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"ticket_{booking[0]}.pdf",
        mimetype='application/pdf'
    )

@app.route('/api/routes')
def get_routes():
    conn = get_db_connection()
    cur = conn.cursor()
    query = """
    SELECT 
        r.route_number,
        r.transport_type,
        c.name as company_name,
        d1.latitude as departure_lat,
        d1.longitude as departure_lon,
        d2.latitude as arrival_lat,
        d2.longitude as arrival_lon
    FROM routes r
    JOIN companies c ON r.company_id = c.id
    JOIN directions d1 ON r.departure_city_id = d1.id
    JOIN directions d2 ON r.arrival_city_id = d2.id
    WHERE d1.latitude IS NOT NULL AND d1.longitude IS NOT NULL
      AND d2.latitude IS NOT NULL AND d2.longitude IS NOT NULL
    LIMIT 50
    """
    cur.execute(query)
    routes = cur.fetchall()
    cur.close()
    conn.close()
    routes_list = []
    for route in routes:
        routes_list.append({
            'route_number': route[0],
            'transport_type': route[1],
            'company_name': route[2],
            'departure_lat': route[3],
            'departure_lon': route[4],
            'arrival_lat': route[5],
            'arrival_lon': route[6]
        })
    
    return jsonify({'success': True, 'routes': routes_list})


if __name__ == '__main__':
    app.run(debug=True)