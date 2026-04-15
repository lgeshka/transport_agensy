from service.common import *

faq_bp = Blueprint('faq', __name__)

@faq_bp.route('/faq')
def faq():
    return render_template('faq.html')