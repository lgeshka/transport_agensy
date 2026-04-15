from service.common import *

advertisement_bp = Blueprint('advertisement', __name__)

@advertisement_bp.route('/advertisement')
def advertisement():
    return render_template('advertisement.html')