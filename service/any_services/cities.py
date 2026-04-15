# service/any_services/cities.py
from service.common import *

cities_bp = Blueprint('cities', __name__)

def escape_like_pattern(pattern):
    """Экранирует спецсимволы для безопасного использования в LIKE"""
    if pattern is None:
        return pattern
    # Порядок важен: сначала \, потом %, потом _
    return pattern.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')

@cities_bp.route('/cities')
def cities():
    search_query = request.args.get('search', '').strip()
    conn = get_db_connection()
    cur = conn.cursor()
    
    if search_query:
        # ✅ Безопасное экранирование спецсимволов
        safe_search = '%' + escape_like_pattern(search_query) + '%'
        
        cur.execute("""
            SELECT city, country 
            FROM directions 
            WHERE city ILIKE %s OR country ILIKE %s
            ORDER BY country, city
        """, (safe_search, safe_search))
    else:
        cur.execute("""
            SELECT city, country 
            FROM directions 
            ORDER BY country, city
        """)
    
    cities = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('cities.html', cities=cities, search_query=search_query)