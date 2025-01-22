import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import yagmail


# Initialize Firebase Admin SDK
cred = credentials.Certificate("venv/serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Get all documents from the 'Email' collection
collection_name = "Email"
documents = db.collection(collection_name).stream()

# Fetch collections to filter stocks
collections = ['stocks', 'stocksMidCap', 'stocksSmallCap']

sender_email = "ujjwalpatel000777@gmail.com"
receiver_email = "newujjwalpatel@gmail.com"
password = "hdic suzn eesl qytc"
subject = "Stock Recommendation "
email_body = ""

# Function to filter stocks based on criteria
def filter_stock(stock, filter_criteria):
    for criterion in filter_criteria:
        field_name = criterion['field']  # Field name from 'userStockData'
        stock_value = stock.get(field_name)
        print(stock_value)
        print(criterion["value"])
        if stock_value is None:
            return False  # If the stock doesn't have the field, it doesn't match
        if criterion['radio'] == 'higher' and stock_value <= criterion['value'][0]:
            return False
        elif criterion['radio'] == 'lower' and stock_value >= criterion['value'][0]:
            return False
    return True


# Loop through each document in 'Email' collection
for doc in documents:
    print(f"Document ID: {doc.id}")
    data = doc.to_dict()
    email = doc.id  # This is the email address

    # Sort the userStockData list by the priority field
    sorted_data = sorted(data['userStockData'], key=lambda x: x['priority'])

    # Extract an array of dictionaries containing type and value in sorted order
    order = [{'type': item['type'], 'value': item['value'], 'field': item['field'], 'radio': item['radio']} for item in
             sorted_data]
    print(order)
    # Initialize an empty list to store matching stocks
    matching_stocks = []

    # Loop through all stock collections and filter based on criteria
    for collection in collections:
        docs = db.collection(collection).stream()

        for stock_doc in docs:
            stock = stock_doc.to_dict()

            # Apply filter to this stock based on order criteria
            if filter_stock(stock, order):
                stock['id'] = stock_doc.id  # Include document ID for reference
                matching_stocks.append(stock)

    print(matching_stocks)

    # Rank the matching stocks based on 'value' and 'priority'
    sorted_stocks = sorted(matching_stocks, key=lambda x: sum(
        [criterion['value'][0] for criterion in order if x.get(criterion['field']) is not None]
    ), reverse=True)

    # Prepare the email body
    email_body = "The following stocks match your criteria:\n\n"
    for index,stock in enumerate(sorted_stocks):
        email_body += f"Stock ID: {index}\n"
        email_body += f"Details: {stock["name"]}\n\n"

    # Set up Yagmail
    yag = yagmail.SMTP(user=sender_email, password=password)

    # Prepare the HTML content for the email
    email_body = """
    <html>
      <body>
        <h2>Stock Recommendations Based on Your Criteria</h2>
        <p>Dear User,</p>
        <p>The following stocks match your criteria:</p>
        <table border="1" cellpadding="10">
          <tr>
            <th>Stock ID</th>
            <th>Details</th>
          </tr>
    """

    # Add the stock details to the email (example)
    for index,stock in enumerate(sorted_stocks):
        email_body += f"""
          <tr>
            <td>{index}</td>
            <td>{stock["name"]}</td>
          </tr>
        """

    email_body += """
        </table>
        <p>Best regards,<br>Your Stock Recommendation System</p>
      </body>
    </html>
    """

    # Send the email
    try:
        yag.send(
            to=receiver_email,
            subject="Stock Recommendations Based on Your Criteria",
            contents=email_body
        )
        print(f"Email sent to: {email}")
    except Exception as e:
        print(f"Error sending email to {email}: {e}")

