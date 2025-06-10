# api/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import routes
from routes.global_agent import global_routes
from routes.rag_agent import rag_routes
from routes.web_search_agent import web_search_routes

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


# Register blueprints
app.register_blueprint(global_routes, url_prefix='/api/global')
app.register_blueprint(rag_routes, url_prefix='/api/rag')
app.register_blueprint(web_search_routes, url_prefix='/api/websearch')

if __name__ == '__main__':
    app.run(port=5328, debug=True)