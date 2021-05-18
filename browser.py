from selenium import webdriver
import time
import json

browser = webdriver.Chrome("./chromedriver")
browser.get('https://schalter.asvz.ch/')
while(browser.current_url != "https://schalter.asvz.ch/tn/memberships"):
    time.sleep(1)
key = browser.execute_script("return localStorage.key(0)")
raw_content = browser.execute_script(f"return localStorage.getItem('{key}')")
dict_content = json.loads(raw_content)
print(dict_content['access_token'])
# print(browser.execute_script("return localStorage.getItem(origin_url)"))