import json
import yfinance as yf
import csv
from collections import defaultdict
import requests
from bs4 import BeautifulSoup

class PortfolioManager:
    def __init__(self):
        self.exchange_symbol = {
            "NSE": "NS",
            "BSE": "BO"
        }

    def get_aggregated_transaction(self):
        # Load the transactions from the JSON file
        with open('transactions.json', 'r') as file:
            transactions = json.load(file)

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
            aggregated_transactions[security]['exchange'] = self.exchange_symbol[transaction['exchange']]
        return aggregated_transactions

    def get_security_name(self, symbol, exchange):
        try:
            stock_data = yf.Ticker(f"{symbol}.{exchange}")
            return stock_data.info['shortName']
        except Exception as e:
            print(f"Error fetching name for {symbol}: {e}")
            return symbol

    def get_price(self, stock_symbol):
        # Construct the Google Finance URL
        url = f"https://www.google.com/finance/quote/{stock_symbol}:BOM"

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

    def calculate_profit_loss(self, security, data):
        exchange = data['exchange']
        stock_symbol = f"{security}.{exchange}"  # NSE symbol
        stock_data = yf.Ticker(stock_symbol)
        
        # Fetch the current stock price
        try:
            current_price = stock_data.history(period="1d")['Close'].iloc[0]
        except IndexError:
            current_price = self.get_price(security)
        
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
            "name": self.get_security_name(security, exchange),
            "average_price": average_price,
            "total_units": data['total_units'],
            "original_cost": total_cost,
            "current_market_value": current_market_value,
            "profit_or_loss": profit_or_loss,
            "current_price": current_price
        }

    def get_my_portfolio(self):
        # Process each aggregated transaction and collect results
        aggregated_transactions = self.get_aggregated_transaction()
        results = []
        for security, data in aggregated_transactions.items():
            result = self.calculate_profit_loss(security, data)
            if result:
                results.append(result)
        return results

    def calculate_overall_profit_loss(self, portfolio_results):
        total_cost = sum(result['original_cost'] for result in portfolio_results)
        total_market_value = sum(result['current_market_value'] for result in portfolio_results)
        overall_profit_loss = total_market_value - total_cost
        
        return {
            "total_cost": total_cost,
            "total_market_value": total_market_value,
            "overall_profit_loss": overall_profit_loss
        }

    def write_to_csv(self, results, overall_stats):
        # Define CSV file headers
        headers = ["Security Name", "Average Price", "Total Units", "Original Cost", "Current Market Value", "Profit/Loss", "Current Price", "Security Symbol"]

        # Write the results to a CSV file
        with open('my_portfolio.csv', 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            
            # Write the header
            writer.writeheader()
            
            # Write the rows for each security
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

            # Write the overall stats as the last row
            writer.writerow({
                "Security Name": "Overall",
                "Average Price": "",
                "Total Units": "",
                "Original Cost": f"{overall_stats['total_cost']:.2f}",
                "Current Market Value": f"{overall_stats['total_market_value']:.2f}",
                "Profit/Loss": f"{overall_stats['overall_profit_loss']:.2f}",
                "Current Price": "",
                "Security Symbol": ""
            })

        print("Results have been written to 'my_portfolio.csv'.")

    @staticmethod
    def main():
        portfolio_manager = PortfolioManager()
        results = portfolio_manager.get_my_portfolio()
        
        # Calculate overall profit or loss
        overall_result = portfolio_manager.calculate_overall_profit_loss(results)
        
        # Write portfolio results and overall stats to CSV
        portfolio_manager.write_to_csv(results, overall_result)
        
        print(f"Overall Profit/Loss: {overall_result['overall_profit_loss']:.2f}")
        print(f"Total Original Cost: {overall_result['total_cost']:.2f}")
        print(f"Total Current Market Value: {overall_result['total_market_value']:.2f}")

if __name__ == "__main__":
    PortfolioManager.main()
