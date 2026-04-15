from service.common import *

popular_bp = Blueprint('popular', __name__)

@popular_bp.route('/popular')
def popular():
    return render_template('popular.html')