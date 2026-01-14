import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ==================== EMAIL CONFIGURATION ====================
# For Gmail: Enable "App Passwords" in your Google Account settings
# Go to: https://myaccount.google.com/apppasswords

SMTP_SERVER = "smtp.gmail.com"  # Gmail SMTP
SMTP_PORT = 587
SENDER_EMAIL = "your_email@gmail.com"  # Your email
SENDER_PASSWORD = "your_app_password"  # Your app password (not regular password!)

# ==================== EMAIL TEMPLATES ====================
def create_booking_email_html(booking_data):
    """Create HTML email template for booking confirmation"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; }}
            .header {{ background-color: #e50914; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; }}
            .booking-details {{ background-color: #f9f9f9; padding: 15px; margin: 20px 0; }}
            .footer {{ text-align: center; color: #666; font-size: 12px; padding: 20px; }}
            .button {{ background-color: #e50914; color: white; padding: 10px 20px; 
                      text-decoration: none; display: inline-block; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎬 CineMatch Booking Confirmation</h1>
            </div>
            <div class="content">
                <h2>Hello {booking_data['user_name']}!</h2>
                <p>Your movie ticket has been successfully booked! Here are your details:</p>
                
                <div class="booking-details">
                    <h3>Booking Details</h3>
                    <p><strong>Booking ID:</strong> #{booking_data.get('booking_id', 'N/A')}</p>
                    <p><strong>Movie:</strong> {booking_data['movie_title']}</p>
                    <p><strong>Theater:</strong> {booking_data['theater']}</p>
                    <p><strong>Showtime:</strong> {booking_data['showtime']}</p>
                    <p><strong>Seats:</strong> {booking_data['seats']}</p>
                    <p><strong>Total Amount:</strong> ₹{booking_data['total_price']}</p>
                    <p><strong>Booking Date:</strong> {booking_data['booking_date']}</p>
                </div>
                
                <p><strong>Important Instructions:</strong></p>
                <ul>
                    <li>Please arrive 15 minutes before showtime</li>
                    <li>Carry a valid ID for verification</li>
                    <li>Show this email at the counter to collect tickets</li>
                </ul>
                
                <center>
                    <a href="#" class="button">View Ticket</a>
                </center>
            </div>
            <div class="footer">
                <p>Thank you for choosing CineMatch!</p>
                <p>Questions? Contact us at support@cinematch.com</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

# ==================== SEND EMAIL FUNCTION ====================
def send_booking_confirmation(booking_data):
    """
    Send booking confirmation email to user
    
    Args:
        booking_data (dict): Dictionary containing booking information
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = f"🎬 Booking Confirmed - {booking_data['movie_title']}"
        message["From"] = SENDER_EMAIL
        message["To"] = booking_data['user_email']
        
        # Create plain text version
        text = f"""
        CineMatch Booking Confirmation
        
        Hello {booking_data['user_name']},
        
        Your movie ticket has been successfully booked!
        
        Booking Details:
        - Movie: {booking_data['movie_title']}
        - Theater: {booking_data['theater']}
        - Showtime: {booking_data['showtime']}
        - Seats: {booking_data['seats']}
        - Total Amount: ₹{booking_data['total_price']}
        
        Please arrive 15 minutes before showtime.
        
        Thank you for choosing CineMatch!
        """
        
        # Create HTML version
        html = create_booking_email_html(booking_data)
        
        # Attach both versions
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        message.attach(part1)
        message.attach(part2)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure connection
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(message)
        
        print(f"✅ Email sent successfully to {booking_data['user_email']}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        return False

# ==================== SENDGRID ALTERNATIVE ====================
# If you want to use SendGrid instead of Gmail SMTP:

"""
# Install SendGrid: pip install sendgrid
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SENDGRID_API_KEY = "your_sendgrid_api_key"

def send_booking_confirmation_sendgrid(booking_data):
    message = Mail(
        from_email='your_verified_sender@example.com',
        to_emails=booking_data['user_email'],
        subject=f'🎬 Booking Confirmed - {booking_data["movie_title"]}',
        html_content=create_booking_email_html(booking_data)
    )
    
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email sent! Status code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
"""

# ==================== TEST FUNCTION ====================
if __name__ == "__main__":
    # Test email sending
    test_booking = {
        'booking_id': 1,
        'user_name': 'John Doe',
        'user_email': 'test@example.com',  # Replace with your email for testing
        'movie_title': 'Inception',
        'theater': 'PVR Cinemas Phoenix',
        'showtime': '06:00 PM',
        'seats': 'A1, A2',
        'booking_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'total_price': 500
    }
    
    send_booking_confirmation(test_booking)