from service.common import *
import time

search_bp = Blueprint('search', __name__)

def escape_like_pattern(pattern):
    """Экранирует спецсимволы для безопасного использования в LIKE"""
    if pattern is None:
        return pattern
    # Порядок важен: сначала \, потом %, потом _
    return pattern.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')

def get_cities():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT city FROM directions ORDER BY city")
    cities = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return cities

def get_companies():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM companies ORDER BY name")
    companies = cur.fetchall()
    cur.close()
    conn.close()
    return companies

def search_routes(departure_city, arrival_city, departure_date, transport_type, company_id, route_number):
    conn = get_db_connection()
    cur = conn.cursor()
    
    print(f"Параметры поиска: departure_city={departure_city}, arrival_city={arrival_city}, departure_date={departure_date}, transport_type={transport_type}, company_id={company_id}, route_number={route_number}")
    
    current_datetime = datetime.now()
    current_date = current_datetime.date()
    current_time = current_datetime.time()
    
    query = """SELECT r.number, c.name, d1.city, d2.city, 
           r.data, r.departure_time, r.arrival_time, 
           r.travel_time, r.price 
           FROM routes r
           JOIN companies c ON r.company_id = c.id
           JOIN directions d1 ON r.departure_id = d1.id
           JOIN directions d2 ON r.arrival_id = d2.id
           WHERE 1=1"""
    
    params = []
    
    if departure_date:
        query += " AND r.data = %s"
        params.append(departure_date)
        if departure_date == str(current_date):
            query += " AND r.departure_time >= %s"
            params.append(current_time)
    else:
        query += " AND (r.data > %s OR (r.data = %s AND r.departure_time >= %s))"
        params.extend([current_date, current_date, current_time])
    
    if route_number:
        query += " AND r.number ILIKE %s"
        # ✅ Безопасное экранирование
        safe_route = '%' + escape_like_pattern(route_number) + '%'
        params.append(safe_route)
    
    if departure_city:
        query += " AND d1.city ILIKE %s"
        # ✅ Безопасное экранирование
        safe_departure = '%' + escape_like_pattern(departure_city) + '%'
        params.append(safe_departure)
    
    if arrival_city:
        query += " AND d2.city ILIKE %s"
        # ✅ Безопасное экранирование
        safe_arrival = '%' + escape_like_pattern(arrival_city) + '%'
        params.append(safe_arrival)
    
    if transport_type and transport_type != 'any':
        query += " AND c.type = %s"
        params.append(transport_type)
    
    if company_id and company_id != 'any':
        query += " AND r.company_id = %s"
        params.append(int(company_id))
    
    query += " ORDER BY r.data, r.departure_time"
    
    print(f"SQL: {query}")
    print(f"Params: {params}")
    
    cur.execute(query, params)
    routes = cur.fetchall()
    
    print(f"Найдено рейсов: {len(routes)}")
    
    cur.close()
    conn.close()
    return routes

@search_bp.route('/', methods=['GET', 'POST'])
def travel():
    companies = get_companies()
    cities = get_cities()
    today = datetime.now().date()
    default_date = today.strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        departure_city = request.form.get('departure_city', '').strip()
        arrival_city = request.form.get('arrival_city', '').strip()
        departure_date = request.form.get('departure_date', '')
        transport_type = request.form.get('transport_type', 'any')
        company_id = request.form.get('company_id', 'any')
        route_number = request.form.get('route_number', '').strip()
        
        routes = search_routes(departure_city, arrival_city, departure_date, 
                                transport_type, company_id, route_number)
        
        return render_template('travel.html', routes=routes, 
                             departure_city=departure_city,
                             arrival_city=arrival_city, 
                             departure_date=departure_date,
                             transport_type=transport_type, 
                             company_id=company_id,
                             route_number=route_number, 
                             companies=companies, 
                             cities=cities,
                             default_date=default_date)
    
    return render_template('travel.html', routes=None, companies=companies, 
                          cities=cities, default_date=default_date)

@search_bp.route('/book_ticket/<route_number>', methods=['POST'])
def book_ticket_route(route_number):
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({'success': False, 'error': 'Требуется авторизация'})
    
    user_id = session.get('user_id')
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Ищем рейс в таблице routes
        cur.execute("SELECT id FROM routes WHERE number = %s", (route_number,))
        route = cur.fetchone()
        
        if route:
            route_id = route[0]
            # Создаем бронирование в таблице ticket_booking
            cur.execute("""INSERT INTO ticket_booking (user_id, route_id, status) 
                          VALUES (%s, %s, 'забронирован') RETURNING id""", 
                       (user_id, route_id))
            booking_id = cur.fetchone()[0]
            conn.commit()
            return jsonify({'success': True, 'booking_id': booking_id})
        else:
            return jsonify({'success': False, 'error': 'Рейс не найден'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cur.close()
        conn.close()