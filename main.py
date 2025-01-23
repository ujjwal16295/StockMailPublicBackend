import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from emails import html
import os


# add firebase config here
firebase_config={
  "type": os.getenv("TYPE"),
  "project_id": os.getenv("PROJECT_ID"),
  "private_key_id": os.getenv("PRIVATE_KEY_ID"),
  "private_key": os.getenv("PRIVATE_KEY"),
  "client_email": os.getenv("CLIENT_EMAIL"),
  "client_id": os.getenv("CLIENT_ID"),
  "auth_uri":  os.getenv("AUTH_URI"),
  "token_uri": os.getenv("TOKEN_URI"),
  "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
  "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL"),
  "universe_domain": os.getenv("UNIVERSE_DOMAIN")
}



cred = credentials.Certificate(firebase_config)
firebase_admin.initialize_app(cred)
db=firestore.client()
# Email details
sender_email = os.getenv("EMAIL")
password = os.getenv("PASSWORD")
subject = "Stock Recommendation"

# HTML email template
email_template = """
<!DOCTYPE html>
<html>
<head>
  <style>
    body {{
      font-family: Arial, sans-serif;
      background-color: #d1d5db; /* Light grey background */
      color: #333; /* Dark text */
      margin: 0;
      padding: 0;
    }}
    .email-container {{
      background-color: #374151; /* Dark header background */
      padding: 20px;
      border-radius: 8px;
      max-width: 600px;
      margin: 20px auto;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }}
    .header {{
      text-align: center;
      color: #ffffff;
      font-size: 24px;
      font-weight: bold;
    }}
    .subheader {{
      text-align: center;
      color: #9ca3af; /* Light grey text */
      margin-top: 5px;
      font-size: 16px;
    }}
    .content {{
      background-color: #60a5fa; /* Blue card background */
      padding: 20px;
      border-radius: 8px;
      color: #ffffff; /* White text */
      margin: 20px 0;
    }}
    .stock-list {{
      margin: 0;
      padding: 0;
      list-style-type: none;
      font-size: 18px;
    }}
    .stock-item {{
      margin: 5px 0;
      padding: 10px;
      background-color: #3b82f6; /* Slightly darker blue */
      border-radius: 5px;
      text-align: center;
    }}
    .footer {{
      text-align: center;
      color: #9ca3af;
      font-size: 14px;
      margin-top: 10px;
    }}
    a {{
      color: #ffffff;
      text-decoration: none;
    }}
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">Your Stock List from StockSage</div>
    <div class="subheader">Stay ahead in the market with our insights</div>

    <div class="content">
      <h3>Here are your selected stocks:</h3>
      <ul class="stock-list">
        {stock_items}
      </ul>
    </div>

    <div class="footer">
      <p>Need more insights? Visit <a href="https://stockmail-site.vercel.app/">StockSage</a> to explore more!</p>
      <p>&copy; 2025 StockSage. All rights reserved.</p>
    </div>
  </div>
</body>
</html>
"""

# Firebase collections to query
collections = ['stocks', 'stocksMidCap', 'stocksSmallCap']

# Get all documents from the 'Email' collection
collection_name = "Email"
documents = db.collection(collection_name).stream()

# Loop through each document in 'Email' collection
for doc in documents:
    data = doc.to_dict()
    receiver_email = doc.id  # This is the email address

    # Reset the stock list for each recipient
    stock_list = []

    # Sort the userStockData list by the priority field
    sorted_data = sorted(data['userStockData'], key=lambda x: x['priority'])

    # Extract an array of dictionaries containing type and value in sorted order
    orders = [{'type': item['type'], 'value': item['value'], 'field': item['field'], 'radio': item['radio']} for item in sorted_data]

    for collection in collections:
        db_ref = db.collection(collection)
        for order in orders:
            if order["radio"] == "lower":
                query = db_ref.where(order["field"], "<=", order["value"])
            else:
                query = db_ref.where(order["field"], ">=", order["value"])

            # Fetch the results from the query
            results = query.stream()

            # Add stocks to the list
            for doc in results:
                stock_list.append(doc.to_dict()["name"])

    # Debugging: Print stock_list
    print(f"Stock list for {receiver_email}: {stock_list}")

    # Generate stock_items dynamically
    stock_items = "".join([f'<li class="stock-item">{stock}</li>' for stock in stock_list])
    print(f"Stock items for {receiver_email}: {stock_items}")

    # Update email template dynamically
    email_body = email_template.format(stock_items=stock_items)

    # Prepare the email
    message = html(
        subject="Your Stock List from StockSage",
        html=email_body,
        mail_from=("StockSage", sender_email)
    )

    # Send the email
    response = message.send(
        to=receiver_email,  # Replace with the recipient's email
        smtp={
            "host": "smtp.gmail.com",
            "port": 587,
            "tls": True,
            "user": sender_email,  # Replace with your email
            "password": password  # Replace with your email password or app password
        }
    )

    # Check if the email was sent successfully
    if response.success:
        print(f"Email sent successfully to {receiver_email}!")
    else:
        print(f"Failed to send email to {receiver_email}: {response.error}")
