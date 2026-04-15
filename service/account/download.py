# service/account/download.py
from service.common import *
from flask import send_file, current_app
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import tempfile
import os

download_bp = Blueprint('download', __name__)

# Регистрируем шрифт
try:
    pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
except:
    pass

@download_bp.route('/download_ticket/<int:booking_id>')
def download_ticket(booking_id):
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('account.account_page'))
    
    user_id = session.get('user_id')
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Добавили d1.code и d2.code
    query = """SELECT tb.id, r.number, c.name, d1.city, d1.code, d2.city, d2.code, 
                      r.data, r.departure_time, r.arrival_time, r.travel_time, r.price
               FROM ticket_booking tb
               JOIN routes r ON tb.route_id = r.id
               JOIN companies c ON r.company_id = c.id
               JOIN directions d1 ON r.departure_id = d1.id
               JOIN directions d2 ON r.arrival_id = d2.id
               WHERE tb.id = %s AND tb.user_id = %s AND tb.status = 'оплачен'"""
    
    cur.execute(query, (booking_id, user_id))
    booking = cur.fetchone()
    cur.close()
    conn.close()
    
    if not booking:
        return redirect(url_for('account.account_page'))
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf_path = temp_file.name
    c = canvas.Canvas(pdf_path, pagesize=A4)
    c.setFont("Arial", 12)
    
    # Логотип
    logo_path = os.path.join(current_app.root_path, 'static', 'images', 'logo')
    possible_extensions = ['.png', '.jpg', '.jpeg', '.gif']
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
            break
    
    text_x = 140
    text_y = photo_y + photo_height - 40
    
    # Синяя полоска
    stripe_height = 2
    stripe_y = photo_y - 10
    stripe_x = 0
    stripe_width = width
    
    c.setFillColorRGB(33/255, 150/255, 243/255)
    c.setStrokeColorRGB(33/255, 150/255, 243/255)
    c.rect(stripe_x, stripe_y, stripe_width, stripe_height, fill=1, stroke=0)
    
    c.setFillColorRGB(0, 0, 0)
    c.setStrokeColorRGB(0, 0, 0)
    
    # Заголовок
    c.setFont("Arial", 26)
    c.drawString(text_x, text_y, "Транспортное")
    text_y -= 25
    c.drawString(text_x, text_y, "Агентство")
    
    # Электронный билет
    electronic_x = text_x + 275
    electronic_y = photo_y + photo_height - 40
    c.setFont("Arial", 10)
    c.drawString(electronic_x, electronic_y, "ЭЛЕКТРОННЫЙ БИЛЕТ")
    electronic_y -= 20
    c.drawString(electronic_x, electronic_y, "(МАРШРУТ/КВИТАНЦИЯ)")
    
    c.setFont("Arial", 12)
    y = photo_y - 25
    
    # Голубой фон
    bg_x = 20
    bg_width = width - 40
    c.setFillColorRGB(0.87, 0.92, 1.0)
    c.setStrokeColorRGB(0.87, 0.92, 1.0)
    c.rect(bg_x, 528, bg_width, 182, fill=1, stroke=0)
    
    c.setFillColorRGB(0, 0, 0)
    c.setStrokeColorRGB(0, 0, 0)
    c.setFont("Arial", 12)
    
    y -= 30
    c.drawString(100, y, f"Билет №{booking[0]}")
    c.drawString(400, y, f"Номер рейса: {booking[1]}")
    
    y -= 30
    c.drawString(245, y, f"Компания: {booking[2]}")
    
    y -= 30
    # Вывод городов с кодами
    c.drawString(205, y, f"{booking[3]} ({booking[4]}) -> {booking[5]} ({booking[6]})")
    
    y -= 30
    c.drawString(245, y, f"Дата: {booking[7]}")
    
    y -= 30
    c.drawString(100, y, f"Вылет: {booking[8]}")
    c.drawString(235, y, f"Длительность: {booking[10]}")
    c.drawString(400, y, f"Прилет: {booking[9]}")
    
    y -= 30
    c.drawString(245, y, f"Цена: {booking[11]} руб.")
    
    # Красный фон с текстом
    red_bg_x = 20
    red_bg_y = 528 - 120
    red_bg_width = width - 40
    red_bg_height = 105
    
    c.setFillAlpha(0.54)
    c.setStrokeAlpha(0.54)
    c.setFillColorRGB(1.0, 0.2, 0.2)
    c.setStrokeColorRGB(1.0, 0.2, 0.2)
    c.rect(red_bg_x, red_bg_y, red_bg_width, red_bg_height, fill=1, stroke=0)
    
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
    
    # Нижний колонтитул
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