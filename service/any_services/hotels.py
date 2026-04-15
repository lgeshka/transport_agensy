from service.common import *

hotels_bp = Blueprint('hotels', __name__)

@hotels_bp.route('/bronirovanie')
def hotels():
    return render_template('bronirovanie.html')