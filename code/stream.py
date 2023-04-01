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