from enum import Enum
import datetime
import re

BASE_URL = "https://www.booking.com/index.pl.html"
IMPLICIT_TIME = 15
RESULTS_PER_CALL = 25

class SortingOptions(Enum):
    TOP_PICKS_FAMILIES = "Top picks for families"
    HOMES_APARTMENTS_FIRST = "Homes & apartments first"
    ASCENDING_PRICES = "Price (lowest first)"
    BEST_REVIEWED_AND_PRICE = "Best reviewed & lowest price"
    PROPERTY_RATING_DESCENDING = "Property rating (high to low)"
    PROPERTY_RATING_ASCENDING = "Property rating (low to high)"
    PROPERTY_RATING_AND_PRICE = "Property rating and price"
    DISTANCE_FROM_DOWNTOWN = "Distance from downtown"
    TOP_REVIEWED = "Top reviewed"

def validate_date(date_str, **kwargs):
    try:
        valid_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        if 'curr_date' in kwargs:
            curr_date = kwargs['curr_date']
            if check_date_correctness(curr_date, valid_date) is False:
                print(f"Date {date_str} is not correct. Current date is {curr_date}.")
                return None
        if 'check_in_date' in kwargs:
            check_in_date = kwargs['check_in_date']
            if check_date_correctness(check_in_date, valid_date.date()) is False:
                print(f"Check-out date: {valid_date.date()} is not correct given the check-in date: {check_in_date}.")
                return None
        return valid_date
    except ValueError:
        print(f"Invalid date format or date: {date_str}. Please use the format YYYY-mm-dd.")
        return None
    
def check_date_correctness(curr_date:datetime, received_date:datetime):
    if curr_date.year > received_date.year: # Year check
        return False
    if curr_date.month > received_date.month and curr_date.year == received_date.year: # Months check
        return False
    if curr_date.month == received_date.month and curr_date.year == received_date.year: # Days check
        if curr_date.day > received_date.day:
            return False
    return True

DATA_TO_BE_SCRAPPED = [
    {
        "parent_attr": {"data-filters-group": "di"},
        "items_attr": {"data-filters-item": re.compile(r'^di:di=')},
        "tag_attr": {"data-testid": "filters-group-label-content"},
        "data_name": "neighborhood"
    },
    {
        "parent_attr": {"data-filters-group": "hotelfacility"},
        "items_attr": {"data-filters-item": re.compile(r'^hotelfacility:hotelfacility=')},
        "tag_attr": {"data-testid": "filters-group-label-content"},
        "data_name": "hotel_facilities"
    },
    {
        "parent_attr": {'data-filters-group': "roomfacility"},
        "items_attr": {'data-filters-item': re.compile(r'^roomfacility:roomfacility=')},
        "tag_attr": {'data-testid': "filters-group-label-content"},
        "data_name": "room_facilities"
    },
    {
        "parent_attr": {'data-filters-group': "ht_id"},
        "items_attr": {'data-filters-item': re.compile(r'^ht_id:')},
        "tag_attr": {'data-testid': "filters-group-label-content"},
        "data_name": "properties"
    }
]


