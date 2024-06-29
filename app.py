from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from flask_session import Session
from datetime import datetime

app = Flask(__name__, static_url_path='/static', static_folder='static')

# Configure the Flask session
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SESSION_TYPE'] = 'filesystem'

# Initialize the session
Session(app)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['your_database_name']  # Replace 'your_database_name' with your actual database name
users_collection = db['users']  # Collection to store user data
user_details_collection = db['user_details']  # Collection to store user details

# User authentication logic
def authenticate(username, password):
    user = users_collection.find_one({"$or": [{"username": username}, {"email": username}], "password": password})
    return user is not None

@app.route('/')
def home():
    if 'username' in session:
        return render_template('index.html')
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if authenticate(username, password):
            session['username'] = username  # Save user in session
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid credentials. Please try again.')

    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)  # Clear the username from session
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Insert user data into MongoDB
        users_collection.insert_one({
            'username': username,
            'email': email,
            'password': password  # Note: Storing passwords in plain text is not secure, use hashing in production
        })

        return redirect(url_for('login'))  # Redirect to login page after signup

    return render_template('signup.html')


@app.route('/booking')
def booking():
    if 'username' in session:
        return render_template('booking.html')
    else:
        return redirect(url_for('login'))

@app.route('/submit_booking', methods=['POST'])
def submit_booking():
    if request.method == 'POST':
        Name = request.form.get('Name', '')
        Email = request.form.get('Email', '')
        PhoneNumber = request.form.get('PhoneNumber', '')
        age = int(request.form.get('age', 0))  # Default to 0 if 'age' is missing or not a number
        DOB = request.form.get('Date_Of_Birth', '')
        Address = request.form.get('Address', '')
        patient = request.form.get('patient', '')
        
        # Validate required fields
        if not Name or not Email or not PhoneNumber or not age or not DOB or not Address or not patient:
            return "All fields are required."
        
        user_data = {
            'Name': Name,
            'Email': Email,
            'PhoneNumber': PhoneNumber,
            'Age': age,
            'Date_Of_Birth': DOB,
            'Address': Address,
            'Patient': patient,
            
        }

        # Store user details in MongoDB
        user_details_collection.insert_one(user_data)

        return redirect(url_for('display_booking'))

    return "Method not allowed."


@app.route('/display_booking')
def display_booking():
    # Example: Fetch booked seats from MongoDB and pass to template
    booked_seats = []  # Fetch from MongoDB or initialize as needed

    return render_template('display.html', booked_seats=booked_seats)

@app.route('/bus_details', methods=['GET', 'POST'])
def bus_details():
    if request.method == 'POST':
        user_details = session.get('user_details', {})

        from_point = request.form.get('From_point', '')
        to_point = request.form.get('To_point', '')
        totalSeats = request.form.get('totalSeats', 1)
        travelDate = request.form.get('travelDate', '')
        facility = request.form.get('facility', '')

        # Update user details with travel information
        user_details.update({
            'From_point': from_point,
            'To_point': to_point,
            'totalSeats': totalSeats,
            'travelDate': travelDate,
            'facility': facility
        })

        # Insert or update the user details in MongoDB
        user_details_collection.update_one(
            {'Email': user_details['Email']},
            {'$set': user_details},
            upsert=True
        )

        return redirect(url_for('show_bus_details'))

    return render_template('bus_details.html')

@app.route('/show_bus_details')
def show_bus_details():
    booked_seats = []  # This should be fetched from your database if you have seat booking logic
    return render_template('bus_details.html', booked_seats=booked_seats)


@app.route('/final_ticket_details')
def final_ticket_details():
    booking_date = request.args.get('booking_date')
    booking_time = request.args.get('booking_time')
    from_point = request.args.get('from_point')
    to_point = request.args.get('to_point')
    total_seats = request.args.get('total_seats')
    total_price = request.args.get('total_price')

    return render_template(
        'final_ticket_details.html',
        booking_date=booking_date,
        booking_time=booking_time,
        from_point=from_point,
        to_point=to_point,
        total_seats=total_seats,
        total_price=total_price
    )
booked_seats = [5, 12, 15, 25, 30]


def index():
    return render_template('bus_booking_details.html', booked_seats=booked_seats)

@app.route('/make_payment', methods=['POST'])
def make_payment():
    if request.method == 'POST':
        # Get booking details from the form
        booked_seats = request.form.getlist('seats')  # Get selected seats
        total_seats = len(booked_seats)
        facility = request.form.get('facility')
        travel_date = request.form.get('travelDate')

        # Validate if all necessary fields are present
        if not all([total_seats, facility, travel_date]):
            return "Invalid booking details provided."

        # Calculate the total price using the amount function
        total_price_per_seat = amount(1, 2, facility)  # Example points (replace with actual logic)
        if total_price_per_seat is None:
            return "Invalid booking details provided."

        total_price = total_price_per_seat * total_seats

        # Redirect to final ticket details page with parameters
        return redirect(url_for('final_details',
                                booked_seats=','.join(booked_seats),
                                total_seats=total_seats,
                                facility=facility,
                                travel_date=travel_date,
                                total_price=total_price))

    else:
        return "Method not allowed."

@app.route('/final_ticket_details')
def final_details():
    # Retrieve parameters from URL query string
    booked_seats = request.args.get('booked_seats').split(',')
    total_seats = request.args.get('total_seats')
    facility = request.args.get('facility')
    travel_date = request.args.get('travel_date')
    total_price = request.args.get('total_price')

    # Render final_ticket_details.html with parameters
    return render_template('final_ticket_details.html',
                           booked_seats=booked_seats,
                           total_seats=total_seats,
                           facility=facility,
                           travel_date=travel_date,
                           total_price=total_price)

def amount(from_point, to_point, facility):
    base_fare = 500
    to_point_fares = [250, 200, 150, 100]
    facility_fares = [250, 150, 500, 350]

    try:
        from_point = int(from_point)
        to_point = int(to_point)
        facility = int(facility)

        if 1 <= from_point <= 4 and 1 <= to_point <= 4 and 1 <= facility <= 4:
            return base_fare + to_point_fares[to_point - 1] + facility_fares[facility - 1]
        else:
            return None
    except (ValueError, TypeError, IndexError):
        return None


@app.route('/contact', methods=['POST'])
def contact():
    if 'username' in session:
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        # Process the contact form data here
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
