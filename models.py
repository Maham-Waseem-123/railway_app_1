from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, ForeignKey, TIMESTAMP, Text
from sqlalchemy.orm import relationship

db = SQLAlchemy()

def setup_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()

class User(db.Model):
    __tablename__ = 'user_registration'

    user_id = Column(Integer, primary_key=True)
    user_name = Column(String(100), nullable=False, unique=True)
    user_password = Column(String(255), nullable=False)
    
    passengers = relationship('Passenger', backref='user', lazy=True)
    bookings = relationship('ReservedTicket', backref='user', lazy=True)
    cancellations = relationship('CanceledTicket', backref='user', lazy=True)

    # Flask-Login required properties and methods
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True  # You can make this conditional if you add an 'active' flag to users

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.user_id)

class Passenger(db.Model):
    __tablename__ = 'passenger_info'

    passenger_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user_registration.user_id'), nullable=False)
    passenger_name = Column(String(100), nullable=False)
    passenger_age = Column(Integer)
    passenger_gender = Column(String(10))
    passenger_cnic = Column(String(15), unique=True)
    passenger_phone = Column(String(15))
    passenger_address = Column(Text)
    passenger_email = Column(String(100))
    
    bookings = relationship('ReservedTicket', backref='passenger', lazy=True)

class TrainInfo(db.Model):
    __tablename__ = 'train_info'

    train_number = Column(String(10), primary_key=True)
    train_name = Column(String(100), nullable=False)
    departure_city = Column(String(50), nullable=False)
    arrival_city = Column(String(50), nullable=False)
    economy_lare = Column(Integer)
    economy_birth_lare = Column(Integer)
    ac_business_lare = Column(Integer)
    ac_standard_lare = Column(Integer)
    ac_sleeper_lare = Column(Integer)
    
    statuses = relationship('TrainStatus', backref='train', lazy=True)
    bookings = relationship('ReservedTicket', backref='train', lazy=True)

class TrainStatus(db.Model):
    __tablename__ = 'train_status'

    status_id = Column(Integer, primary_key=True)
    train_number = Column(String(10), ForeignKey('train_info.train_number'), nullable=False)
    train_name = Column(String(100))
    travel_date = Column(Date, nullable=False)
    total_economy_seats = Column(Integer)
    total_birth_seats = Column(Integer)
    total_business_seats = Column(Integer)
    total_standard_seats = Column(Integer)
    total_sleeper_seats = Column(Integer)
    booked_economy_seats = Column(Integer, default=0)
    booked_birth_seats = Column(Integer, default=0)
    booked_business_seats = Column(Integer, default=0)
    booked_standard_seats = Column(Integer, default=0)
    booked_sleeper_seats = Column(Integer, default=0)
    
    __table_args__ = (
        db.UniqueConstraint('train_number', 'travel_date', name='unique_train_date'),
    )

class ReservedTicket(db.Model):
    __tablename__ = 'reserved_ticket'

    ticket_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_registration.user_id'), nullable=False)
    passenger_id = db.Column(db.Integer, db.ForeignKey('passenger_info.passenger_id'), nullable=False)
    train_number = db.Column(db.String(10), db.ForeignKey('train_info.train_number'), nullable=False)
    booking_date = db.Column(db.TIMESTAMP(timezone=True), default=datetime.utcnow)
    ticket_status = db.Column(db.String(20), default='confirmed')  # <-- Key change: track status here
    ticket_category = db.Column(db.String(20), nullable=False)
    travel_date = db.Column(db.Date, nullable=False)

    # Foreign key constraint for train_status
    __table_args__ = (
        db.ForeignKeyConstraint(
            ['train_number', 'travel_date'],
            ['train_status.train_number', 'train_status.travel_date']
        ),
    )

class CanceledTicket(db.Model):
    __tablename__ = 'canceled_ticket'

    ticket_id = db.Column(db.Integer, db.ForeignKey('reserved_ticket.ticket_id'), primary_key=True)
    booking_date = db.Column(db.TIMESTAMP(timezone=True))
    cancellation_date = db.Column(db.TIMESTAMP(timezone=True), default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user_registration.user_id'))
    passenger_id = db.Column(db.Integer, db.ForeignKey('passenger_info.passenger_id'))
    train_number = db.Column(db.String(10), db.ForeignKey('train_info.train_number'))
    ticket_category = db.Column(db.String(20))
    travel_date = db.Column(db.Date)

    # Keep only these relationships
    passenger = db.relationship('Passenger', backref='canceled_tickets')
    train = db.relationship('TrainInfo', backref='canceled_tickets')

    # ❌ REMOVE this line:
    # user = db.relationship('User', backref='canceled_tickets')
