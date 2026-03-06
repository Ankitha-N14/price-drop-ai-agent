import smtplib
from email.mime.text import MIMEText

import os

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_email(user_email,product,price,url):

    msg = MIMEText(f"""
Price drop detected!

Product: {product}

New Price: ₹{price}

Buy here:
{url}
""")

    msg["Subject"] = "Price Drop Alert"
    msg["From"] = EMAIL
    msg["To"] = user_email

    server = smtplib.SMTP_SSL("smtp.gmail.com",465)
    server.login(EMAIL,PASSWORD)

    server.sendmail(EMAIL,user_email,msg.as_string())

    server.quit()
