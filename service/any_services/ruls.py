from service.common import *

ruls_bp = Blueprint('ruls', __name__)

@ruls_bp.route('/ruls')
def ruls():
    return render_template('ruls.html')