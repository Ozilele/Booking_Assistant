import time
import datetime
from booking.booking import Booking
from selenium.webdriver.chrome.options import Options
from booking.constants import SortingOptions, validate_date, FILTERS_TO_APPLY, DATA_TO_BE_SCRAPPED
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
            bot.select_adults(adults=adults_nr, children=children_nr, children_ages=tuple(children_age), rooms=rooms, withPets=with_Pets)

            while True:
                filter_option = inquirer.select(
                    message="Select filter option you want to apply (or press Escape to skip)",
                    choices=FILTERS_TO_APPLY,
                    default=None,
                    vi_mode=True,
                    mandatory=False,
                    multiselect=False,
                    keybindings={"skip": [{"key": "escape"}]}
                ).execute()
                if filter_option is None or filter_option == []: # No filter option selected
                    break
                if " " in filter_option:
                    parts = filter_option.split(" ")
                    filter_option_key = '_'.join([part.lower() for part in parts])
                else:
                    filter_option_key = filter_option.lower()
                obj = None
                for elem in DATA_TO_BE_SCRAPPED:
                    if elem['data_name'] == filter_option_key:
                        obj = elem
                scrapped_data = bot.scrape_data(obj)
                answers = inquirer.checkbox(
                    message=f"Select {filter_option} you're interested in(toggle choice by pressing space or press Escape to skip)",
                    choices=scrapped_data,
                    transformer=lambda result: ", ".join(result),
                    validate=lambda answer: True,
                    vi_mode=True,
                    mandatory=False,
                    keybindings={"skip": [{"key": "escape"}]},
                ).execute()
                if answers is None or answers == []: # No choice selected
                    continue
                bot.apply_filtration(**{filter_option_key: answers})
                FILTERS_TO_APPLY.remove(filter_option)
                if len(FILTERS_TO_APPLY) == 0:
                    break
            sort_option = inquirer.rawlist(
                message="Select sorting option (or press Escape to skip):",
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
            if sort_option is not None:
                bot.apply_filtration(sort_by=sort_option)
            # time.sleep(1)
            # bot.refresh()
            # bot.wait_for_results() # Wait for all the results
            # bot.report_data() # Report data about properties
    except Exception as e:
        print(f'Error msg: {e.__str__}')
        print("There is a problem running this program from command line interface")

