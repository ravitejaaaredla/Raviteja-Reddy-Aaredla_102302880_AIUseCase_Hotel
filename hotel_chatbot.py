from flask import Flask, render_template, request, session, redirect, url_for
from datetime import datetime
import re
import json
import random

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a random secret key


class AdvancedHotelChatbot:
    def __init__(self):
        self.room_prices = {'single': 100, 'double': 150, 'suite': 250}
        self.breakfast_price = 20

        # Training data for more natural conversations
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
                "When would you like to check in? (You can say 'tomorrow', 'next Friday', or use YYYY-MM-DD)",
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
                "What type of room would you prefer? We have 🛌 single, 🛌🛌 double, and 🏨 suite rooms.",
                "Please choose a room type: single ($100/night), double ($150/night), or suite ($250/night)",
                "Which room would you like? Options: single, double, suite"
            ],
            'ask_breakfast': [
                "Would you like breakfast included for an additional $20 per person? (yes/no)",
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

    def extract_info(self, message, current_step, booking_data):
        """Extract information using NLP patterns"""
        message_lower = message.lower()

        # Extract name
        if 'name' in current_step or current_step == 'get_name':
            if 'name is' in message_lower:
                name = re.search(r'name is (\w+)', message_lower)
                if name:
                    return name.group(1)
            elif 'i am' in message_lower or 'im ' in message_lower:
                name = re.search(r'i am (\w+)|im (\w+)', message_lower)
                if name:
                    return name.group(1) or name.group(2)
            return message.strip().title()

        # Extract email
        elif 'email' in current_step:
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', message)
            return email_match.group() if email_match else None

        # Extract phone
        elif 'phone' in current_step:
            phone_match = re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', message)
            return phone_match.group() if phone_match else None

        # Extract dates
        elif 'date' in current_step or 'check' in current_step:
            # Handle relative dates
            if 'tomorrow' in message_lower:
                return (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            elif 'today' in message_lower:
                return datetime.now().strftime('%Y-%m-%d')
            elif 'next week' in message_lower:
                return (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')

            # Handle specific dates
            date_patterns = [
                r'\b\d{4}-\d{2}-\d{2}\b',
                r'\b\d{1,2}/\d{1,2}/\d{4}\b',
                r'\b\d{1,2}-\d{1,2}-\d{4}\b'
            ]
            for pattern in date_patterns:
                date_match = re.search(pattern, message)
                if date_match:
                    return date_match.group()
            return None

        # Extract numbers for guests
        elif 'guest' in current_step:
            num_match = re.search(r'\b\d+\b', message)
            return num_match.group() if num_match else None

        return message

    def get_response(self, current_step, booking_data, user_message=None):
        """Get AI-powered response based on current step"""
        if current_step == 'welcome':
            return random.choice(self.training_responses['greeting']) + " " + random.choice(
                self.training_responses['ask_name'])

        elif current_step == 'get_name':
            if user_message:
                booking_data['name'] = self.extract_info(user_message, 'get_name', booking_data)
                return f"Nice to meet you, {booking_data['name']}! " + random.choice(
                    self.training_responses['ask_email'])
            return random.choice(self.training_responses['ask_name'])

        elif current_step == 'get_email':
            if user_message:
                email = self.extract_info(user_message, 'get_email', booking_data)
                if email:
                    booking_data['email'] = email
                    return random.choice(self.training_responses['ask_dates'])
                else:
                    return "Please provide a valid email address."
            return random.choice(self.training_responses['ask_email'])

        elif current_step == 'get_checkin':
            if user_message:
                checkin = self.extract_info(user_message, 'get_checkin', booking_data)
                if checkin:
                    booking_data['checkin'] = checkin
                    return random.choice(self.training_responses['ask_checkout'])
                else:
                    return "Please provide a valid date (e.g., 2024-12-25 or 'tomorrow')."
            return random.choice(self.training_responses['ask_dates'])

        elif current_step == 'get_checkout':
            if user_message:
                checkout = self.extract_info(user_message, 'get_checkout', booking_data)
                if checkout:
                    booking_data['checkout'] = checkout
                    return random.choice(self.training_responses['ask_guests'])
                else:
                    return "Please provide a valid check-out date."
            return random.choice(self.training_responses['ask_checkout'])

        elif current_step == 'get_guests':
            if user_message:
                guests = self.extract_info(user_message, 'get_guests', booking_data)
                if guests and guests.isdigit():
                    booking_data['guests'] = guests
                    return random.choice(self.training_responses['ask_room_type'])
                else:
                    return "Please enter a valid number of guests."
            return random.choice(self.training_responses['ask_guests'])

        elif current_step == 'get_room_type':
            if user_message:
                room_type = user_message.lower()
                if room_type in ['single', 'double', 'suite']:
                    booking_data['room_type'] = room_type
                    return random.choice(self.training_responses['ask_breakfast'])
                else:
                    return "Please choose from: single, double, or suite."
            return random.choice(self.training_responses['ask_room_type'])

        elif current_step == 'get_breakfast':
            if user_message:
                breakfast = user_message.lower()
                if breakfast in ['yes', 'no']:
                    booking_data['breakfast'] = breakfast
                    # Calculate price
                    price = self.calculate_price(booking_data)
                    booking_data['price'] = price

                    summary = f"""
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
                    return summary
                else:
                    return "Please answer yes or no."
            return random.choice(self.training_responses['ask_breakfast'])

        elif current_step == 'confirm_booking':
            if user_message and user_message.lower() == 'yes':
                return f"""
                {random.choice(self.training_responses['completion'])}

                📧 A confirmation has been sent to {booking_data['email']}
                🏨 We look forward to welcoming you, {booking_data['name']}!
                💳 Total charged: ${booking_data['price']}

                Thank you for choosing Sunshine Hotel! 🌟
                """
            else:
                return "Booking cancelled. Would you like to start over? (yes/no)"

        return "I'm here to help you book a room. What would you like to do?"

    def calculate_price(self, booking_data):
        """Calculate total price"""
        try:
            # Simple calculation - in real app, calculate based on dates
            base_price = self.room_prices.get(booking_data['room_type'], 150)
            guests = int(booking_data.get('guests', 1))
            breakfast_cost = self.breakfast_price * guests if booking_data.get('breakfast') == 'yes' else 0

            # Assume 3 nights for demo
            nights = 3
            total = (base_price + breakfast_cost) * nights
            return total
        except:
            return 450  # Default price for demo


# Initialize chatbot
chatbot = AdvancedHotelChatbot()


@app.route('/', methods=['GET', 'POST'])
def index():
    # Initialize session if not exists
    if 'messages' not in session:
        session['messages'] = []
        session['booking_data'] = {}
        session['current_step'] = 'welcome'

    if request.method == 'POST':
        user_input = request.form['user_input']

        # Add user message
        session['messages'].append(f"You: {user_input}")

        # Get bot response
        bot_response = chatbot.get_response(
            session['current_step'],
            session['booking_data'],
            user_input
        )

        # Add bot message
        session['messages'].append(f"Bot: {bot_response}")

        # Update current step based on conversation flow
        current_step = session['current_step']
        if current_step == 'welcome':
            session['current_step'] = 'get_name'
        elif current_step == 'get_name' and session['booking_data'].get('name'):
            session['current_step'] = 'get_email'
        elif current_step == 'get_email' and session['booking_data'].get('email'):
            session['current_step'] = 'get_checkin'
        elif current_step == 'get_checkin' and session['booking_data'].get('checkin'):
            session['current_step'] = 'get_checkout'
        elif current_step == 'get_checkout' and session['booking_data'].get('checkout'):
            session['current_step'] = 'get_guests'
        elif current_step == 'get_guests' and session['booking_data'].get('guests'):
            session['current_step'] = 'get_room_type'
        elif current_step == 'get_room_type' and session['booking_data'].get('room_type'):
            session['current_step'] = 'get_breakfast'
        elif current_step == 'get_breakfast' and session['booking_data'].get('breakfast'):
            session['current_step'] = 'confirm_booking'
        elif current_step == 'confirm_booking' and user_input.lower() == 'yes':
            session['current_step'] = 'completed'
        elif user_input.lower() == 'start over':
            session.clear()
            return redirect(url_for('index'))

        session.modified = True

    return render_template('index.html', messages=session['messages'])


@app.route('/reset')
def reset():
    """Reset the conversation"""
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)