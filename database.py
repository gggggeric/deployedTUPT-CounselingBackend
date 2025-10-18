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
        # Validate ObjectId
        if not ObjectId.is_valid(user_id):
            print(f"❌ Invalid user ID format: {user_id}")
            return None
            
        user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if user_data:
            print(f"✅ User found in database: {user_data.get('username')}")
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
        
        result = mongo.db.appointments.insert_one(appointment_dict)
        print(f"✅ Appointment inserted with ID: {result.inserted_id}")
        return result.inserted_id
    except Exception as e:
        print(f"❌ Error inserting appointment: {e}")
        import traceback
        print(f"🔍 Stack trace: {traceback.format_exc()}")
        return None

def find_appointments_by_user_id(user_id):
    try:
        print(f"🔍 Searching for appointments for user: {user_id}")
        appointments_data = mongo.db.appointments.find({'user_id': user_id}).sort('date', -1)
        appointments = []
        for appointment_data in appointments_data:
            appointments.append(Appointment.from_dict(appointment_data))
        print(f"✅ Found {len(appointments)} appointments for user {user_id}")
        return appointments
    except Exception as e:
        print(f"❌ Error finding appointments by user ID: {e}")
        return []

def update_appointment_status(appointment_id, new_status, current_status=None):
    """Update the status of an appointment with validation"""
    try:
        print(f"🔍 Updating appointment {appointment_id} from {current_status} to status: {new_status}")
        
        # Validate status first
        if not Appointment.is_valid_status(new_status):
            print(f"❌ Invalid status: {new_status}")
            return False, "Invalid status value"
        
        # First check if appointment exists
        appointment_data = mongo.db.appointments.find_one({'_id': ObjectId(appointment_id)})
        if not appointment_data:
            print(f"❌ Appointment not found: {appointment_id}")
            return False, "Appointment not found"
            
        print(f"✅ Found appointment: {appointment_data}")
        
        # For admin updates, if current_status is provided and it's 'Pending', 
        # only allow 'Approved' or 'Rejected'
        if current_status == 'Pending' and not Appointment.is_admin_updatable_status(new_status):
            print(f"❌ Cannot update from Pending to {new_status}. Only 'Approved' or 'Rejected' allowed.")
            return False, "Can only approve or reject pending appointments"
        
        result = mongo.db.appointments.update_one(
            {'_id': ObjectId(appointment_id)},
            {'$set': {'status': new_status}}
        )
        
        print(f"✅ Update result - matched: {result.matched_count}, modified: {result.modified_count}")
        
        if result.modified_count > 0:
            print(f"✅ Successfully updated appointment {appointment_id} to {new_status}")
            return True, "Status updated successfully"
        else:
            print(f"⚠️ No changes made to appointment {appointment_id}")
            return False, "No changes made"
            
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
    """Find a specific appointment by ID"""
    try:
        print(f"🔍 Searching for appointment with ID: {appointment_id}")
        
        # SIMPLE FIX: Just search by string ID since that's how it's stored
        appointment_data = mongo.db.appointments.find_one({'_id': appointment_id})
        
        if appointment_data:
            print(f"✅ Appointment found: {appointment_data}")
            return Appointment.from_dict(appointment_data), None
        else:
            print(f"❌ No appointment found with ID: {appointment_id}")
            return None, "Appointment not found"
            
    except Exception as e:
        print(f"❌ Error finding appointment by ID: {e}")
        return None, f"Error finding appointment: {str(e)}"

def update_appointment_status(appointment_id, new_status, current_status=None):
    """Update the status of an appointment"""
    try:
        print(f"🔍 Updating appointment {appointment_id} to status: {new_status}")
        
        # Validate status
        if not Appointment.is_valid_status(new_status):
            return False, "Invalid status value"
        
        # SIMPLE FIX: Update by string ID
        result = mongo.db.appointments.update_one(
            {'_id': appointment_id},  # Just use the string ID directly
            {'$set': {'status': new_status}}
        )
        
        if result.modified_count > 0:
            print(f"✅ Successfully updated appointment {appointment_id} to {new_status}")
            return True, "Status updated successfully"
        else:
            print(f"⚠️ No changes made to appointment {appointment_id}")
            return False, "No changes made"
            
    except Exception as e:
        print(f"❌ Error updating appointment status: {e}")
        return False, f"Error updating appointment: {str(e)}"
    

    
def get_appointments_with_user_details():
    """Get all appointments with user information using aggregation"""
    try:
        pipeline = [
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'user_id',
                    'foreignField': '_id',
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
            serialized_apt = {
                '_id': str(apt['_id']),
                'user_id': apt['user_id'],
                'date': apt['date'],
                'preferred_time': apt['preferred_time'],
                'concern_type': apt['concern_type'],
                'status': apt.get('status', 'Pending'),
                'created_at': apt.get('created_at', ''),
                'user_info': {
                    'username': apt.get('user_info', {}).get('username', 'Unknown'),
                    'id_number': apt.get('user_info', {}).get('id_number', 'Unknown')
                } if apt.get('user_info') else {}
            }
            serialized_appointments.append(serialized_apt)
        
        return serialized_appointments
        
    except Exception as e:
        print(f"❌ Error getting appointments with user details: {e}")
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
            print(f"  user_id: {apt.get('user_id', 'N/A')}")
            print(f"  date: {apt.get('date', 'N/A')}")
            print(f"  status: {apt.get('status', 'N/A')}")
            print(f"  concern_type: {apt.get('concern_type', 'N/A')}")
            print("  ---")
            
        return appointments
    except Exception as e:
        print(f"❌ Error debugging appointments: {e}")
        return []