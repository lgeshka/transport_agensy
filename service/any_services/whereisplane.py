from service.common import *

whereisplane_bp = Blueprint('whereisplane', __name__)

@whereisplane_bp.route('/status')
def whereisplane():
    return render_template('status.html')