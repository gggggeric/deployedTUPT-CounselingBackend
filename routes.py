from flask import jsonify, request
from database import find_user_by_username, find_user_by_id_number, insert_user, insert_appointment, find_appointments_by_user_id, update_appointment_status, get_all_appointments, find_user_by_id, find_appointment_by_id, get_appointments_with_user_details
from models import User, Appointment
from bson import ObjectId

def init_routes(app):
    @app.route('/')
    def index():
        return jsonify({
            'message': 'TUPT Counseling Scheduler API',
            'status': 'active'
        })
  
    @app.route('/ping', methods=['GET'])
    def ping():
        return jsonify({
            "status": "ok",
            "message": "✅ Server is alive!",
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }), 200

    @app.route('/register', methods=['POST'])
    def register():
        try:
            print("🚀 REGISTER ENDPOINT CALLED")
            data = request.get_json()
            print(f"📦 Received registration data: {data}")
            
            # Validate required fields
            if not data:
                print("❌ No JSON data provided")
                return jsonify({
                    'message': 'Invalid request data',
                    'error': 'No JSON data provided'
                }), 400
            
            required_fields = ['username', 'password', 'id_number', 'birthdate']
            missing_fields = [field for field in required_fields if not data.get(field)]
            
            if missing_fields:
                print(f"❌ Missing fields: {missing_fields}")
                return jsonify({
                    'message': 'Missing required fields',
                    'error': f'Missing fields: {", ".join(missing_fields)}',
                    'missing_fields': missing_fields
                }), 400
            
            print(f"🔍 Checking if username exists: {data['username']}")
            # Check if user already exists
            if find_user_by_username(data['username']):
                print(f"❌ Username already exists: {data['username']}")
                return jsonify({
                    'message': 'Registration failed',
                    'error': 'Username already exists'
                }), 409
            
            print(f"🔍 Checking if ID number exists: {data['id_number']}")
            # Check if ID number already exists
            if find_user_by_id_number(data['id_number']):
                print(f"❌ ID number already exists: {data['id_number']}")
                return jsonify({
                    'message': 'Registration failed', 
                    'error': 'ID number already registered'
                }), 409
            
            # Validate password length
            if len(data['password']) < 6:
                print(f"❌ Password too short: {len(data['password'])} characters")
                return jsonify({
                    'message': 'Registration failed',
                    'error': 'Password must be at least 6 characters long'
                }), 400
            
            print("✅ All validations passed, creating user...")
            # Create new user with default role 'user'
            password_hash = User.set_password(data['password'])
            user = User(
                username=data['username'],
                password_hash=password_hash,
                id_number=data['id_number'],
                birthdate=data['birthdate'],
                role=data.get('role', 'user')  # Default role is 'user'
            )
            
            print(f"👤 User object created: {user.username}")
            
            # Save user to database
            result = insert_user(user)
            print(f"💾 Database insertion result: {result}")
            
            if result:
                print(f"✅ User registered successfully: {user.username}")
                return jsonify({
                    'message': 'Registration successful! Please login.',
                    'user_id': str(user._id),
                    'user': {
                        'username': user.username,
                        'id_number': user.id_number,
                        'birthdate': user.birthdate,
                        'role': user.role
                    }
                }), 201
            else:
                print("❌ Failed to insert user into database")
                return jsonify({
                    'message': 'Registration failed',
                    'error': 'Failed to create user in database'
                }), 500
            
        except Exception as e:
            print(f"💥 Registration error: {str(e)}")
            import traceback
            print(f"🔍 Stack trace: {traceback.format_exc()}")
            return jsonify({
                'message': 'Registration error',
                'error': str(e)
            }), 500

    @app.route('/login', methods=['POST'])
    def login():
        try:
            data = request.get_json()
            
            if not data or not data.get('username') or not data.get('password'):
                return jsonify({
                    'message': 'Login failed',
                    'error': 'Username and password are required'
                }), 400
            
            user = find_user_by_username(data['username'])
            if user is None or not user.check_password(data['password']):
                return jsonify({
                    'message': 'Login failed',
                    'error': 'Invalid username or password'
                }), 401
            
            print(f"✅ User {user.username} logged in successfully. Role: {user.role}")
            
            return jsonify({
                'message': 'Login successful',
                'user': {
                    'username': user.username,
                    'id_number': user.id_number,
                    'birthdate': user.birthdate,
                    'user_id': str(user._id),
                    'role': user.role
                }
            }), 200
            
        except Exception as e:
            print(f"❌ Login error: {e}")
            return jsonify({
                'message': 'Login error',
                'error': str(e)
            }), 500

    @app.route('/appointments', methods=['POST'])
    def create_appointment():
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data:
                return jsonify({
                    'message': 'Invalid request data',
                    'error': 'No JSON data provided'
                }), 400
            
            required_fields = ['user_id', 'date', 'preferred_time', 'concern_type']
            missing_fields = [field for field in required_fields if not data.get(field)]
            
            if missing_fields:
                return jsonify({
                    'message': 'Missing required fields',
                    'error': f'Missing fields: {", ".join(missing_fields)}',
                    'missing_fields': missing_fields
                }), 400
            
            # Create new appointment with default status 'Pending' (not approved)
            appointment = Appointment(
                user_id=data['user_id'],
                date=data['date'],
                preferred_time=data['preferred_time'],
                concern_type=data['concern_type'],
                status=data.get('status', 'Pending')  # Default status is 'Pending'
            )
            
            # Save appointment to database
            result = insert_appointment(appointment)
            
            if result:
                print(f"✅ Appointment created for user {data['user_id']} on {data['date']} at {data['preferred_time']}")
                return jsonify({
                    'message': 'Appointment scheduled successfully! Waiting for approval.',
                    'appointment_id': str(appointment._id),
                    'appointment': appointment.to_dict()
                }), 201
            else:
                return jsonify({
                    'message': 'Appointment scheduling failed',
                    'error': 'Failed to create appointment in database'
                }), 500
            
        except Exception as e:
            print(f"❌ Appointment scheduling error: {e}")
            return jsonify({
                'message': 'Appointment scheduling error',
                'error': str(e)
            }), 500

    @app.route('/appointments/<user_id>', methods=['GET'])
    def get_user_appointments(user_id):
        try:
            appointments = find_appointments_by_user_id(user_id)
            
            print(f"✅ Retrieved {len(appointments)} appointments for user {user_id}")
            
            return jsonify({
                'message': 'Appointments retrieved successfully',
                'appointments': [appointment.to_dict() for appointment in appointments]
            }), 200
            
        except Exception as e:
            print(f"❌ Error retrieving appointments: {e}")
            return jsonify({
                'message': 'Error retrieving appointments',
                'error': str(e)
            }), 500

    @app.route('/appointments/<appointment_id>/status', methods=['PUT'])
    def update_appointment_status_route(appointment_id):
        try:
            data = request.get_json()
            
            if not data or not data.get('status'):
                return jsonify({
                    'message': 'Status is required'
                }), 400
            
            # Validate status
            valid_statuses = ['Pending', 'Approved', 'Rejected', 'Cancelled', 'Completed']
            if data['status'] not in valid_statuses:
                return jsonify({
                    'message': f'Status must be one of: {", ".join(valid_statuses)}'
                }), 400
            
            # SIMPLE: Just update the status directly
            success, message = update_appointment_status(appointment_id, data['status'])
            
            if success:
                return jsonify({
                    'message': f'Appointment status updated to {data["status"]}',
                    'status': data['status']
                }), 200
            else:
                return jsonify({
                    'message': 'Failed to update appointment status',
                    'error': message
                }), 400
                
        except Exception as e:
            return jsonify({
                'message': 'Error updating appointment status',
                'error': str(e)
            }), 500
        
    # Enhanced endpoint to get all appointments with user details
    @app.route('/all-appointments', methods=['GET'])
    def get_all_appointments_route():
        try:
            appointments = get_appointments_with_user_details()
            
            return jsonify({
                'message': 'All appointments retrieved successfully',
                'appointments': appointments
            }), 200
            
        except Exception as e:
            print(f"❌ Error retrieving all appointments: {e}")
            return jsonify({
                'message': 'Error retrieving appointments',
                'error': str(e)
            }), 500

    # New endpoint to get user profile with role information
    @app.route('/user/<user_id>', methods=['GET'])
    def get_user_profile(user_id):
        try:
            user = find_user_by_id(user_id)
            if not user:
                return jsonify({
                    'message': 'User not found',
                    'error': 'Invalid user ID'
                }), 404
            
            return jsonify({
                'message': 'User profile retrieved successfully',
                'user': {
                    'username': user.username,
                    'id_number': user.id_number,
                    'birthdate': user.birthdate,
                    'user_id': str(user._id),
                    'role': user.role,
                    'created_at': user.created_at.isoformat() if hasattr(user.created_at, 'isoformat') else user.created_at
                }
            }), 200
            
        except Exception as e:
            print(f"❌ Error retrieving user profile: {e}")
            return jsonify({
                'message': 'Error retrieving user profile',
                'error': str(e)
            }), 500

    @app.route('/dashboard')
    def dashboard():
        return jsonify({
            'message': 'Dashboard endpoint',
            'note': 'Authentication handled by frontend localStorage'
        })

    @app.route('/user/profile')
    def user_profile():
        return jsonify({
            'message': 'User profile endpoint',
            'note': 'Authentication handled by frontend localStorage'
        })

    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': 'API is running'
        })

    # Test endpoint to check if appointments collection exists
    @app.route('/test-appointments')
    def test_appointments():
        try:
            from database import mongo
            # Try to access appointments collection
            appointments_count = mongo.db.appointments.count_documents({})
            return jsonify({
                'message': 'Appointments collection is accessible',
                'appointments_count': appointments_count
            })
        except Exception as e:
            return jsonify({
                'message': 'Error accessing appointments collection',
                'error': str(e)
            }), 500

    # Debug endpoint to check appointment data
    @app.route('/debug/appointments/<appointment_id>')
    def debug_appointment(appointment_id):
        try:
            result = find_appointment_by_id(appointment_id)
            if isinstance(result, tuple):
                appointment, error_msg = result
            else:
                appointment, error_msg = result, None
                
            if appointment:
                return jsonify({
                    'found': True,
                    'appointment': appointment.to_dict(),
                    'raw_id': appointment_id,
                    'is_valid_objectid': ObjectId.is_valid(appointment_id)
                }), 200
            else:
                return jsonify({
                    'found': False,
                    'error': error_msg,
                    'raw_id': appointment_id,
                    'is_valid_objectid': ObjectId.is_valid(appointment_id)
                }), 404
        except Exception as e:
            return jsonify({
                'error': str(e),
                'raw_id': appointment_id
            }), 500

    # Debug endpoint to list all appointments
    @app.route('/debug/all-appointments-raw')
    def debug_all_appointments_raw():
        try:
            from database import mongo
            appointments = list(mongo.db.appointments.find())
            
            serialized_appointments = []
            for apt in appointments:
                serialized_apt = {
                    '_id': str(apt['_id']),
                    'user_id': apt.get('user_id', 'N/A'),
                    'date': apt.get('date', 'N/A'),
                    'status': apt.get('status', 'N/A'),
                    'concern_type': apt.get('concern_type', 'N/A'),
                    'preferred_time': apt.get('preferred_time', 'N/A'),
                    'created_at': apt.get('created_at', 'N/A')
                }
                serialized_appointments.append(serialized_apt)
            
            return jsonify({
                'appointments': serialized_appointments,
                'count': len(serialized_appointments)
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Debug endpoint to check user details
    @app.route('/debug/users')
    def debug_users():
        try:
            from database import mongo
            users = list(mongo.db.users.find())
            
            serialized_users = []
            for user in users:
                serialized_user = {
                    '_id': str(user['_id']),
                    'username': user.get('username', 'N/A'),
                    'id_number': user.get('id_number', 'N/A'),
                    'role': user.get('role', 'N/A')
                }
                serialized_users.append(serialized_user)
            
            return jsonify({
                'users': serialized_users,
                'count': len(serialized_users)
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500