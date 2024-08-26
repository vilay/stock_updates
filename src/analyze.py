import pandas as pd

def analyze_portfolio(file_path):
    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(file_path)

    # Calculate the sum of the original investment (Original Cost) and current value (Current Market Value)
    total_invested = df['Original Cost'].sum()
    total_current_value = df['Current Market Value'].sum()

    # Calculate the overall gain/loss
    overall_gain = total_current_value - total_invested

    # Print the analysis results
    print(f"Total Invested: ₹{total_invested:.2f}")
    print(f"Total Current Value: ₹{total_current_value:.2f}")
    print(f"Overall Gain/Loss: ₹{overall_gain:.2f}")

# Example usage
file_path = 'my_portpolio.csv'  # Replace with the path to your CSV file
analyze_portfolio(file_path)
