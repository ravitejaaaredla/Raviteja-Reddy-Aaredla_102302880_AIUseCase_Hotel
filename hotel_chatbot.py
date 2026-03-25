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
            "greeting": [
                "Hello! Welcome to Sunshine Hotel 🌞 How can I assist you today?",
                "Hi there! Ready to book your perfect stay at Sunshine Hotel?",
                "Welcome! I’m here to help you book a room at Sunshine Hotel."
            ],
            "ask_name": [
                "May I have your name to get started?",
                "What’s your name so I can personalize your booking?",
                "Could you please tell me your name?"
            ],
            "ask_email": [
                "What’s your email address for the confirmation?",
                "Please provide your email so we can send your booking details.",
                "May I have your email address?"
            ],
            "ask_dates": [
                "When would you like to check in? You can use YYYY-MM-DD or say 'tomorrow'.",
                "What are your preferred check-in dates?",
                "When will you be arriving?"
            ],
            "ask_checkout": [
                "When will you be checking out?",
                "What’s your check-out date?",
                "How many nights will you be staying?"
            ],
            "ask_guests": [
                "How many guests will be staying?",
                "Could you tell me the number of guests?",
                "How many people will be in your party?"
            ],
            "ask_room_type": [
                "What type of room would you prefer: single, double, or suite?",
                "Please choose a room: single ($100), double ($150), or suite ($250)."
            ],
            "ask_breakfast": [
                "Would you like breakfast included for $20 per person? Please answer yes or no.",
                "Would you like to add breakfast to your stay?"
            ],
            "confirmation": [
                "Great! Let me confirm your booking details.",
                "Perfect! Here is your booking summary.",
                "Thank you. I’m reviewing your reservation details now."
            ],
            "completion": [
                "🎉 Booking confirmed! Thank you for choosing Sunshine Hotel.",
                "✅ Your reservation is confirmed. We look forward to welcoming you.",
                "📅 Your stay has been booked successfully. Welcome to Sunshine Hotel."
            ]
        }

        self.faq_responses = {
            "greeting": {
                "patterns": ["hello", "hi", "hey", "good morning", "good evening"],
                "answer": "Hello! Welcome to Sunshine Hotel 🌞 How can I assist you today?"
            },
            "checkin_checkout": {
                "patterns": [
                    "what time is check in", "what time is check-in",
                    "check in time", "check-in time",
                    "what time is check out", "what time is check-out",
                    "check out time", "check-out time"
                ],
                "answer": "Our check-in time is 2:00 PM and check-out time is 11:00 AM."
            },
            "room_availability": {
                "patterns": [
                    "do you have any available rooms", "available rooms",
                    "rooms available", "is any room available"
                ],
                "answer": "Room availability depends on your check-in and check-out dates. I can help you check and book a single, double, or suite room."
            },
            "wifi": {
                "patterns": [
                    "what's the wi-fi password", "what is the wi-fi password",
                    "wifi password", "wi-fi password", "internet password"
                ],
                "answer": "Complimentary Wi-Fi is available for all guests. The Wi-Fi password is shared at reception during check-in."
            },
            "breakfast": {
                "patterns": [
                    "do you offer breakfast", "breakfast",
                    "breakfast timing", "what are the breakfast timings"
                ],
                "answer": "Yes, we offer breakfast daily from 7:00 AM to 10:00 AM for an additional $20 per person."
            },
            "parking": {
                "patterns": [
                    "is parking available", "is parking free",
                    "parking", "do you have parking"
                ],
                "answer": "Yes, parking is available for guests. Complimentary parking is subject to availability."
            },
            "nearby_places": {
                "patterns": [
                    "can you recommend nearby restaurants", "nearby restaurants",
                    "nearby attractions", "places to visit nearby", "restaurants nearby"
                ],
                "answer": "Yes, there are several restaurants, cafés, and local attractions near the hotel. Our reception team can recommend the best nearby options based on your interests."
            },
            "facilities": {
                "patterns": [
                    "is there a gym", "is there a pool", "is there a spa",
                    "gym pool spa", "do you have a gym"
                ],
                "answer": "We offer selected wellness facilities for guests. Please check with reception for the current availability of the gym, pool, and spa."
            },
            "airport_shuttle": {
                "patterns": [
                    "do you provide airport shuttle service", "airport shuttle",
                    "shuttle service", "airport transfer"
                ],
                "answer": "Airport shuttle service can be arranged on request, depending on availability and schedule."
            },
            "luggage": {
                "patterns": [
                    "can you help with luggage", "luggage help",
                    "baggage help", "can you store luggage"
                ],
                "answer": "Yes, we can assist with luggage and also offer luggage storage before check-in or after check-out."
            },
            "cancellation": {
                "patterns": [
                    "what's the cancellation policy", "what is the cancellation policy",
                    "cancellation policy", "can i cancel my booking", "booking cancellation"
                ],
                "answer": "Our cancellation policy depends on the booking type and selected rate. Standard bookings can usually be cancelled up to 24 hours before check-in."
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
        """Parse a date string into a date object. Supports YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, and 'today'/'tomorrow'/'next week'."""
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

    def parse_nights(self, text):
        """Extract number of nights from a phrase like '5 nights' or 'stay for 3 days'."""
        text = text.lower()
        match = re.search(r'(\d+)\s*(nights?|days?)', text)
        if match:
            return int(match.group(1))
        return None

    def extract_info(self, message, step):
        if not message:
            return None
        if step == 'get_name':
            words = message.strip().split()
            if len(words) == 1:
                return words[0].title()
            elif len(words) <= 3 and not any(w in message.lower() for w in ['book', 'room', 'hotel', 'reserve']):
                return ' '.join(words).title()
            else:
                return None
        elif step == 'get_email':
            match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', message)
            return match.group(0) if match else None
        elif step in ['get_checkin', 'get_checkout']:
            parsed = self.parse_date(message)
            if parsed:
                return parsed.strftime('%Y-%m-%d')
            if step == 'get_checkout':
                nights = self.parse_nights(message)
                if nights is not None:
                    return nights
            return None
        elif step == 'get_guests':
            match = re.search(r'\d+', message)
            return int(match.group(0)) if match else None
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
        # FAQ handling
        if message:
            faq_answer = self.get_faq_response(message)
            if faq_answer:
                return faq_answer, False

        if step == 'get_name':
            name = self.extract_info(message, step)
            if name:
                data['name'] = name
                return f"Nice to meet you, {name}! " + random.choice(self.training_responses['ask_email']), True
            return "I didn't catch your name. Could you please tell me your name? (Just your first name is fine)", False

        elif step == 'get_email':
            email = self.extract_info(message, step)
            if email:
                data['email'] = email
                return random.choice(self.training_responses['ask_dates']), True
            return "Please enter a valid email (e.g., name@example.com).", False

        elif step == 'get_checkin':
            date = self.extract_info(message, step)
            if date:
                data['checkin'] = date
                return random.choice(self.training_responses['ask_checkout']), True
            return "Invalid date. Please use YYYY-MM-DD or say 'tomorrow'.", False

        elif step == 'get_checkout':
            result = self.extract_info(message, step)
            if result:
                if isinstance(result, int):  # number of nights
                    try:
                        checkin_date = datetime.strptime(data['checkin'], '%Y-%m-%d')
                        checkout_date = checkin_date + timedelta(days=result)
                        data['checkout'] = checkout_date.strftime('%Y-%m-%d')
                        return random.choice(self.training_responses['ask_guests']), True
                    except Exception:
                        return "There was a problem calculating the checkout date. Please try again.", False
                else:  # date string
                    # Validate that it's after check-in
                    try:
                        checkin = datetime.strptime(data['checkin'], '%Y-%m-%d')
                        checkout = datetime.strptime(result, '%Y-%m-%d')
                        if checkout <= checkin:
                            return "Checkout date must be after check-in. Please enter a later date.", False
                        data['checkout'] = result
                        return random.choice(self.training_responses['ask_guests']), True
                    except Exception:
                        return "Invalid date format. Please use YYYY-MM-DD.", False
            return "Please enter a valid checkout date (YYYY-MM-DD) or number of nights (e.g., '5 nights').", False

        elif step == 'get_guests':
            guests = self.extract_info(message, step)
            if guests:
                data['guests'] = guests
                return random.choice(self.training_responses['ask_room_type']), True
            return "Please enter a valid number of guests.", False

        elif step == 'get_room_type':
            if not message:
                return "Please choose: single, double, or suite.", False
            msg_lower = message.lower()
            room = None
            if 'single' in msg_lower:
                room = 'single'
            elif 'double' in msg_lower:
                room = 'double'
            elif 'suite' in msg_lower:
                room = 'suite'
            if room:
                guests = data.get('guests', 0)
                capacity = {'single': 2, 'double': 4, 'suite': 6}
                if guests > capacity[room]:
                    return f"Sorry, a {room} room can accommodate up to {capacity[room]} guests. Would you like to upgrade to a larger room? (double or suite)", False
                data['room_type'] = room
                return random.choice(self.training_responses['ask_breakfast']), True
            return "Please choose a valid room type: single, double, or suite.", False

        elif step == 'get_breakfast':
            if message and message.lower() in ['yes', 'no']:
                data['breakfast'] = message.lower()
                price = self.calculate_price(data)
                if price is None:
                    return "Error in calculation. Please check your dates.", False
                data['price'] = price
                summary = f"""
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
                return summary, True
            return "Please answer yes or no.", False

        elif step == 'confirm_booking':
            if message and message.lower() == 'yes':
                return f"Booking confirmed! 🎉 Email sent to {data['email']}", True
            return "Booking cancelled.", True

        # Fallback – should never reach here
        return "Let's continue with your booking. Please answer the questions above.", True


chatbot = AdvancedHotelChatbot()


@app.route('/', methods=['GET', 'POST'])
def index():
    if 'step' not in session:
        session['step'] = 'get_name'
        session['data'] = {}
        session['messages'] = []
        greeting = random.choice(chatbot.training_responses['greeting'])
        ask_name = random.choice(chatbot.training_responses['ask_name'])
        session['messages'].append(f"👩🏻‍💼: {greeting} {ask_name}")
        session.modified = True

    if request.method == 'POST':
        user_input = request.form.get('user_input', '').strip()
        if user_input:
            session['messages'].append(f"You: {user_input}")

            response, success = chatbot.get_response(session['step'], session['data'], user_input)
            session['messages'].append(f"👩🏻‍💼: {response}")

            if success:
                flow = ['get_name', 'get_email', 'get_checkin', 'get_checkout',
                        'get_guests', 'get_room_type', 'get_breakfast', 'confirm_booking']
                if session['step'] in flow:
                    idx = flow.index(session['step'])
                    if idx + 1 < len(flow):
                        session['step'] = flow[idx + 1]

    clean_messages = []
    for msg in session.get('messages', []):
        if isinstance(msg, tuple):
            sender, text = msg
            if sender.lower() == 'you':
                clean_messages.append(f"You: {text}")
            else:
                clean_messages.append(f"👩🏻‍💼: {text}")
        else:
            clean_messages.append(msg)
    session['messages'] = clean_messages

    return render_template('index.html', messages=session['messages'])


@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)