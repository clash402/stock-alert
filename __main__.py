import requests as req
from decouple import config
from twilio.rest import Client


# PROPERTIES
STOCK_NAME = "TSLA"
COMPANY_NAME = "Tesla Inc"


# STOCK
def get_stock_closing_prices(stock_name):
    alpha_vantage_endpoint = "https://www.alphavantage.co/query"
    alpha_vantage_key = config("ALPHA_VANTAGE_KEY")
    alpha_vantage_params = {"apikey": alpha_vantage_key, "function": "TIME_SERIES_DAILY", "symbol": stock_name}

    res = req.get(alpha_vantage_endpoint, params=alpha_vantage_params)
    res.raise_for_status()

    data = res.json()["Time Series (Daily)"]
    data_list = [value for (_, value) in data.items()]

    yesterdays_data = data_list[0]
    yesterdays_closing_price = yesterdays_data["4. close"]
    day_before_yesterdays_closing_price = data_list[1]["4. close"]

    return yesterdays_closing_price, day_before_yesterdays_closing_price


def get_difference(closing_prices):
    return float(closing_prices[0]) - float(closing_prices[1])


def round_difference(difference, closing_prices):
    return round((difference / float(closing_prices[0])) * 100)


def compare_difference(difference):
    if difference > 0:
        return "🔺"
    else:
        return "🔻"


# NEWS
def get_latest_articles(company_name, stock_name, up_down, difference_rounded):
    news_api_endpoint = "https://newsapi.org/v2/everything"
    news_api_key = config("NEWS_API_KEY")
    news_api_params = {"apiKey": news_api_key, "qInTitle": company_name}

    res = req.get(news_api_endpoint, params=news_api_params)
    res.raise_for_status()

    articles = res.json()["articles"]
    latest_three_articles = articles[:3]

    return [f"{stock_name}: {up_down}{difference_rounded}%\n\n"
            f"Headline:\n{article['title']}. \n\n"
            f"Brief:\n{article['description']}" for article in latest_three_articles]


# MESSAGE
def will_send_message(company_name, stock_name, up_down, difference_rounded):
    if abs(difference_rounded) > 1:
        latest_articles = get_latest_articles(company_name, stock_name, up_down, difference_rounded)

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
closing_prices = get_stock_closing_prices(STOCK_NAME)
difference = get_difference(closing_prices)
difference_rounded = round_difference(difference, closing_prices)
up_down = compare_difference(difference)

will_send_message(COMPANY_NAME, STOCK_NAME, up_down, difference_rounded)
