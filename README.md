
# Automated-Stock-&-Crypto-Price-Volatility-alert

## Introduction

Market volatility can make it difficult to keep track of your favorite stocks and cryptocurrencies. With this project, you can automate the monitoring process with real-time alerts for price movements.


## AWS architecture
![Project architecture](https://monkheart.s3.ap-south-1.amazonaws.com/Github/project.jpg)


## Features

- CloudWatch Events trigger an SQS service at regular intervals.

- The SQS service generates a query message, which invokes a Lambda function.

- The Lambda function collects live data for specified tickers from Yahoo Finance.

- The data is automatically stored in a DynamoDB database.

- New data in the database triggers another Lambda function using DynamoDB streams.

- This Lambda function calculates the volatility in price by comparing the latest and previous prices for each ticker.

- If the volatility exceeds a threshold percentage, an alert Email is sent to the user via AWS SES service.

### Benefits:

- The system eliminates the need for manual monitoring and saves time and effort.
- The automation of data retrieval and processing ensures accuracy and consistency.
- The use of AWS services provides scalability, flexibility, and security.

## Technologies Used

- CloudWatch Event
- AWS SQS (Simple Queue Service)
- AWS IAM (Identity and Access Management)
- AWS Lambda
- AWS DynamoDB
- AWS SES (Simple Email Service)
- Python
## 
##  
## CloudWatch Event triger :
CloudWatch Events trigger an SQS service at regular intervals.


![CloudWatch Event ](https://monkheart.s3.ap-south-1.amazonaws.com/Github/cloudWatch.png)
## 
## 
## Lambda Stock_api
The SQS service generates a query message, which invokes a Lambda function.
![Stock_api](https://monkheart.s3.ap-south-1.amazonaws.com/Github/stock_api.png)
## 
## 
## Code for live data collection :

To run this code, we need to upload a deployement package in lambda layer. This package include all the necessary libraries which is used by python to perform the task.

```python
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
        fav_stocks[symbol] = round(price, 2)  # Store the price in the dictionary, rounded to two decimal.

    ddb_data = json.loads(json.dumps(fav_stocks),parse_float=decimal.Decimal)
    # Convert the prices to Decimal values for storage in DynamoDB

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

```


This code will get the live data from yahoo finance and will store the price for given ticker into the DynamoDB table mentioned.
## 
## 
## DynamoDB
The data is automatically stored in a DynamoDB database.

![DynamoDB](https://monkheart.s3.ap-south-1.amazonaws.com/Github/DynamoDb.png)
## 
## 
## Lambda stream
New data in the database triggers another Lambda function using DynamoDB streams.

![DynamoDB](https://monkheart.s3.ap-south-1.amazonaws.com/Github/stream.png)
## 
## 
## Code for calculation :

```python
import json
import boto3
from boto3.dynamodb.conditions import Key
import os

table_name = os.environ['table_name'] # get table name from environment variables
SENDER = os.environ['sender'] # get sender email from environment variables
RECIPIENT = os.environ['recipient'] # get recipient email from environment variables
AWS_REGION = os.environ['region'] # get AWS region from environment variables
percent_change = int(os.environ['percent_change']) # get percent change threshold from environment variables

def find_volatility(values):
    """function to compare the prices
    Returns
    ------
    Percentage of Volatility
    """
    print('I am here in volatile--->')
    item_values = values[:2]
    ticker = item_values[0]['ticker']
    volatile_values = []
    for item in item_values:
        value = float(item['price'])
        volatile_values.append(value)

    message = None  # initialize tweet variable to None

    if len(volatile_values) == 1:
        pass
    else:
        if volatile_values[0] > volatile_values[1]:
            increase = volatile_values[0] - volatile_values[1]
            increase_percent = int((increase / volatile_values[1]) * 100)
            message = "There is volatility in the market. The price of " + ticker + " has rised by " + str(
                increase) + "%" + " with current price " + str(volatile_values[0])
        elif volatile_values[0] == volatile_values[1]:
            pass
        else:
            decrease = volatile_values[1] - volatile_values[0]
            decrease_percent = int((decrease / volatile_values[1]) * 100)
            message = "There is volatility in the market. The price of " + ticker + " has dropped by " + str(
                decrease) + "%" + " with current price " + str(volatile_values[0])
    if message:
        return message
    else:
        pass

def Email(values):
    if len(values) > 1:
        mail = find_volatility(values) # call find_volatility function to check for volatility
    else:
        mail = None

    ses = boto3.client('ses', region_name=AWS_REGION) # create an SES client for sending email
    CHARSET = "UTF-8"
    SUBJECT = "Serverless-Workflow for Stocks and Crypto Volatility"
    BODY = """
    Hello, 
    Here's an update on your favorite Stock/Crypto price movements:

    %s

    """ % mail if mail else "No volatility detected." # format email body to include volatility message or default message
    x=0
    for item in values:
        if x <2:
            ticker = item["ticker"]
            price = item["price"]
            timestamp = item["timestamp"]
            BODY += f"{ticker} at {price} as of {timestamp}\n\t" # add ticker, price and timestamp information to email body
            x+=1
        else:
            break
    BODY += """
    Regards,
    Manish
    """
    try:
        response = ses.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT, # set recipient email
                ],
            },
            Message={
                'Body': {
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY, # set email body
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT, # set email subject
                },
            },
            Source=SENDER, # set sender email

        )
    except Exception as e:
        print(e)

def lambda_handler(event, context):
    for record in event['Records']:
        if record['eventName'] == "INSERT": # check if new record was inserted
            newImage = record["dynamodb"]["NewImage"]
            ticker = newImage["ticker"]["S"]
            newTickerPrice = newImage["price"]["N"]
            timestamp = newImage["timestamp"]["N"]

            dynamodb = boto3.resource('dynamodb')
            table = dynamodb.Table(table_name) # get DynamoDB table object
            response = table.query(
                KeyConditionExpression=Key('ticker').eq(ticker), # query for items with the same ticker
                ScanIndexForward=False
            )
            values = response['Items'] # get list of items with the same ticker

            Email(values) # send email with price information
```

This code will calculate the changes, if the calculated change in price is exceed the Threshold, it will email the user.

## 
## 
## Triggered E-mail

### E-mail 1
![Email 1](https://monkheart.s3.ap-south-1.amazonaws.com/Github/proof+2.png)

### E-mail 2

![Email 2](https://monkheart.s3.ap-south-1.amazonaws.com/Github/proof+2.png)




## Room For improvement :

To manage data efficiently in a growing DynamoDB table, create a lambda function that removes all items except the latest and last five. Event source of Trigger for the function, when table item count exceeds 100. 

Necessary IAM roles and permissions must be set up. Thorough testing is crucial to ensure proper function and avoid issues. This approach saves costs and optimizes performance. It's useful for monitoring stock and crypto prices using free tier account.
## Conclusion :

With this stock and crypto price alert system, you can stay updated on price movements of your favorite stocks or crypto without having to monitor the market continuously.
