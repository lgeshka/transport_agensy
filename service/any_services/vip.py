from service.common import *

vip_bp = Blueprint('vip', __name__)

@vip_bp.route('/vip')
def vip():
    return render_template('vip.html')