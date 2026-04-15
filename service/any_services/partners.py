from service.common import *
import os
from flask import current_app

partners_bp = Blueprint('partners', __name__)

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
    file_path = os.path.join(current_app.root_path, 'static', 'txt', 'partners_urls.txt')
    
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
        except Exception as e:
            print(f"Ошибка при чтении файла: {e}")
    
    return urls

@partners_bp.route('/partners')
def partners():
    companies = get_all_companies()
    partner_urls = load_partner_urls()
    return render_template('partners.html', companies=companies, partner_urls=partner_urls)