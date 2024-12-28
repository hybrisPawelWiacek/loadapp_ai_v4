"""Main application module."""
import os
from flask import Flask, jsonify, make_response
from flask_restful import Api, Resource
from flask_cors import CORS
import structlog
from dotenv import load_dotenv

from .config import Config
from .infrastructure.container import Container
from .infrastructure.database import init_db

# Load environment variables
load_dotenv()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

def create_app(config: Config = None) -> Flask:
    """Create and configure the Flask application.
    
    Args:
        config: Application configuration. If None, loads from environment.
        
    Returns:
        Flask application instance
    """
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    if config is None:
        config = Config.from_env()
    
    # Configure logging
    logger.info("app.configuring", 
                environment=config.ENV,
                log_level=config.LOGGING.LEVEL)
    
    # Initialize container with configuration
    container = Container(config.to_dict())
    
    # Store container in app context
    app.container = container
    
    # Configure CORS
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "Accept"],
            "expose_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Initialize API
    api = Api(app)
    
    # Initialize database
    init_db(config.DATABASE.URL)
    
    # Register routes
    register_routes(api, container)
    
    # Register error handlers
    register_error_handlers(app)

    @app.after_request
    def after_request(response):
        """Log after each request."""
        logger.info("request.completed", 
                    status_code=response.status_code,
                    headers=dict(response.headers))
        return response
    
    return app

def register_routes(api: Api, container: Container):
    """Register API routes with their handlers.
    
    Args:
        api: Flask-RESTful API instance
        container: Dependency injection container
    """
    # Example route for testing
    class HelloWorld(Resource):
        def get(self):
            logger.info("hello_world.accessed", status="success")
            response = make_response(jsonify({"message": "Hello, World!"}))
            return response

        def options(self):
            response = make_response()
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
            return response

    api.add_resource(HelloWorld, '/api/hello')
    
    # TODO: Add other API routes here
    # Example:
    # from .api.routes.transport_routes import TransportResource
    # api.add_resource(
    #     TransportResource, 
    #     '/api/transports',
    #     resource_class_kwargs={'transport_service': container.transport_service()}
    # )

def register_error_handlers(app: Flask):
    """Register error handlers for the application.
    
    Args:
        app: Flask application instance
    """
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error("internal_server_error", error=str(error))
        return jsonify({"error": "Internal server error"}), 500

def main():
    """Main entry point for the application."""
    config = Config.from_env()
    app = create_app(config)
    
    logger.info("server.starting", 
                port=config.SERVER.PORT,
                host=config.SERVER.HOST,
                debug=config.SERVER.DEBUG)
    
    app.run(
        debug=config.SERVER.DEBUG,
        host=config.SERVER.HOST,
        port=config.SERVER.PORT
    )

if __name__ == '__main__':
    main()
