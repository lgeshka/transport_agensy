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
    
    # Получаем все бронирования (без first_name, last_name)
    cur.execute("""
        SELECT tb.id, u.login, u.id as user_id,
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
        SELECT r.id, u.id, u.login, r.report, r.created_at
        FROM reports r
        JOIN users u ON r.user_id = u.id
        ORDER BY r.created_at DESC
    """)
    reports = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('admin.html', bookings=bookings, logs=logs, reports=reports)