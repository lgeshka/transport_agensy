from service.common import *

connect_to_partner_bp = Blueprint('connect_to_partner', __name__)

@connect_to_partner_bp.route('/connect_to_partner')
def connect_to_partner():
    return render_template('connect_to_partner.html')