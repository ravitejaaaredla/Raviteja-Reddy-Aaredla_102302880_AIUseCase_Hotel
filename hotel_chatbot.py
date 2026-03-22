from flask import Flask, render_template, request, session, redirect, url_for
from datetime import datetime, timedelta
import re
import random
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")


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
                "When would you like to check in? (Use YYYY-MM-DD or say 'tomorrow')",
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
                "What type of room would you prefer? (single, double, suite)",
                "Choose a room: single ($100), double ($150), suite ($250)"
            ],
            'ask_breakfast': [
                "Would you like breakfast included for $20 per person? (yes/no)"
            ],
            'confirmation': [
                "Great! Let me confirm your booking details..."
            ],
            'completion': [
                "🎉 Booking confirmed! Thank you for choosing Sunshine Hotel!"
            ]
        }

        self.faq_responses = {
            "greeting": {
                "patterns": ["hello", "hi", "hey", "good morning", "good evening"],
                "answer": "Hello! Welcome to Sunshine Hotel 🌞 How can I assist you today? You can ask about rooms, check-in, breakfast, parking, or start a booking."
            },
            "checkin_checkout": {
                "patterns": [
                    "what time is check in",
                    "what time is check-in",
                    "check in time",
                    "check-in time",
                    "what time is check out",
                    "what time is check-out",
                    "check out time",
                    "check-out time"
                ],
                "answer": "Our check-in time is 2:00 PM and check-out time is 11:00 AM."
            },
            "room_availability": {
                "patterns": [
                    "do you have any available rooms",
                    "available rooms",
                    "rooms available",
                    "is any room available"
                ],
                "answer": "Yes, room availability depends on your check-in and check-out dates. I can help you check and book a single, double, or suite room."
            },
            "wifi": {
                "patterns": [
                    "what's the wi-fi password",
                    "wifi password",
                    "wi-fi password",
                    "internet password"
                ],
                "answer": "Our complimentary Wi-Fi is available for all guests. The Wi-Fi password is shared at reception during check-in."
            },
            "breakfast": {
                "patterns": [
                    "do you offer breakfast",
                    "breakfast",
                    "breakfast timing",
                    "what are the breakfast timings"
                ],
                "answer": "Yes, we offer breakfast daily from 7:00 AM to 10:00 AM for an additional $20 per person."
            },
            "parking": {
                "patterns": [
                    "is parking available",
                    "is parking free",
                    "parking",
                    "do you have parking"
                ],
                "answer": "Yes, parking is available for guests. Complimentary parking is subject to availability."
            },
            "nearby_places": {
                "patterns": [
                    "can you recommend nearby restaurants",
                    "nearby restaurants",
                    "nearby attractions",
                    "places to visit nearby",
                    "restaurants nearby"
                ],
                "answer": "Yes, there are several restaurants, cafés, and local attractions near the hotel. Our reception team can recommend the best nearby options based on your interests."
            },
            "facilities": {
                "patterns": [
                    "is there a gym",
                    "is there a pool",
                    "is there a spa",
                    "gym pool spa",
                    "do you have a gym"
                ],
                "answer": "We offer selected wellness facilities for guests. Please check with reception for current availability of the gym, pool, and spa."
            },
            "airport_shuttle": {
                "patterns": [
                    "do you provide airport shuttle service",
                    "airport shuttle",
                    "shuttle service",
                    "airport transfer"
                ],
                "answer": "Airport shuttle service can be arranged on request, depending on availability and schedule."
            },
            "luggage": {
                "patterns": [
                    "can you help with luggage",
                    "luggage help",
                    "baggage help",
                    "can you store luggage"
                ],
                "answer": "Yes, we can assist with luggage and also offer luggage storage before check-in or after check-out."
            },
            "cancellation": {
                "patterns": [
                    "what's the cancellation policy",
                    "cancellation policy",
                    "can i cancel my booking",
                    "booking cancellation"
                ],
                "answer": "Our cancellation policy depends on the booking type and rate selected. Standard bookings can usually be cancelled up to 24 hours before check-in."
            }
        }

    def get_faq_response(self, message):
        message_lower = message.lower().strip()

        for faq in self.faq_responses.values():
            for pattern in faq["patterns"]:
                if pattern in message_lower:
                    return faq["answer"]

        return None

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

    def extract_info(self, message, step):
        if step == 'get_name':
            return message.strip().title()

        elif step == 'get_email':
            match = re.search(r'\b\S+@\S+\.\S+\b', message)
            return match.group(0) if match else None

        elif step in ['get_checkin', 'get_checkout']:
            parsed = self.parse_date(message)
            return parsed.strftime('%Y-%m-%d') if parsed else None

        elif step == 'get_guests':
            match = re.search(r'\d+', message)
            return match.group(0) if match else None

        return message.strip()

    def calculate_price(self, data):
        try:
            checkin = datetime.strptime(data['checkin'], '%Y-%m-%d')
            checkout = datetime.strptime(data['checkout'], '%Y-%m-%d')

            nights = (checkout - checkin).days
            if nights <= 0:
                return None

            base = self.room_prices[data['room_type']]
            guests = int(data['guests'])
            breakfast = self.breakfast_price * guests if data['breakfast'] == 'yes' else 0

            return (base + breakfast) * nights
        except Exception:
            return None

    def get_response(self, step, data, message=None):
        if message:
            faq_answer = self.get_faq_response(message)
            if faq_answer:
                return faq_answer

        if step == 'welcome':
            return random.choice(self.training_responses['greeting']) + " " + random.choice(self.training_responses['ask_name'])

        elif step == 'get_name':
            name = self.extract_info(message, step)
            data['name'] = name
            return f"Nice to meet you, {name}! " + random.choice(self.training_responses['ask_email'])

        elif step == 'get_email':
            email = self.extract_info(message, step)
            if email:
                data['email'] = email
                return random.choice(self.training_responses['ask_dates'])
            return "Please enter a valid email."

        elif step == 'get_checkin':
            date = self.extract_info(message, step)
            if date:
                data['checkin'] = date
                return random.choice(self.training_responses['ask_checkout'])
            return "Invalid date."

        elif step == 'get_checkout':
            date = self.extract_info(message, step)
            if date:
                data['checkout'] = date
                return random.choice(self.training_responses['ask_guests'])
            return "Invalid checkout date."

        elif step == 'get_guests':
            guests = self.extract_info(message, step)
            if guests:
                data['guests'] = guests
                return random.choice(self.training_responses['ask_room_type'])
            return "Enter valid number of guests."

        elif step == 'get_room_type':
            if message and message.lower() in ['single', 'double', 'suite']:
                data['room_type'] = message.lower()
                return random.choice(self.training_responses['ask_breakfast'])
            return "Choose: single / double / suite"

        elif step == 'get_breakfast':
            if message and message.lower() in ['yes', 'no']:
                data['breakfast'] = message.lower()
                price = self.calculate_price(data)
                if price is None:
                    return "Error in calculation. Please check your dates."

                data['price'] = price

                return f"""
Booking Summary:
Name: {data['name']}
Email: {data['email']}
Checkin: {data['checkin']}
Checkout: {data['checkout']}
Guests: {data['guests']}
Room: {data['room_type']}
Breakfast: {data['breakfast']}
Total: ${price}

Confirm? (yes/no)
"""
            return "Please answer yes/no"

        elif step == 'confirm_booking':
            if message and message.lower() == 'yes':
                return f"Booking confirmed! 🎉 Email sent to {data['email']}"
            return "Booking cancelled."

        return "Start booking by typing anything."


chatbot = AdvancedHotelChatbot()


@app.route('/', methods=['GET', 'POST'])
def index():
    if 'step' not in session:
        session['step'] = 'welcome'
        session['data'] = {}
        session['messages'] = []

        msg = chatbot.get_response('welcome', session['data'])
        session['messages'].append(f"👩🏻‍💼: {msg}")
        session.modified = True

    if request.method == 'POST':
        user_input = request.form.get('user_input', '').strip()

        if user_input:
            session['messages'].append(f": {user_input}")

            response = chatbot.get_response(session['step'], session['data'], user_input)
            session['messages'].append(f"👩🏻‍💼: {response}")

            faq_answer = chatbot.get_faq_response(user_input)

            if not faq_answer:
                flow = [
                    'welcome', 'get_name', 'get_email', 'get_checkin',
                    'get_checkout', 'get_guests', 'get_room_type',
                    'get_breakfast', 'confirm_booking'
                ]

                if session['step'] in flow:
                    idx = flow.index(session['step'])
                    if idx + 1 < len(flow):
                        session['step'] = flow[idx + 1]

            session.modified = True

    return render_template('index.html', messages=session['messages'])