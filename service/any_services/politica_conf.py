from service.common import *

politica_conf_bp = Blueprint('politica_conf', __name__)

@politica_conf_bp.route('/politica_conf')
def politica_conf():
    return render_template('politica_conf.html')