from service.common import *

about_bp = Blueprint('about', __name__)

@about_bp.route('/about')
def about():
    return render_template('about.html')

@about_bp.route('/api/cities_with_coords')
def get_cities_with_coords():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT city, country, code, latitude, longitude FROM directions WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
    cities = cur.fetchall()
    cur.close()
    conn.close()
    
    cities_list = []
    for city in cities:
        cities_list.append({
            'city': city[0],
            'country': city[1] if city[1] else '',
            'code': city[2] if city[2] else '',
            'lat': float(city[3]),
            'lng': float(city[4])
        })
    
    return jsonify({'success': True, 'cities': cities_list})