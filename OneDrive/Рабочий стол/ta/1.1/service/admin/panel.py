# service/admin/panel.py
from service.common import *

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in') or not session.get('is_admin'):
            return redirect(url_for('account.account_page'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin')
@admin_required
def admin_panel():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Получаем все бронирования
    cur.execute("""
        SELECT tb.id, u.login, tb.user_id,
               r.number, d1.city, d2.city, r.data, r.departure_time,
               r.arrival_time, r.price, tb.status, tb.created_at
        FROM ticket_booking tb
        JOIN users u ON tb.user_id = u.id
        JOIN routes r ON tb.route_id = r.id
        JOIN directions d1 ON r.departure_id = d1.id
        JOIN directions d2 ON r.arrival_id = d2.id
        ORDER BY tb.created_at DESC
    """)
    bookings = cur.fetchall()
    
    # Получаем пользователей
    cur.execute("""
        SELECT id, login, email, created_time, admin
        FROM users
        ORDER BY id
    """)
    users = cur.fetchall()
    
    # Получаем логи
    cur.execute("""
        SELECT l.id, u.login, u.id, u.admin, l.time
        FROM logs l
        JOIN users u ON l.user_id = u.id
        ORDER BY l.time DESC
    """)
    logs = cur.fetchall()
    
    # Получаем обращения
    cur.execute("""
        SELECT r.id, u.id, u.login, u.email, r.report, r.created_at, r.status
        FROM reports r
        JOIN users u ON r.user_id = u.id
        ORDER BY r.created_at DESC
    """)
    reports = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('admin.html', bookings=bookings, logs=logs, reports=reports, users=users)

@admin_bp.route('/cancel_booking_admin', methods=['POST'])
@admin_required
def cancel_booking_admin():
    data = request.get_json()
    booking_id = data.get('booking_id')
    
    if not booking_id:
        return jsonify({'success': False, 'error': 'Не указан ID бронирования'})
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("UPDATE ticket_booking SET status = 'отменен' WHERE id = %s", (booking_id,))
        conn.commit()
        return jsonify({'success': True, 'message': 'Бронирование отменено'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cur.close()
        conn.close()

@admin_bp.route('/change_report_status', methods=['POST'])
@admin_required
def change_report_status():
    data = request.get_json()
    report_id = data.get('report_id')
    new_status = data.get('status')
    
    if not report_id or not new_status:
        return jsonify({'success': False, 'error': 'Не указаны параметры'})
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("UPDATE reports SET status = %s WHERE id = %s", (new_status, report_id))
        conn.commit()
        return jsonify({'success': True, 'message': 'Статус обновлен'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cur.close()
        conn.close()