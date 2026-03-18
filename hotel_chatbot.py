from flask import Flask, render_template, request, session, redirect, url_for
from datetime import datetime, timedelta
import re
import random
import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Flask home page is working"

@app.route('/reset')
def reset():
    return "Reset page is working"

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)

class AdvancedHotelChatbot:
    def __init__(self):
        self.room_prices = {'single': 100, 'double': 150, 'suite': 250}
        self.breakfast_price = 20

        self.training_responses = {
            'greeting': [
                "Hello! Welcome to Sunshine Hotel! 🌞 How can I assist you today?",
                "Hi there! Ready to book your perfect stay at Sunshine Hotel?",
                "Welcome! I'm here to help you book a room at Sunshine Hotel."
            ],
            'ask_name': [
                "May I have your name to get started?",
                "What's your name so I can personalize your booking?",
                "Could you please tell me your name?"
            ],
            'ask_email': [
                "What's your email address for the confirmation?",
                "Please provide your email so we can send booking details.",
                "May I have your email address?"
            ],
            'ask_dates': [
                "When would you like to check in? (Use YYYY-MM-DD, or say 'tomorrow')",
                "What are your preferred check-in dates?",
                "When will you be arriving?"
            ],
            'ask_checkout': [
                "When will you be checking out?",
                "What's your check-out date?",
                "How many nights will you be staying?"
            ],
            'ask_guests': [
                "How many guests will be staying?",
                "Number of guests please?",
                "How many people will be in your party?"
            ],
            'ask_room_type': [
                "What type of room would you prefer? We have single, double, and suite rooms.",
                "Please choose a room type: single ($100/night), double ($150/night), or suite ($250/night)",
                "Which room would you like? Options: single, double, suite"
            ],
            'ask_breakfast': [
                "Would you like breakfast included for an additional $20 per person per night? (yes/no)",
                "Should we include breakfast with your stay?",
                "Breakfast option: would you like it included?"
            ],
            'confirmation': [
                "Great! Let me confirm your booking details...",
                "Perfect! Here's your booking summary...",
                "Thank you! Reviewing your reservation..."
            ],
            'completion': [
                "🎉 Booking confirmed! Thank you for choosing Sunshine Hotel!",
                "✅ Reservation complete! We're excited to host you!",
                "📅 Your booking is confirmed! Welcome to Sunshine Hotel!"
            ]
        }

    def parse_date(self, text):
        text = text.strip().lower()

        if text == "today":
            return datetime.now().date()
        if text == "tomorrow":
            return (datetime.now() + timedelta(days=1)).date()
        if text == "next week":
            return (datetime.now() + timedelta(days=7)).date()

        formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]
        for fmt in formats:
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        return None

    def extract_info(self, message, current_step, booking_data):
        message_lower = message.lower().strip()

        if current_step == 'get_name':
            patterns = [
                r'name is ([a-zA-Z ]+)',
                r'i am ([a-zA-Z ]+)',
                r"i'm ([a-zA-Z ]+)",
                r'im ([a-zA-Z ]+)'
            ]
            for pattern in patterns:
                match = re.search(pattern, message_lower)
                if match:
                    return match.group(1).strip().title()
            return message.strip().title()

        elif current_step == 'get_email':
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', message)
            return email_match.group(0) if email_match else None

        elif current_step in ['get_checkin', 'get_checkout']:
            parsed = self.parse_date(message)
            return parsed.strftime('%Y-%m-%d') if parsed else None

        elif current_step == 'get_guests':
            num_match = re.search(r'\b\d+\b', message)
            if num_match:
                guests = int(num_match.group(0))
                return str(guests) if guests > 0 else None
            return None

        return message.strip()

    def calculate_price(self, booking_data):
        try:
            checkin = datetime.strptime(booking_data['checkin'], '%Y-%m-%d').date()
            checkout = datetime.strptime(booking_data['checkout'], '%Y-%m-%d').date()

            nights = (checkout - checkin).days
            if nights <= 0:
                return None

            base_price = self.room_prices.get(booking_data['room_type'], 150)
            guests = int(booking_data.get('guests', 1))
            breakfast_cost = self.breakfast_price * guests if booking_data.get('breakfast') == 'yes' else 0

            total = (base_price + breakfast_cost) * nights
            return total
        except Exception as e:
            print(f"Price calculation error: {e}")
            return None

    def get_response(self, current_step, booking_data, user_message=None):
        if current_step == 'welcome':
            return random.choice(self.training_responses['greeting']) + " " + random.choice(self.training_responses['ask_name'])

        elif current_step == 'get_name':
            if user_message:
                booking_data['name'] = self.extract_info(user_message, 'get_name', booking_data)
                return f"Nice to meet you, {booking_data['name']}! " + random.choice(self.training_responses['ask_email'])
            return random.choice(self.training_responses['ask_name'])

        elif current_step == 'get_email':
            if user_message:
                email = self.extract_info(user_message, 'get_email', booking_data)
                if email:
                    booking_data['email'] = email
                    return random.choice(self.training_responses['ask_dates'])
                return "Please provide a valid email address."
            return random.choice(self.training_responses['ask_email'])

        elif current_step == 'get_checkin':
            if user_message:
                checkin = self.extract_info(user_message, 'get_checkin', booking_data)
                if checkin:
                    booking_data['checkin'] = checkin
                    return random.choice(self.training_responses['ask_checkout'])
                return "Please provide a valid check-in date in YYYY-MM-DD format or say 'tomorrow'."
            return random.choice(self.training_responses['ask_dates'])

        elif current_step == 'get_checkout':
            if user_message:
                checkout = self.extract_info(user_message, 'get_checkout', booking_data)
                if checkout:
                    checkin_date = datetime.strptime(booking_data['checkin'], '%Y-%m-%d').date()
                    checkout_date = datetime.strptime(checkout, '%Y-%m-%d').date()

                    if checkout_date <= checkin_date:
                        return "Check-out date must be after check-in date. Please enter a valid check-out date."

                    booking_data['checkout'] = checkout
                    return random.choice(self.training_responses['ask_guests'])
                return "Please provide a valid check-out date."
            return random.choice(self.training_responses['ask_checkout'])

        elif current_step == 'get_guests':
            if user_message:
                guests = self.extract_info(user_message, 'get_guests', booking_data)
                if guests:
                    booking_data['guests'] = guests
                    return random.choice(self.training_responses['ask_room_type'])
                return "Please enter a valid number of guests."
            return random.choice(self.training_responses['ask_guests'])

        elif current_step == 'get_room_type':
            if user_message:
                room_type = user_message.lower().strip()
                if room_type in ['single', 'double', 'suite']:
                    booking_data['room_type'] = room_type
                    return random.choice(self.training_responses['ask_breakfast'])
                return "Please choose from: single, double, or suite."
            return random.choice(self.training_responses['ask_room_type'])

        elif current_step == 'get_breakfast':
            if user_message:
                breakfast = user_message.lower().strip()
                if breakfast in ['yes', 'no']:
                    booking_data['breakfast'] = breakfast
                    price = self.calculate_price(booking_data)

                    if price is None:
                        return "There was an issue calculating the booking price. Please check your dates and try again."

                    booking_data['price'] = price

                    return f"""
{random.choice(self.training_responses['confirmation'])}

📋 Booking Summary:
• Name: {booking_data['name']}
• Email: {booking_data['email']}
• Check-in: {booking_data['checkin']}
• Check-out: {booking_data['checkout']}
• Guests: {booking_data['guests']}
• Room: {booking_data['room_type']}
• Breakfast: {booking_data['breakfast']}
• Total: ${price}

Does everything look correct? (yes/no)
"""
                return "Please answer yes or no."
            return random.choice(self.training_responses['ask_breakfast'])

        elif current_step == 'confirm_booking':
            if user_message and user_message.lower().strip() == 'yes':
                return f"""
{random.choice(self.training_responses['completion'])}

📧 A confirmation has been sent to {booking_data['email']}
🏨 We look forward to welcoming you, {booking_data['name']}!
💳 Total charged: ${booking_data['price']}

Thank you for choosing Sunshine Hotel! 🌟
"""
            return "Booking cancelled. Type 'start over' to begin again."

        return "I'm here to help you book a room. What would you like to do?"

    @app.route('/reset')
    def reset():
        session.clear()
        return redirect(url_for('index'))

    if __name__ == '__main__':
        print("Starting Flask app...")
        app.run(host='127.0.0.1', port=5000, debug=True)