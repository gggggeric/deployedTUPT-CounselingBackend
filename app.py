from flask import Flask
from flask_cors import CORS
from database import init_app
from routes import init_routes
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Enable CORS for React frontend
CORS(app)

# MongoDB configuration from environment variables
MONGO_USERNAME = os.environ.get('MONGO_USERNAME')
MONGO_PASSWORD = os.environ.get('MONGO_PASSWORD')
MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME')

# Validate that all required environment variables are set
required_env_vars = ['MONGO_USERNAME', 'MONGO_PASSWORD', 'MONGO_DB_NAME']
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]

if missing_vars:
    print(f"💥 CRITICAL: Missing required environment variables: {', '.join(missing_vars)}")
    print("💡 Please set these environment variables before running the application")
    exit(1)

app.config['MONGO_URI'] = f'mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@cluster1.hcz8tdb.mongodb.net/{MONGO_DB_NAME}?retryWrites=true&w=majority&appName=Cluster1'
app.config['MONGO_DB_NAME'] = MONGO_DB_NAME

# Initialize extensions
try:
    init_app(app)
    print("🎉 MongoDB initialization completed successfully!")
except Exception as e:
    print(f"💥 CRITICAL: Failed to initialize MongoDB: {e}")
    print("💡 Please check your credentials and connection")
    exit(1)

# Initialize routes (no Flask-Login needed)
init_routes(app)

@app.route('/test-db')
def test_db():
    """Route to test database connection"""
    from database import test_connection
    if test_connection():
        return jsonify({
            'message': '✅ Database connection is active!',
            'status': 'success'
        })
    else:
        return jsonify({
            'message': '❌ Database connection failed!',
            'status': 'error'
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Flask API server...")
    print(f"📊 Database: {MONGO_DB_NAME}")
    print(f"👤 MongoDB User: {MONGO_USERNAME}")
    print(f"🌐 Server will run on: http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)