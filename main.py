from flask import Flask
from config import config
from service.common import Blueprint

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Импорт Blueprint
from service.routes.search import search_bp
from service.account.profile import account_bp
from service.account.payment import payment_bp
from service.account.download import download_bp
from service.any_services.popular import popular_bp
from service.any_services.partners import partners_bp
from service.any_services.about import about_bp
from service.reports.support import support_bp
from service.any_services.cities import cities_bp
from service.any_services.hotels import hotels_bp
from service.any_services.ruls import ruls_bp
from service.any_services.vacancy import vacancy_bp
from service.any_services.politica_conf import politica_conf_bp
from service.any_services.vip import vip_bp
from service.any_services.cargo import cargo_bp
from service.any_services.connect_to_partner import connect_to_partner_bp
from service.any_services.advertisement import advertisement_bp
from service.any_services.howtobuy import howtobuy_bp
from service.any_services.faq import faq_bp
from service.admin.panel import admin_bp
from service.any_services.whereisplane import whereisplane_bp

# Регистрация Blueprint
app.register_blueprint(search_bp)
app.register_blueprint(account_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(download_bp)
app.register_blueprint(popular_bp)
app.register_blueprint(partners_bp)
app.register_blueprint(about_bp)
app.register_blueprint(support_bp)
app.register_blueprint(cities_bp)
app.register_blueprint(hotels_bp)
app.register_blueprint(ruls_bp)
app.register_blueprint(vacancy_bp)
app.register_blueprint(politica_conf_bp)
app.register_blueprint(vip_bp)
app.register_blueprint(cargo_bp)
app.register_blueprint(connect_to_partner_bp)
app.register_blueprint(advertisement_bp)
app.register_blueprint(howtobuy_bp)
app.register_blueprint(faq_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(whereisplane_bp)

if __name__ == '__main__':
    app.run(debug=True)