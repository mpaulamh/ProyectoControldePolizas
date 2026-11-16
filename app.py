import os
from flask import Flask
from controllers.polizas_controller import polizas_bp

app = Flask(
    __name__,
    template_folder="views",
    static_folder="public/static",
    static_url_path="/static",
)

app.register_blueprint(polizas_bp)

app.secret_key = os.environ.get("SECRET_KEY", "cambiar_por_clave_segura_en_produccion")


@app.template_filter("moneda")
def formato_moneda(valor):
    """Formatea un número como moneda con separadores de miles."""
    if valor is None:
        return "No registrada"
    return f"{valor:,.0f}"


if __name__ == "__main__":
    app.run(
        debug=False,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
    )