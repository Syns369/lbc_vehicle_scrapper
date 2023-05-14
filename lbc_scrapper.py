import os
import time
import pickle
import undetected_chromedriver as uc
import json
import pgeocode
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def sort_write(filename, key):
    with open("results/vehicle_list.json", "r") as json_file:
        list = json.load(json_file)
        list.sort(key=lambda x: x[key])
    json_object = json.dumps(list, indent=4)
    with open(f"results/{filename}.json", "w") as outfile:
        outfile.write(json_object)


options = Options()
# # Adding argument to disable the AutomationControlled flag
options.add_argument("--disable-blink-features=AutomationControlled")

# # Exclude the collection of enable-automation switches
options.add_experimental_option("excludeSwitches", ["enable-automation"])

# # Turn-off userAutomationExtension
options.add_experimental_option("useAutomationExtension", False)
options.add_argument(f"user-data-dir={os.path.join(os.getcwd(), 'profile')}")
options.add_experimental_option("detach", True)

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), options=options
)

driver.get("https://www.leboncoin.fr/mes-annonces")

time.sleep(1)

# for each data-test-id="price" print the span text
adList = driver.find_elements("xpath", "//a[@data-test-id='ad']")
# priceDict from adList with the @data-test-id='ad' attribute and the ad.get_attribute("href")
vanList = []
for ad in adList:
    # create a dict for each ad
    price = ad.find_element("xpath", ".//p[@data-test-id='price']")
    zipcode = ad.find_element("xpath", ".//p[contains(@aria-label, 'Située à')]")
    link = ad.get_attribute("href")
    vanList.append(
        {
            "price": int(re.sub("[^0-9]", "", price.text)),
            "zipcode": re.sub("[^0-9]", "", zipcode.text),
            "link": link,
        }
    )

for van in vanList:
    # go to the ad
    driver.get(van["link"])
    # find element with data-test-id="criteria_item_km" in the new tab
    km = driver.find_element("xpath", "//div[@data-qa-id='criteria_item_mileage']")
    # ad the km to the priceDict key
    van["km"] = int(re.sub("[^0-9]", "", km.text))
    dist = pgeocode.GeoDistance("fr")
    van["distance"] = dist.query_postal_code("92220", van["zipcode"]).round(0)
    van["note"] = (van["price"] + van["km"] + van["distance"]) / 3
    print(f"price: {van['price']} €")
    print(f"km: {van['km']} km")
    print(f"distance: {van['distance']} km")
    print(f"link: {van['link']}")
    print(f"zipcode: {van['zipcode']}")
    print("------------------")

driver.quit()

print(vanList)

json_object = json.dumps(vanList, indent=4)
# writing to results/vehicle_list.json create intermediate folders if they don't exist

if not os.path.exists("results"):
    os.makedirs("results")

with open("results/vehicle_list.json", "w") as outfile:
    outfile.write(json_object)

# sort the vehicle_list.json by price
sort_write("priceList", "price")

# sort the vehicle_list.json by km
sort_write("kmList", "km")

# sort the vehicle_list.json by distance
sort_write("distanceList", "distance")

# sort the vehicle_list.json by note
sort_write("noteList", "note")

print(f"Done \U0001F44D")
