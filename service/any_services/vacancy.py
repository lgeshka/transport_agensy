from service.common import *

vacancy_bp = Blueprint('vacancy', __name__)

@vacancy_bp.route('/vacancy')
def vacancy():
    return render_template('vacancy.html')