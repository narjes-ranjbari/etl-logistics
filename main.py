import pandas as pd 
import logging
from sqlalchemy import create_engine
from sqlalchemy.exc import ProgrammingError, OperationalError
from config import url
import requests

logging.basicConfig(
    filename='logistics.log',
    level=logging.INFO
)


def connect_to_db():
    try :
        engine = create_engine(
            "mssql+pyodbc://DESKTOP-7V802UN/logistics?driver=SQL+Server&trusted_connection=yes"
        )
    except OperationalError as e :
        logging.error(f"SQL connection error : {e}")
    logging.info("Connected to database")
    return engine

def read_from_db(engine):
    try:
        customers = pd.read_sql('SELECT * FROM customers', engine)
        logging.info('Fetch data from customers table')
        orders = pd.read_sql('SELECT * FROM orders', engine)
        logging.info('Fetch data from orders table')
    except OperationalError as e :
        logging.error(f"SQL connection error : {e}")
    except ProgrammingError as e :
        logging.error(f'SQL query error : {e}')
    return customers, orders

def read_from_csv(file):
    try:
        df = pd.read_csv(file)
    except FileNotFoundError as e :
        logging.error(f"file not found {e}")
        return None
    except pd.errors.EmptyDataError as e :
        logging.error(e)
        return None
    logging.info('shipping cost file reded')
    return df


def get_rate_from_url(url):
    try :
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        irr_rate = data['rates'].get('IRR')
    except requests.Timeout:
        logging.error('API timeout')
        return None
    except requests.HTTPError as e:
        logging.error(f'HTTP error: {e}')
        return None
    logging.info(f'the exchange rate is {irr_rate}')
    return irr_rate

def filtered_cancelled_orders(orders):
    try :
        orders = orders[orders['status'] != 'cancelled']
    except KeyError as e :
        logging.error(e)
        None
    logging.info("orders filtered out by cancelled")
    return orders

def fill_missing_email(customers):
    try :
        customers['email'] = customers['email'].fillna('unknown@email.com')
    except KeyError as e :
        logging.error(e)
        return None
    logging.info('missing emails filled with unknown@email.com')
    return customers

def merge_sources(customers, orders, shipping_costs):
    try :
        merge1 = customers.merge(orders, left_on='customer_id', right_on='customer_id')
        logging.info('customers tables merged with orders table')
        merge2 = merge1.merge(shipping_costs, left_on='city', right_on='city')
        logging.info('Merged tables merged with shipping_costs data')
    except KeyError as e :
        logging.error(f'Key error : {e}')
    return merge2

def create_new_column_total_cost(merged_data):
    try :
        merged_data['total_cost'] = merged_data['amount'] + merged_data['shipping_cost']
    except KeyError as e :
        logging.error(e)
        return None
    logging.info('new column total_cost added to data')
    return merged_data

def new_column_total_cost_usd(data, irr_rate):
    try :
        data['total_cost_usd'] = data['total_cost'] / irr_rate
    except ZeroDivisionError as e :
        logging.error(e)
        return None
    except KeyError as e :
        logging.error(e)
        return None
    logging.info('new column total_cost added to data')
    return data

def create_month_column(data):
    try :
        data['order_date'] = pd.to_datetime(data['order_date'])
        data['month'] = data['order_date'].dt.month
    except KeyError as e :
        logging.error(e)
        return None
    logging.info('month column added to data')
    return data
    
def group_by_city_report(data):
    try :
        data = data.groupby('city')['total_cost'].sum().reset_index()
        data.columns = ['city', 'total_revenue']
    except KeyError as e :
        logging.error(e)
        return None
    logging.info('total_cost grouped by city')
    return data

def group_by_month_report(data):
    try :
        data = data.groupby('month')['total_cost'].sum().reset_index()
        data.columns = ['month', 'total_revenue']
    except KeyError as e :
        logging.error(e)
        return None
    logging.info('total_cost grouped by month')
    return data
def top_3_customers(data):
    try :
        result = data.sort_values('total_cost', ascending=False).head(3)
    except KeyError as e :
        logging.error(e)
        return None
    logging.info('top 3 customer founded')
    return result[['name', 'total_cost']]

def csv_reports(city_report, top_customers, monthly_report, paths):
    monthly_report.to_csv(paths[2], index=False)
    logging.info(f'monthly_report added to {paths[2]}')
    city_report.to_csv(paths[0], index=False)
    logging.info(f'city_report added to {paths[0]}')
    top_customers.to_csv(paths[1], index=False)
    logging.info(f'top_customers added to {paths[1]}')
    return 'reports file created'


def main():
    csv_file = 'shipping_costs.csv'
    paths = ['city_report.csv', 'top_customers.csv' ,'monthly_report.csv']
    engine = connect_to_db()
    customers, orders = read_from_db(engine)
    shipping_cost = read_from_csv(csv_file)
    irr_rate = get_rate_from_url(url)
    delivered_orders = filtered_cancelled_orders(orders)
    fill_mis_emails = fill_missing_email(customers)
    merged_data = merge_sources(fill_mis_emails, delivered_orders, shipping_cost)
    total_cost = create_new_column_total_cost(merged_data)
    total_cost_usd = new_column_total_cost_usd(total_cost, irr_rate)
    month_column = create_month_column(total_cost_usd)
    group_by_city = group_by_city_report(month_column)
    group_by_month = group_by_month_report(month_column)
    top_3 = top_3_customers(month_column)
    save_to_csv = csv_reports(group_by_city, top_3, group_by_month, paths)
    print(save_to_csv)

main()