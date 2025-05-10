#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import sys
import os
from datetime import datetime, timezone
import dateutil.parser
import babel
from flask import (
    Flask, render_template, request, flash, redirect,
    url_for, abort, session, jsonify
)
from flask_moment import Moment
from flask_login import LoginManager
from sqlalchemy import or_, desc, and_, create_engine, text
from werkzeug.security import generate_password_hash, check_password_hash
from forms import SearchForm, BookingForm, UserRegistrationForm, PassengerForm, LoginForm
from models import setup_db, db, User, Passenger, TrainInfo, TrainStatus, ReservedTicket, CanceledTicket
from check_db.check_db import requires_db
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from azure.storage.blob import BlobServiceClient  # already exists
from dotenv import load_dotenv


load_dotenv()
#----------------------------------------------------------------------------#
# Azure Blob Storage Configuration
#----------------------------------------------------------------------------#
AZURE_STORAGE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=mahamstorage;AccountKey=RlOVEUnUdxiZsPsCvwTCzFCUjZs81wrXmt1i7VwLz49euyRYNgEPRee7/AKlp/LrPyo+pU7K8Ci/+AStlMTZLg==;EndpointSuffix=core.windows.net"
AZURE_CONTAINER_NAME = "train-docs"

# ----------------------
# App Config - Azure PostgreSQL
# ----------------------

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(32)
moment = Moment(app)

# Azure PostgreSQL connection - hardcoded
# In your app.py configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://maham:Datascience12.@maham.postgres.database.azure.com:5432/railway?sslmode=require')
# SQLAlchemy engine options
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_size': 5,
    'max_overflow': 2
}

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize DB
db.init_app(app)
with app.app_context():
    try:
        db.session.execute(text('SELECT 1'))
        print("Database connection successful!")
    except Exception as e:
        print(f"Database connection failed: {str(e)}")
        raise

# Ensure tables are created at startup
with app.app_context():
    try:
        print("Attempting to connect to Azure PostgreSQL...")
        db.create_all()
        print("✔️ Database connection successful")
        print("✔️ Tables created/verified")
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#
def format_datetime(value, format='medium'):
    if isinstance(value, str):
        value = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(value, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Helper Functions
#----------------------------------------------------------------------------#
def calculate_available_seats(train_number, travel_date):
    status = TrainStatus.query.filter_by(
        train_number=train_number,
        travel_date=travel_date
    ).first()
    
    if not status:
        return None
    
    return {
        'economy': status.total_economy_seats - status.booked_economy_seats,
        'economy_birth': status.total_birth_seats - status.booked_birth_seats,
        'ac_business': status.total_business_seats - status.booked_business_seats,
        'ac_standard': status.total_standard_seats - status.booked_standard_seats,
        'ac_sleeper': status.total_sleeper_seats - status.booked_sleeper_seats
    }

def generate_pdf_ticket(booking_details):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(100, 750, "Railway Booking Ticket")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(100, 720, f"Passenger: {booking_details.passenger.passenger_name}")
    pdf.drawString(100, 700, f"Train: {booking_details.train.train_name} ({booking_details.train.train_number})")
    pdf.drawString(100, 680, f"Date: {booking_details.travel_date.strftime('%Y-%m-%d')}")
    pdf.drawString(100, 660, f"Class: {booking_details.ticket_category.upper()}")

    pdf.save()
    buffer.seek(0)
    return buffer

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#
# In your index route:
# Add this in app.py before your routes
@app.context_processor
def inject_now():
    return {'now': datetime.now(timezone.utc)}

@app.route('/')
def index():
    form = SearchForm()
    popular_trains = TrainInfo.query.order_by(TrainInfo.train_name).limit(4).all()
    return render_template(
        'pages/home.html',
        form=form,
        popular_trains=popular_trains,
        now=datetime.now(timezone.utc)  # Timezone-aware UTC time
    )

# Search Trains
@app.route('/search', methods=['GET', 'POST'])
def search_trains():
    form = SearchForm()
    if form.validate_on_submit():
        departure = form.departure_city.data
        arrival = form.arrival_city.data
        travel_date = form.travel_date.data
        
        # Find trains matching the route
        trains = TrainInfo.query.filter_by(
            departure_city=departure,
            arrival_city=arrival
        ).all()
        
        # Get status for each train on the travel date
        results = []
        for train in trains:
            status = TrainStatus.query.filter_by(
                train_number=train.train_number,
                travel_date=travel_date
            ).first()
            
            if status:
                available_seats = calculate_available_seats(train.train_number, travel_date)
                results.append({
                    'train': train,
                    'status': status,
                    'available_seats': available_seats
                })
        
        return render_template('pages/search_results.html', results=results, form=form)
    
    return render_template('forms/search.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = UserRegistrationForm()
    if form.validate_on_submit():
        try:
            # Remove password hashing
            user = User(
                user_name=form.username.data,
                user_password=form.password.data  # Store plain text
            )
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Username may already exist.')
    
    return render_template('forms/register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(user_name=form.username.data).first()
        
        # Direct password comparison
        if user and user.user_password == form.password.data:
            session['user_id'] = user.user_id
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('forms/login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out successfully.')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get popular routes (top 5 trains by route)
    popular_routes = db.session.query(
        TrainInfo.departure_city,
        TrainInfo.arrival_city
    ).distinct().limit(5).all()
    
    # For each route, get the next available train
    route_trains = []
    for route in popular_routes:
        train = TrainInfo.query.filter_by(
            departure_city=route[0],
            arrival_city=route[1]
        ).order_by(TrainInfo.train_name).first()
        
        if train:
            # Get next available travel date
            status = TrainStatus.query.filter_by(
                train_number=train.train_number
            ).filter(TrainStatus.travel_date >= datetime.now().date()
            ).order_by(TrainStatus.travel_date).first()
            
            if status:
                route_trains.append({
                    'train': train,
                    'status': status,
                    'available_seats': calculate_available_seats(train.train_number, status.travel_date)
                })
    
    # Get user's active bookings
    active_bookings = ReservedTicket.query.filter(
    ReservedTicket.user_id == user_id,
    ReservedTicket.ticket_status == 'confirmed'
    ).join(TrainInfo, ReservedTicket.train).join(Passenger).all()
    
    return render_template('pages/dashboard.html', 
                         route_trains=route_trains,
                         popular_routes=popular_routes,
                         active_bookings=active_bookings)
    


# Add this new route to app.py
@app.route('/filter_trains', methods=['POST'])
def filter_trains():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    departure = request.form.get('departure_city')
    arrival = request.form.get('arrival_city')
    
    if not departure or not arrival:
        flash('Please select both departure and arrival cities')
        return redirect(url_for('dashboard'))
    
    # Get trains for the selected route
    trains = TrainInfo.query.filter_by(
        departure_city=departure,
        arrival_city=arrival
    ).order_by(TrainInfo.train_name).limit(4).all()
    
    # Prepare results with status and available seats
    results = []
    for train in trains:
        status = TrainStatus.query.filter_by(
            train_number=train.train_number
        ).filter(TrainStatus.travel_date >= datetime.now().date()
        ).order_by(TrainStatus.travel_date).first()
        
        if status:
            results.append({
                'train': train,
                'status': status,
                'available_seats': calculate_available_seats(train.train_number, status.travel_date)
            })
    
    # Get popular routes for the dropdown
    popular_routes = db.session.query(
        TrainInfo.departure_city,
        TrainInfo.arrival_city
    ).distinct().limit(5).all()
    
    # Get user's active bookings
    active_bookings = ReservedTicket.query.filter(
        ReservedTicket.user_id == session['user_id'],
        ReservedTicket.ticket_status == 'confirmed'
    ).join(TrainInfo).join(Passenger).all()
    
    return render_template('pages/dashboard.html',
                         route_trains=results,
                         selected_route={'departure': departure, 'arrival': arrival},
                         popular_routes=popular_routes,
                         active_bookings=active_bookings)

@app.route('/book/<train_number>/<travel_date>', methods=['GET', 'POST'])
@requires_db(app.config.get('SQLALCHEMY_DATABASE_URI'))
def book_train(train_number, travel_date):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    form = BookingForm()
    user_id = session['user_id']
    
    train = TrainInfo.query.get(train_number)
    status = TrainStatus.query.filter_by(
        train_number=train_number,
        travel_date=travel_date
    ).first()
    
    if not train or not status:
        flash('Invalid train or date selection')
        return redirect(url_for('search_trains'))
    
    # Get available seats
    available_seats = calculate_available_seats(train_number, travel_date)
    
    # Populate passengers for dropdown
    form.passenger_id.choices = [
        (p.passenger_id, p.passenger_name) 
        for p in Passenger.query.filter_by(user_id=user_id).all()
    ]
    
    if form.validate_on_submit():
        try:
            # Create booking
            booking = ReservedTicket(
                user_id=user_id,
                passenger_id=form.passenger_id.data,
                train_number=train_number,
                ticket_category=form.ticket_category.data,
                travel_date=travel_date,
                ticket_status='confirmed'
            )
            
            # Update seat availability
            category_map = {
                'economy': 'booked_economy_seats',
                'economy_birth': 'booked_birth_seats',
                'ac_business': 'booked_business_seats',
                'ac_standard': 'booked_standard_seats',
                'ac_sleeper': 'booked_sleeper_seats'
            }
            
            seat_field = category_map.get(form.ticket_category.data)
            if seat_field:
                setattr(status, seat_field, getattr(status, seat_field) + 1)
            
            db.session.add(booking)
            db.session.commit()

            # Generate PDF and upload to Azure
            try:
                pdf_buffer = generate_pdf_ticket(booking)
                blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
                container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)
                blob_name = f"tickets/{booking.ticket_id}.pdf"
                blob_client = container_client.get_blob_client(blob_name)
                blob_client.upload_blob(pdf_buffer.getvalue(), overwrite=True)
                flash('Ticket generated and uploaded to Azure successfully!')
            except Exception as e:
                app.logger.error(f"PDF generation or upload failed: {str(e)}")
                flash('Booking confirmed, but ticket generation failed. Contact support.')

            flash('Booking successful!')
            return redirect(url_for('dashboard'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Booking failed. Error: {str(e)}')
    
    return render_template(
        'forms/booking.html',
        form=form,
        train=train,
        travel_date=travel_date,
        available_seats=available_seats,
        status=status
    )


@app.route('/cancel/<int:ticket_id>')
@requires_db(app.config.get('SQLALCHEMY_DATABASE_URI'))
def cancel_booking(ticket_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    booking = ReservedTicket.query.get(ticket_id)
    
    if not booking or booking.user_id != user_id:
        flash('Invalid booking request')
        return redirect(url_for('dashboard'))
    
    try:
        # Get train status for seat updates
        status = TrainStatus.query.filter_by(
            train_number=booking.train_number,
            travel_date=booking.travel_date
        ).first()
        
        if not status:
            flash('Train status not found')
            return redirect(url_for('dashboard'))

        # First create the canceled ticket record
        canceled = CanceledTicket(
            ticket_id=booking.ticket_id,
            booking_date=booking.booking_date,
            user_id=booking.user_id,
            passenger_id=booking.passenger_id,
            train_number=booking.train_number,
            ticket_category=booking.ticket_category,
            travel_date=booking.travel_date
        )
        db.session.add(canceled)
        
        # Update seat availability
        category_map = {
            'economy': 'booked_economy_seats',
            'economy_birth': 'booked_birth_seats',
            'ac_business': 'booked_business_seats',
            'ac_standard': 'booked_standard_seats',
            'ac_sleeper': 'booked_sleeper_seats'
        }
        
        seat_field = category_map.get(booking.ticket_category)
        if seat_field:
            current_count = getattr(status, seat_field, 0)
            setattr(status, seat_field, max(current_count - 1, 0))

        # Instead of deleting, mark as canceled
        booking.ticket_status = 'canceled'
        
        db.session.commit()
        flash('Booking canceled successfully')
    except Exception as e:
        db.session.rollback()
        flash(f'Cancellation failed: {str(e)}')
    
    return redirect(url_for('dashboard'))

# Add Passenger
@app.route('/passengers/add', methods=['GET', 'POST'])
@requires_db(app.config.get('SQLALCHEMY_DATABASE_URI'))
def add_passenger():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    form = PassengerForm()
    train_number = request.args.get('train_number')
    travel_date = request.args.get('travel_date')
    
    if form.validate_on_submit():
        try:
            # Create passenger first
            passenger = Passenger(
                user_id=session['user_id'],
                passenger_name=form.name.data,
                passenger_age=form.age.data,
                passenger_gender=form.gender.data,
                passenger_cnic=form.cnic.data,
                passenger_phone=form.phone.data,
                passenger_address=form.address.data,
                passenger_email=form.email.data
            )
            db.session.add(passenger)
            db.session.commit()

            # Handle file uploads to Azure Blob Storage
            uploaded_files = request.files.getlist('files')
            if uploaded_files:
                # Initialize Azure Blob Service Client
                blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
                container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)

                for file in uploaded_files:
                    if file.filename != '':
                        # Create a blob name using passenger ID and original filename
                        blob_name = f"passenger_{passenger.passenger_id}/{file.filename}"
                        blob_client = container_client.get_blob_client(blob_name)
                        
                        # Upload the file
                        blob_client.upload_blob(file.stream)
                        flash(f'File {file.filename} uploaded successfully')

            flash('Passenger added successfully! Please complete the booking.')
            return redirect(url_for('book_train', 
                                 train_number=train_number, 
                                 travel_date=travel_date))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to add passenger. Error: {str(e)}')
    
    return render_template('forms/add_passenger.html', 
                         form=form, 
                         train_number=train_number, 
                         travel_date=travel_date)


# Admin Views
@app.route('/admin/trains')
@requires_db(app.config.get('SQLALCHEMY_DATABASE_URI'))
def admin_trains():
    trains = TrainInfo.query.all()
    return render_template('pages/admin_trains.html', trains=trains)

@app.route('/admin/train_status')
@requires_db(app.config.get('SQLALCHEMY_DATABASE_URI'))
def admin_train_status():
    status_list = TrainStatus.query.join(TrainInfo).all()
    return render_template('pages/admin_train_status.html', status_list=status_list)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
