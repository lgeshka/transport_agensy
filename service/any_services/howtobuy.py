from service.common import *

howtobuy_bp = Blueprint('howtobuy', __name__)

@howtobuy_bp.route('/howtobuy')
def howtobuy():
    return render_template('howtobuy.html')