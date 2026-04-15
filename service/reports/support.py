from service.common import *

support_bp = Blueprint('support', __name__)

def create_report(user_id, report_text):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""INSERT INTO reports (user_id, report) 
                      VALUES (%s, %s) RETURNING id""", 
                   (user_id, report_text))
        report_id = cur.fetchone()[0]
        conn.commit()
        return report_id
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при создании обращения: {e}")
        return None
    finally:
        cur.close()
        conn.close()

@support_bp.route('/support', methods=['GET', 'POST'])
def support():
    if request.method == 'POST':
        if 'logged_in' not in session or not session['logged_in']:
            return render_template('support.html', error='Для отправки обращения необходимо авторизоваться')
        
        user_id = session.get('user_id')
        report_text = request.form.get('report', '').strip()
        
        if not report_text:
            return render_template('support.html', error='Пожалуйста, введите текст обращения')
        
        report_id = create_report(user_id, report_text)
        if report_id:
            return render_template('support.html', success=f'Ваше обращение успешно отправлено! Номер обращения: {report_id}')
        else:
            return render_template('support.html', error='Ошибка при отправке обращения')
    
    return render_template('support.html')