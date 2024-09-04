import time
import datetime
from booking.booking import Booking
from selenium.webdriver.chrome.options import Options
from booking.constants import SortingOptions, validate_date
from InquirerPy import inquirer

chrome_options = Options()
chrome_options.add_extension('./Ublock_org.crx')
chrome_options.add_argument("--no-first-run")
chrome_options.add_argument("--disable-search-engine-choice-screen") # search engine choice disabled
chrome_options.add_argument("--no-default-browser-check")
# chrome_options.add_argument("--disable-cache")

if __name__ == "__main__":
    try:
        with Booking(chrome_options=chrome_options) as bot:
            bot.land_first_page()
            bot.change_currency(currency="Dolar amerykański")
            time.sleep(0.5)
            bot.change_language(language="English (US)")
            bot.select_place_to_go(input("Type your place of stay:\n"))
            current_date = datetime.date.today()
            while True:
                check_in_date = input("Type your check-in date: (YYYY-MM-DD):\n").strip()
                valid_check_in = validate_date(check_in_date, curr_date=current_date)
                if valid_check_in:
                    break
            while True:
                check_out_date = input("Type your check-out-date: (YYYY-MM-DD):\n").strip()
                valid_check_out = validate_date(check_out_date, curr_date=current_date, check_in_date=valid_check_in.date())
                if valid_check_out:
                    break
            bot.select_dates(check_in_date, check_out_date) # Select dates
            while True:
                adults_nr = int(input("Type number of adults(from 1 to 30 possible):\n").strip())
                if adults_nr >= 1 and adults_nr <= 30:
                    break
            while True:
                children_nr = int(input("Type number of kids(from 0 to 10 possible):\n").strip())
                if children_nr >= 0 and children_nr <= 10:
                    break
            children_age = []
            while len(children_age) < children_nr:
                child_age = int(input(f"Type age of a kid:\n").strip())
                children_age.append(child_age)
            while True:
                rooms = int(input("Type number of rooms(from 1 to 30 possible):\n").strip())
                if rooms >= 1 and rooms <= 30:
                    break
            with_Pets = None
            with_Pets = inquirer.confirm(
                message="Are you travelling with pets?",
                default=False,
                vi_mode=True,
                mandatory=True,
                mandatory_message="Type (y/Y) if yes or (n/N) if no)."
            ).execute()
            search_results_data = bot.select_adults(adults=adults_nr, children=children_nr, children_ages=tuple(children_age), rooms=rooms, withPets=with_Pets)
            applied_filters = dict() 
            # neigh-25, room-25, property_type-8(size dostosowuje sie do wyszukiwania), hotel_fac-14(size dostosowuje sie do wyszukiwania)
            for key, values in search_results_data.items():
                if '_' in key:
                    words = key.split('_')
                    filter_option = ' '.join(word.capitalize() for word in words)
                else:
                    filter_option = key.capitalize()
                answers = inquirer.checkbox(
                    message=f"Select {filter_option} you're interested in (or press Escape to skip):",
                    choices=values,
                    transformer=lambda result: ", ".join(result),
                    validate=lambda answer: True,
                    vi_mode=True,
                    mandatory=False,
                    keybindings={"skip": [{"key": "escape"}]},
                ).execute()
                applied_filters[key] = answers
            print(f'Applied filters are {applied_filters}')
            sort_option = inquirer.rawlist(
                message="Select your sort option (or press Escape to skip):",
                choices = [
                    SortingOptions.TOP_PICKS_FAMILIES.value,
                    SortingOptions.HOMES_APARTMENTS_FIRST.value,
                    SortingOptions.ASCENDING_PRICES.value,
                    SortingOptions.BEST_REVIEWED_AND_PRICE.value,
                    SortingOptions.PROPERTY_RATING_DESCENDING.value,
                    SortingOptions.PROPERTY_RATING_ASCENDING.value,
                    SortingOptions.PROPERTY_RATING_AND_PRICE.value,
                    SortingOptions.DISTANCE_FROM_DOWNTOWN.value,
                    SortingOptions.TOP_REVIEWED.value,
                ],
                default=1,
                multiselect=False,
                transformer=lambda result: result,
                vi_mode=True,
                mandatory=False,
                keybindings={"skip": [{"key": "escape"}]}
            ).execute()
            print(f'Sort option is {sort_option}')
            bot.apply_filtrations(3, 4, 5, sort_by=sort_option, **applied_filters) # basic filtrations
            time.sleep(1)
            bot.refresh()
            bot.wait_for_results() # Wait for all the results
            # bot.report_data() # Report data about properties
    except Exception as e:
        print("There is a problem running this program from command line interface")

