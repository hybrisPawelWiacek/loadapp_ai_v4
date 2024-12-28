from flask import Flask, jsonify, make_response
from flask_restful import Api, Resource
from flask_cors import CORS
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

app = Flask(__name__)
# Configure CORS to allow all origins in development
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept"],
        "expose_headers": ["Content-Type", "Authorization"]
    }
})
api = Api(app)

class HelloWorld(Resource):
    def get(self):
        logger.info("hello_world.accessed", status="success")
        response = make_response(jsonify({"message": "Hello, World!"}))
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    def options(self):
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        return response

api.add_resource(HelloWorld, '/api/hello')

@app.after_request
def after_request(response):
    logger.info("request.completed", 
                status_code=response.status_code,
                headers=dict(response.headers))
    return response

if __name__ == '__main__':
    logger.info("server.starting", port=5000)
    # Allow connections from any host
    app.run(debug=True, host='0.0.0.0', port=5000)
