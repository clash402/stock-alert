import requests as req

from decouple import config
from twilio.rest import Client


# PROPERTIES
STOCK_NAME = "TSLA"
COMPANY_NAME = "Tesla Inc"


# STOCK
def get_stock_closing_price(stock_name, day: int):
    alpha_vantage_endpoint = "https://www.alphavantage.co/query"
    alpha_vantage_key = config("ALPHA_VANTAGE_KEY")
    alpha_vantage_params = {"apikey": alpha_vantage_key, "function": "TIME_SERIES_DAILY", "symbol": stock_name}

    res = req.get(alpha_vantage_endpoint, params=alpha_vantage_params)
    res.raise_for_status()

    data = res.json()["Time Series (Daily)"]
    data_list = [value for (_, value) in data.items()]

    return data_list[day]["4. close"]


def get_difference(one_days_ago_closing_price, two_days_ago_closing_price):
    return float(one_days_ago_closing_price) - float(two_days_ago_closing_price)


def round_difference(difference, one_days_ago_closing_price):
    return round((difference / float(one_days_ago_closing_price)) * 100)


def get_up_down_emoji(difference):
    if difference > 0:
        return "🔺"
    else:
        return "🔻"


# NEWS
def get_latest_articles(company_name, stock_name, up_down_emoji, difference_rounded):
    news_api_endpoint = "https://newsapi.org/v2/everything"
    news_api_key = config("NEWS_API_KEY")
    news_api_params = {"apiKey": news_api_key, "qInTitle": company_name}

    res = req.get(news_api_endpoint, params=news_api_params)
    res.raise_for_status()

    articles = res.json()["articles"]
    latest_three_articles = articles[:3]

    return [f"{stock_name}: {up_down_emoji}{difference_rounded}%\n\n"
            f"Headline:\n{article['title']}. \n\n"
            f"Brief:\n{article['description']}" for article in latest_three_articles]


# MESSAGE
def will_send_message(company_name, stock_name, up_down_emoji, difference_rounded):
    if abs(difference_rounded) > 1:
        latest_articles = get_latest_articles(company_name, stock_name, up_down_emoji, difference_rounded)

        twilio_sid = config("TWILIO_SID")
        twilio_auth_token = config("TWILIO_AUTH_TOKEN")
        twilio_client = Client(twilio_sid, twilio_auth_token)

        for article in latest_articles:
            twilio_client.messages.create(
                body=article,
                from_=config("SENDING_PHONE_NUMBER"),
                to=config("RECEIVING_PHONE_NUMBER")
            )


# MAIN
one_days_ago_closing_price = get_stock_closing_price(STOCK_NAME, 0)
two_days_ago_closing_price = get_stock_closing_price(STOCK_NAME, 1)
difference = get_difference(one_days_ago_closing_price, two_days_ago_closing_price)
difference_rounded = round_difference(difference, one_days_ago_closing_price)
up_down_emoji = get_up_down_emoji(difference)

will_send_message(COMPANY_NAME, STOCK_NAME, up_down_emoji, difference_rounded)
