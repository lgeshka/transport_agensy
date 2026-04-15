from service.common import *

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/payment')
def payment_page():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('account.account_page'))
    
    booking_id = request.args.get('booking_id')
    if not booking_id:
        return redirect(url_for('account.account_page'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM ticket_booking WHERE id = %s AND user_id = %s AND status = 'забронирован'", 
               (booking_id, session['user_id']))
    booking = cur.fetchone()
    cur.close()
    conn.close()
    
    if not booking:
        return redirect(url_for('account.account_page'))
    
    return render_template('payment.html', booking_id=booking_id)

@payment_bp.route('/pay_booking', methods=['POST'])
def pay_booking():
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({'success': False, 'error': 'Требуется авторизация'})
    
    try:
        data = request.get_json()
        booking_id = data.get('booking_id')
        
        if not booking_id:
            return jsonify({'success': False, 'error': 'Не указан ID бронирования'})
        
        user_id = session.get('user_id')
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM ticket_booking WHERE id = %s AND user_id = %s AND status = 'забронирован'", 
                   (booking_id, user_id))
        booking = cur.fetchone()
        
        if not booking:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Бронирование не найдено или уже оплачено'})
        
        cur.execute("UPDATE ticket_booking SET status = 'оплачен' WHERE id = %s", (booking_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Оплата прошла успешно'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Ошибка: {str(e)}'})