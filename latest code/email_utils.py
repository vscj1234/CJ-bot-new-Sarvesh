from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os

def send_email(user_message, bot_response):
    message = Mail(
        from_email='support@cloudjune.com',
        to_emails='marketing@cloudjune.com',  # Update with recipient email
        subject='User Enquiry',
        html_content=f'<p>User Message: {user_message}</p><p>Bot Response: {bot_response}</p>'
    )

    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(str(e))
