from service.common import *

cargo_bp = Blueprint('cargo', __name__)

@cargo_bp.route('/cargo')
def cargo():
    return render_template('cargo.html')