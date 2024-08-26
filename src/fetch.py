import requests
from bs4 import BeautifulSoup

# Specify the stock ticker symbol
stock_symbol = "540205"
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

print(get_price(stock_symbol=stock_symbol))