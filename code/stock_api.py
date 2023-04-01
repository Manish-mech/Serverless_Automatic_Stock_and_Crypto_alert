import boto3  # Import the boto3 library to interact with AWS services
import time  # Import the time library to get the current time
import decimal  # Import the decimal library for decimal arithmetic
from yahoo_fin.stock_info import *  # Import yahoo_fin.stock_info library for stock price retrieval

dynamodb = boto3.resource('dynamodb')  # Create a connection to DynamoDB
table_name = 'Ticker_table'  # name of your DynamoDB table to store the data
table = dynamodb.Table(table_name)  # Connect to the DynamoDB table


def lambda_handler(event, context):  # Define the AWS Lambda function
    tickers = ['TCS.NS', 'RELIANCE.NS', 'GOOG']  # List of stock tickers to fetch data for

    fav_stocks = {}  # Create an empty dictionary to store the stock prices
    for symbol in tickers:  # Loop through the list of tickers
        price = get_live_price(symbol)  # Get the current price for each stock
        fav_stocks[symbol] = round(price, 2)  # Store the price in the dictionary, rounded to two decimal places

    ddb_data = json.loads(json.dumps(fav_stocks),parse_float=decimal.Decimal)  # Convert the prices to Decimal values for storage in DynamoDB

    for key in ddb_data:  # Loop through the dictionary of stock prices
        response = table.put_item(  # Insert the data into DynamoDB
            Item={
                'ticker': key,  # The stock ticker
                'timestamp': int(round(time.time() * 1000)),  # The current timestamp in milliseconds
                'price': ddb_data[key]  # The current price of the stock
            }
        )

    return {
        'statusCode': 200,  # Return a success status code
        'body': 'Data stored in DynamoDB'  # Return a success message
    }
