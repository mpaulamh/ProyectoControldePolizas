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

if __name__ == "__main__":
    app.run(
        debug=False,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
    )