import json
import yfinance as yf
import csv
from collections import defaultdict
import requests
from bs4 import BeautifulSoup

# Load the transactions from the JSON file
with open('transactions.json', 'r') as file:
    transactions = json.load(file)

exchange_symbol = {
    "NSE": "NS",
    "BSE": "BO"
}

# Aggregate transactions by security
aggregated_transactions = defaultdict(lambda: {"total_units": 0, "total_amount": 0, "total_expenses": 0})

for transaction in transactions:
    security = transaction['security']
    if transaction['type'] == "BUY":
        aggregated_transactions[security]['total_units'] += transaction['units']
        aggregated_transactions[security]['total_amount'] += transaction['amount']
        aggregated_transactions[security]['total_expenses'] += transaction['tran_expense']
    elif transaction['type'] == "SELL":
        aggregated_transactions[security]['total_units'] -= transaction['units']
        aggregated_transactions[security]['total_amount'] -= transaction['amount']
        aggregated_transactions[security]['total_expenses'] += transaction['tran_expense']
    aggregated_transactions[security]['exchange'] = exchange_symbol[transaction['exchange']]

# Function to get the name of the security
def get_security_name(symbol, exchange):
    try:
        stock_data = yf.Ticker(f"{symbol}.{exchange}")
        return stock_data.info['shortName']
    except Exception as e:
        print(f"Error fetching name for {symbol}: {e}")
        return symbol

def get_price(stock_symbol):
    # Construct the Google Finance URL
    url = f"https://www.google.com/finance/quote/{stock_symbol}:NSE"

    # Send a request to the URL
    response = requests.get(url)

    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the element containing the stock price
    price_element = soup.find('div', class_='YMlKec fxKbKc')
    
    # Extract text and remove currency symbol and commas
    price_text = price_element.text.strip()
    price_number = float(price_text.replace('₹', '').replace(',', ''))
    
    return price_number

# Function to calculate profit or loss for each aggregated transaction
def calculate_profit_loss(security, data):
    exchange = data['exchange']
    stock_symbol = f"{security}.{exchange}"  # NSE symbol
    stock_data = yf.Ticker(stock_symbol)
    
    # Fetch the current stock price
    try:
        current_price = stock_data.history(period="1d")['Close'].iloc[0]
    except IndexError:
        # Handle case where no price data is found
        print(f"No price data found for {security} on {exchange}. You may need to check the stock symbol or manually enter the price.")
        current_price = 0
        return
    
    # Calculate the average purchase price per unit
    average_price = data['total_amount'] / data['total_units'] if data['total_units'] > 0 else 0
    
    # Calculate the total cost including aggregated transaction expenses
    total_cost = data['total_amount'] + data['total_expenses']
    
    # Calculate the current market value of the units held
    current_market_value = data['total_units'] * current_price
    
    # Calculate profit or loss
    profit_or_loss = current_market_value - total_cost
    
    return {
        "security": security,
        "name": get_security_name(security, exchange),
        "average_price": average_price,
        "total_units": data['total_units'],
        "original_cost": total_cost,
        "current_market_value": current_market_value,
        "profit_or_loss": profit_or_loss,
        "current_price": current_price
    }

# Process each aggregated transaction and collect results
results = []
for security, data in aggregated_transactions.items():
    result = calculate_profit_loss(security, data)
    if result:
        results.append(result)

# Define CSV file headers
headers = ["Security Name", "Average Price", "Total Units", "Original Cost", "Current Market Value", "Profit/Loss", "Current Price", "Security Symbol"]

# Write the results to a CSV file
with open('results.csv', 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=headers)
    
    # Write the header
    writer.writeheader()
    
    # Write the rows
    for result in results:
        writer.writerow({
            "Security Name": result['name'],
            "Average Price": f"{result['average_price']:.2f}",
            "Total Units": result['total_units'],
            "Original Cost": f"{result['original_cost']:.2f}",
            "Current Market Value": f"{result['current_market_value']:.2f}",
            "Profit/Loss": f"{result['profit_or_loss']:.2f}",
            "Current Price": f"{result['current_price']:.2f}",
            "Security Symbol": result['security'],
        })

print("Results have been written to 'results.csv'.")
