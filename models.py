from flask_login import UserMixin
from bson import ObjectId
import bcrypt
from datetime import datetime

class User(UserMixin):
    def __init__(self, username, password_hash, id_number=None, birthdate=None, role="user", _id=None, created_at=None):
        self.username = username
        self.password_hash = password_hash
        self.id_number = id_number
        self.birthdate = birthdate
        self.role = role  # 'user' or 'admin'
        self._id = _id or ObjectId()
        self.created_at = created_at or datetime.utcnow()

    def get_id(self):
        return str(self._id)

    @staticmethod
    def set_password(password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def to_dict(self):
        return {
            'username': self.username,
            'password_hash': self.password_hash,
            'id_number': self.id_number,
            'birthdate': self.birthdate,
            'role': self.role,
            '_id': self._id,  # Keep as ObjectId for database consistency
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }

    @classmethod
    def from_dict(cls, data):
        # Handle _id conversion
        _id = data.get('_id')
        if _id and not isinstance(_id, ObjectId):
            try:
                _id = ObjectId(_id)
            except:
                _id = _id  # Keep as string if conversion fails
        
        # Handle created_at conversion
        created_at = data.get('created_at')
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                created_at = datetime.utcnow()
        
        return cls(
            username=data['username'],
            password_hash=data['password_hash'],
            id_number=data.get('id_number'),
            birthdate=data.get('birthdate'),
            role=data.get('role', 'user'),
            _id=_id,
            created_at=created_at
        )


class Appointment:
    def __init__(self, user_id, date, preferred_time, concern_type, status="Pending", attended=False, _id=None, created_at=None):
        # Convert user_id to ObjectId if it's a valid ObjectId string, otherwise keep as string
        if user_id and ObjectId.is_valid(user_id):
            self.user_id = ObjectId(user_id)
        else:
            self.user_id = user_id
            
        self.date = date
        self.preferred_time = preferred_time
        self.concern_type = concern_type
        self.status = status  # 'Pending', 'Approved', 'Rejected', 'Cancelled', 'Completed'
        self.attended = attended  # New field to track if user attended
        self._id = _id or ObjectId()
        self.created_at = created_at or datetime.utcnow()

    @staticmethod
    def is_valid_status(status):
        """Validate if status is allowed"""
        valid_statuses = ['Pending', 'Approved', 'Rejected', 'Cancelled', 'Completed']
        return status in valid_statuses

    @staticmethod
    def is_admin_updatable_status(status):
        """Validate if status can be set by admin (only Approved or Rejected for pending appointments)"""
        return status in ['Approved', 'Rejected']
    
    def to_dict(self):
        # Use the actual created_at datetime to generate the formatted string
        current_created_at = self.created_at
        if isinstance(current_created_at, str):
            try:
                current_created_at = datetime.fromisoformat(current_created_at.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                current_created_at = datetime.utcnow()
        
        formatted_created_at = current_created_at.strftime('%B %d, %Y at %I:%M %p')
        
        return {
            'user_id': self.user_id,
            'date': self.date,
            'preferred_time': self.preferred_time,
            'concern_type': self.concern_type,
            'status': self.status,
            'attended': self.attended,
            '_id': self._id,
            'created_at': current_created_at.isoformat() if isinstance(current_created_at, datetime) else current_created_at,
            'formatted_created_at': formatted_created_at
        }

    @classmethod
    def from_dict(cls, data):
        # Handle _id conversion
        _id = data.get('_id')
        if _id and not isinstance(_id, ObjectId):
            try:
                _id = ObjectId(_id)
            except:
                _id = _id  # Keep as string if conversion fails
        
        # Handle user_id conversion - ensure consistency
        user_id = data.get('user_id')
        if user_id and ObjectId.is_valid(user_id) and not isinstance(user_id, ObjectId):
            user_id = ObjectId(user_id)
        
        # Handle created_at conversion from string to datetime if needed
        created_at = data.get('created_at')
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                created_at = datetime.utcnow()
        
        return cls(
            user_id=user_id,
            date=data['date'],
            preferred_time=data['preferred_time'],
            concern_type=data['concern_type'],
            status=data.get('status', 'Pending'),
            attended=data.get('attended', False),
            _id=_id,
            created_at=created_at
        )