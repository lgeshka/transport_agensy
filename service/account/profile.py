from service.common import *

account_bp = Blueprint('account', __name__)

def get_user_by_login(login):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, login, password, email, admin FROM users WHERE login = %s", (login,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def create_user(login, password, email):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        salt, hashed_password = hash_password(password)
        password_hash = f"{salt}:{hashed_password}"
        
        cur.execute("INSERT INTO users (login, password, email, admin) VALUES (%s, %s, %s, %s)",
                   (login, password_hash, email, False))
        conn.commit()
        print(f"Пользователь {login} добавлен в БД с хешированным паролем")
        return True
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при создании пользователя: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def check_user_password(login, password):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, login, password, admin FROM users WHERE login = %s", (login,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if user:
        stored_password = user[2]
        if ':' in stored_password:
            salt, hash_value = stored_password.split(':')
            if check_password(password, salt, hash_value):
                return user
    return None

def get_user_bookings(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT tb.id, r.number, c.name, d1.city, d2.city, 
               r.data, r.departure_time, r.arrival_time, r.travel_time, r.price, 
               tb.status, tb.created_at
        FROM ticket_booking tb
        JOIN routes r ON tb.route_id = r.id
        JOIN companies c ON r.company_id = c.id
        JOIN directions d1 ON r.departure_id = d1.id
        JOIN directions d2 ON r.arrival_id = d2.id
        WHERE tb.user_id = %s
        ORDER BY tb.created_at DESC
    """, (user_id,))
    bookings = cur.fetchall()
    cur.close()
    conn.close()
    return bookings

@account_bp.route('/account', methods=['GET', 'POST'])
def account_page():
    if 'logged_in' in session and session['logged_in']:
        user_id = session.get('user_id')
        is_admin = session.get('is_admin', False)
        
        if is_admin:
            return redirect(url_for('admin.admin_panel'))
        
        bookings = get_user_bookings(user_id)
        return render_template('account.html', bookings=bookings)
    
    else:
        if request.method == 'POST':
            if 'register' in request.form:
                login = request.form.get('reg_login', '').strip()
                password = request.form.get('reg_password', '').strip()
                email = request.form.get('email', '').strip()
                
                if not all([login, password, email]):
                    return render_template('account.html', reg_error='Заполните все поля')
                
                if get_user_by_login(login):
                    return render_template('account.html', reg_error='Пользователь уже существует')
                
                if create_user(login, password, email):
                    return render_template('account.html', reg_success='Регистрация успешна')
                else:
                    return render_template('account.html', reg_error='Ошибка при регистрации')
            
            else:
                login = request.form.get('login', '').strip()
                password = request.form.get('password', '').strip()
                
                user = check_user_password(login, password)
                if user:
                    session['logged_in'] = True
                    session['username'] = login
                    session['user_id'] = user[0]
                    session['is_admin'] = user[3] if len(user) > 3 and user[3] else False
                    
                    if session['is_admin']:
                        return redirect(url_for('admin.admin_panel'))
                    else:
                        return redirect(url_for('account.account_page'))
                
                return render_template('account.html', error='Неверный логин или пароль')
        
        return render_template('account.html')

@account_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('account.account_page'))

@account_bp.route('/cancel_booking', methods=['POST'])
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
    
    try:
        cur.execute("SELECT id FROM ticket_booking WHERE id = %s AND user_id = %s AND status = 'забронирован'", 
                   (booking_id, user_id))
        booking = cur.fetchone()
        
        if not booking:
            return jsonify({'success': False, 'error': 'Бронирование не найдено или уже оплачено'})
        
        cur.execute("UPDATE ticket_booking SET status = 'отменен' WHERE id = %s", (booking_id,))
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Бронирование отменено'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cur.close()
        conn.close()