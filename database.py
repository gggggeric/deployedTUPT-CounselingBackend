from flask_pymongo import PyMongo
from bson import ObjectId
from models import User, Appointment

mongo = PyMongo()

def init_app(app):
    mongo.init_app(app)

def test_connection():
    try:
        mongo.db.command('ping')
        return True
    except Exception:
        return False

def insert_user(user):
    try:
        print(f"🔍 Attempting to insert user: {user.username}")
        user_dict = user.to_dict()
        print(f"📝 User data to insert: {user_dict}")
        
        # Check if database connection is working
        try:
            mongo.db.command('ping')
            print("✅ Database connection is active")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return None
        
        # Check if users collection exists
        collections = mongo.db.list_collection_names()
        print(f"📁 Available collections: {collections}")
        
        result = mongo.db.users.insert_one(user_dict)
        print(f"✅ User inserted successfully with ID: {result.inserted_id}")
        return str(result.inserted_id)
    except Exception as e:
        print(f"❌ Error inserting user: {e}")
        import traceback
        print(f"🔍 Stack trace: {traceback.format_exc()}")
        return None

def find_user_by_username(username):
    try:
        user_data = mongo.db.users.find_one({'username': username})
        if user_data:
            return User.from_dict(user_data)
        return None
    except Exception as e:
        print(f"Error finding user by username: {e}")
        return None

def find_user_by_id_number(id_number):
    try:
        user_data = mongo.db.users.find_one({'id_number': id_number})
        if user_data:
            return User.from_dict(user_data)
        return None
    except Exception as e:
        print(f"Error finding user by ID number: {e}")
        return None

def find_user_by_id(user_id):
    try:
        print(f"🔍 Searching for user with ID: {user_id}")
        
        # Try both ObjectId and string lookup
        if ObjectId.is_valid(user_id):
            user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
            if user_data:
                print(f"✅ User found using ObjectId: {user_data.get('username')}")
                return User.from_dict(user_data)
        
        # If not found with ObjectId, try string lookup
        user_data = mongo.db.users.find_one({'_id': user_id})
        if user_data:
            print(f"✅ User found using string ID: {user_data.get('username')}")
            return User.from_dict(user_data)
        else:
            print(f"❌ No user found with ID: {user_id}")
            return None
    except Exception as e:
        print(f"❌ Error finding user by ID: {e}")
        return None

def insert_appointment(appointment):
    try:
        appointment_dict = appointment.to_dict()
        print(f"📝 Inserting appointment data: {appointment_dict}")
        print(f"🔍 User ID type in appointment: {type(appointment_dict['user_id'])}")
        
        result = mongo.db.appointments.insert_one(appointment_dict)
        print(f"✅ Appointment inserted with ID: {result.inserted_id}")
        return str(result.inserted_id)
    except Exception as e:
        print(f"❌ Error inserting appointment: {e}")
        import traceback
        print(f"🔍 Stack trace: {traceback.format_exc()}")
        return None

def find_appointments_by_user_id(user_id):
    try:
        print(f"🔍 Searching for appointments for user: {user_id}")
        print(f"🔍 User ID type: {type(user_id)}")
        
        # Convert user_id to ObjectId if it's a valid ObjectId string
        if ObjectId.is_valid(user_id):
            query_user_id = ObjectId(user_id)
        else:
            query_user_id = user_id
            
        appointments_data = mongo.db.appointments.find({'user_id': query_user_id}).sort('date', -1)
        appointments = []
        for appointment_data in appointments_data:
            appointments.append(Appointment.from_dict(appointment_data))
        print(f"✅ Found {len(appointments)} appointments for user {user_id}")
        return appointments
    except Exception as e:
        print(f"❌ Error finding appointments by user ID: {e}")
        return []

def update_appointment_status(appointment_id, new_status):
    """Update the status of an appointment with validation"""
    try:
        print(f"🔍 Updating appointment {appointment_id} to status: {new_status}")
        print(f"🔍 ID type: {type(appointment_id)}")
        
        # Validate status first
        if not Appointment.is_valid_status(new_status):
            print(f"❌ Invalid status: {new_status}")
            return False, "Invalid status value"
        
        # Build query based on ID type
        if ObjectId.is_valid(appointment_id):
            query = {'_id': ObjectId(appointment_id)}
            print(f"🔍 Using ObjectId query")
        else:
            query = {'_id': appointment_id}
            print(f"🔍 Using string ID query")
        
        # First check if appointment exists
        appointment_data = mongo.db.appointments.find_one(query)
        if not appointment_data:
            print(f"❌ Appointment not found: {appointment_id}")
            # Debug: list all appointments
            all_appointments = list(mongo.db.appointments.find({}, {'_id': 1, 'status': 1}))
            print(f"🔍 All available appointments: {[(str(apt['_id']), apt.get('status')) for apt in all_appointments]}")
            return False, "Appointment not found"
            
        print(f"✅ Found appointment: {appointment_data}")
        current_db_status = appointment_data.get('status', 'Pending')
        print(f"🔍 Current status in DB: {current_db_status}")
        
        # For admin updates, if current_status is 'Pending', only allow 'Approved' or 'Rejected'
        if current_db_status == 'Pending' and not Appointment.is_admin_updatable_status(new_status):
            print(f"❌ Cannot update from Pending to {new_status}. Only 'Approved' or 'Rejected' allowed.")
            return False, "Can only approve or reject pending appointments"
        
        # Update the appointment
        result = mongo.db.appointments.update_one(
            query,
            {'$set': {'status': new_status}}
        )
        
        print(f"✅ Update result - matched: {result.matched_count}, modified: {result.modified_count}")
        
        if result.modified_count > 0:
            print(f"✅ Successfully updated appointment {appointment_id} from {current_db_status} to {new_status}")
            return True, "Status updated successfully"
        elif result.matched_count > 0:
            print(f"⚠️ Status already set to {new_status}")
            return True, "Status was already set to the requested value"
        else:
            print(f"⚠️ No changes made to appointment {appointment_id}")
            print(f"🔍 Query used: {query}")
            print(f"🔍 New status: {new_status}")
            return False, "No changes made - appointment not found or status unchanged"
            
    except Exception as e:
        print(f"❌ Error updating appointment status: {e}")
        import traceback
        print(f"🔍 Stack trace: {traceback.format_exc()}")
        return False, f"Error updating appointment: {str(e)}"

def get_all_appointments():
    """Get all appointments (for admin/counselor view)"""
    try:
        appointments = list(mongo.db.appointments.find().sort('created_at', -1))
        print(f"🔍 Found {len(appointments)} total appointments in database")
        for apt in appointments:
            print(f"   - {apt['_id']}: {apt.get('user_id', 'N/A')} - {apt.get('date', 'N/A')} - {apt.get('status', 'N/A')}")
        return [Appointment.from_dict(appointment) for appointment in appointments]
    except Exception as e:
        print(f"Error getting all appointments: {e}")
        return []

def find_appointment_by_id(appointment_id):
    """Find a specific appointment by ID - handles both ObjectId and string IDs"""
    try:
        print(f"🔍 Searching for appointment with ID: {appointment_id}")
        print(f"🔍 ID type: {type(appointment_id)}")
        
        # Try to find by ObjectId first if it's a valid ObjectId
        if ObjectId.is_valid(appointment_id):
            print(f"🔍 Trying to find by ObjectId: {appointment_id}")
            appointment_data = mongo.db.appointments.find_one({'_id': ObjectId(appointment_id)})
            if appointment_data:
                print(f"✅ Appointment found using ObjectId: {appointment_data}")
                return Appointment.from_dict(appointment_data), None
        
        # If not found or not valid ObjectId, try as string ID
        print(f"🔍 Trying to find by string ID: {appointment_id}")
        appointment_data = mongo.db.appointments.find_one({'_id': appointment_id})
        
        if appointment_data:
            print(f"✅ Appointment found using string ID: {appointment_data}")
            return Appointment.from_dict(appointment_data), None
        else:
            print(f"❌ No appointment found with ID: {appointment_id}")
            # Debug: list all appointments to see what's available
            all_appointments = list(mongo.db.appointments.find({}, {'_id': 1, 'user_id': 1, 'date': 1}))
            print(f"🔍 All available appointments: {[(str(apt['_id']), apt.get('user_id'), apt.get('date')) for apt in all_appointments]}")
            return None, "Appointment not found"
            
    except Exception as e:
        print(f"❌ Error finding appointment by ID: {e}")
        import traceback
        print(f"🔍 Stack trace: {traceback.format_exc()}")
        return None, f"Error finding appointment: {str(e)}"

def update_appointment_attended(appointment_id, attended_status):
    """
    Update the attended status of an appointment - handles both ObjectId and string IDs
    """
    try:
        print(f"🔍 Updating appointment {appointment_id} attended status to: {attended_status}")
        print(f"🔍 ID type: {type(appointment_id)}")
        
        # Build query based on ID type
        if ObjectId.is_valid(appointment_id):
            query = {'_id': ObjectId(appointment_id)}
            print(f"🔍 Using ObjectId query for attendance update")
        else:
            query = {'_id': appointment_id}
            print(f"🔍 Using string ID query for attendance update")
        
        result = mongo.db.appointments.update_one(
            query,
            {'$set': {'attended': attended_status}}
        )
        
        print(f"✅ Update result - matched: {result.matched_count}, modified: {result.modified_count}")
        
        if result.modified_count > 0:
            print(f"✅ Successfully updated appointment {appointment_id} attended status to {attended_status}")
            return True, "Attendance status updated successfully"
        elif result.matched_count > 0:
            print(f"⚠️ Attendance status already set to {attended_status}")
            return True, "Attendance status was already set"
        else:
            print(f"⚠️ No changes made to appointment {appointment_id}")
            # Debug what's in the database
            all_appointments = list(mongo.db.appointments.find({}, {'_id': 1}))
            print(f"🔍 Available appointment IDs: {[str(apt['_id']) for apt in all_appointments]}")
            return False, "Appointment not found or no changes made"
            
    except Exception as e:
        print(f"❌ Error updating attendance status: {e}")
        import traceback
        print(f"🔍 Stack trace: {traceback.format_exc()}")
        return False, str(e)

def get_appointments_with_user_details():
    """Get all appointments with user information using aggregation - FIXED VERSION"""
    try:
        print("🔍 Starting get_appointments_with_user_details...")
        
        # First, let's debug what's in the collections
        users_count = mongo.db.users.count_documents({})
        appointments_count = mongo.db.appointments.count_documents({})
        print(f"🔍 Users count: {users_count}, Appointments count: {appointments_count}")
        
        # Get all appointments first to see user_id types
        all_appointments = list(mongo.db.appointments.find({}, {'user_id': 1}))
        user_id_types = {}
        for apt in all_appointments:
            user_id = apt.get('user_id')
            user_id_types[str(type(user_id))] = user_id_types.get(str(type(user_id)), 0) + 1
        print(f"🔍 User ID types in appointments: {user_id_types}")
        
        # Get all users to see _id types
        all_users = list(mongo.db.users.find({}, {'_id': 1, 'username': 1}))
        user_id_types = {}
        for user in all_users:
            user_id = user.get('_id')
            user_id_types[str(type(user_id))] = user_id_types.get(str(type(user_id)), 0) + 1
        print(f"🔍 User _id types in users collection: {user_id_types}")
        print(f"🔍 Sample users: {[(str(user['_id']), user.get('username')) for user in all_users[:3]]}")
        
        # Enhanced pipeline that handles both ObjectId and string user_ids
        pipeline = [
            {
                '$lookup': {
                    'from': 'users',
                    'let': { 'appointment_user_id': '$user_id' },
                    'pipeline': [
                        {
                            '$match': {
                                '$expr': {
                                    '$or': [
                                        { '$eq': ['$_id', '$$appointment_user_id'] },
                                        { '$eq': [{ '$toString': '$_id' }, '$$appointment_user_id'] },
                                        { '$eq': ['$_id', { '$toObjectId': '$$appointment_user_id' }] }
                                    ]
                                }
                            }
                        }
                    ],
                    'as': 'user_info'
                }
            },
            {
                '$unwind': {
                    'path': '$user_info',
                    'preserveNullAndEmptyArrays': True
                }
            },
            {
                '$sort': {'date': 1, 'preferred_time': 1}
            }
        ]
        
        appointments_cursor = mongo.db.appointments.aggregate(pipeline)
        appointments = list(appointments_cursor)
        
        print(f"🔍 Found {len(appointments)} appointments with user details")
        
        # Convert to serializable format
        serialized_appointments = []
        for apt in appointments:
            # Handle both ObjectId and string _id
            appointment_id = str(apt['_id']) if isinstance(apt['_id'], ObjectId) else apt['_id']
            
            # Get user info with fallbacks
            user_info = {}
            if apt.get('user_info'):
                user_info = {
                    'username': apt['user_info'].get('username', 'Unknown'),
                    'id_number': apt['user_info'].get('id_number', 'N/A')
                }
            else:
                # If no user info found, try to find the user directly
                user_id = apt.get('user_id')
                if user_id:
                    user = find_user_by_id(user_id)
                    if user:
                        user_info = {
                            'username': user.username,
                            'id_number': user.id_number or 'N/A'
                        }
                    else:
                        user_info = {
                            'username': 'Unknown',
                            'id_number': 'N/A'
                        }
                else:
                    user_info = {
                        'username': 'Unknown',
                        'id_number': 'N/A'
                    }
            
            serialized_apt = {
                '_id': appointment_id,
                'user_id': str(apt['user_id']) if isinstance(apt['user_id'], ObjectId) else apt['user_id'],
                'date': apt['date'],
                'preferred_time': apt['preferred_time'],
                'concern_type': apt['concern_type'],
                'status': apt.get('status', 'Pending'),
                'attended': apt.get('attended', False),
                'created_at': apt.get('created_at', ''),
                'user_info': user_info
            }
            serialized_appointments.append(serialized_apt)
        
        # Debug: Check how many appointments have user info
        with_user_info = len([apt for apt in serialized_appointments if apt['user_info'].get('username') != 'Unknown'])
        print(f"🔍 Appointments with user info: {with_user_info}/{len(serialized_appointments)}")
        
        return serialized_appointments
        
    except Exception as e:
        print(f"❌ Error getting appointments with user details: {e}")
        import traceback
        print(f"🔍 Stack trace: {traceback.format_exc()}")
        return []

def debug_appointments():
    """Debug function to see all appointments and their structure"""
    try:
        print("🔍 DEBUG: All appointments in database:")
        appointments = list(mongo.db.appointments.find())
        print(f"Total appointments: {len(appointments)}")
        
        for i, apt in enumerate(appointments):
            print(f"Appointment {i+1}:")
            print(f"  _id: {apt['_id']} (type: {type(apt['_id'])})")
            print(f"  user_id: {apt.get('user_id', 'N/A')} (type: {type(apt.get('user_id'))})")
            print(f"  date: {apt.get('date', 'N/A')}")
            print(f"  status: {apt.get('status', 'N/A')}")
            print(f"  concern_type: {apt.get('concern_type', 'N/A')}")
            print(f"  attended: {apt.get('attended', 'N/A')}")
            print("  ---")
            
        return appointments
    except Exception as e:
        print(f"❌ Error debugging appointments: {e}")
        return []