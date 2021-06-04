import time
import os 
import datetime
from datetime import date
import sys
import json
from selenium import webdriver
import subprocess

def sanitize_input(inputs):
    lenght = len(inputs)
    if lenght != 4:
        print("Expected 3 parameters, found {}\n\
            Usage:   absbot <hour in 24 hour format> <minute> <lesson id>\n\
            Example: absbot 15 30 295430".format(len(sys.argv) - 1))
        sys.exit()

    try:
        hour = int(inputs[1])
        minute = int(inputs[2])
        lesson_id = int(inputs[3])
    except:
        print("The arguments have to be valid numbers!")
        sys.exit()

    if  hour < 0 or hour > 23:
        print("Expected hour parameter in range [0-23]")
        exit()
    if minute < 0 or minute > 59:
        print("Expected minute parameter in range [0-59]")
        sys.exit()

    try:
        file = open("cmd_request")
    except:
    	print("Not request file found! Creating one...")
    	os.popen("touch request")
    	sys.exit()
    return hour, minute, lesson_id

def timestamp_unix(hour, minute):
    today = date.today()
    local_timezone = datetime.datetime.now().astimezone().tzinfo
    target_time = datetime.datetime(today.year, today.month, today.day, hour=hour, minute=minute, tzinfo=local_timezone)
    timestamp = int(time.mktime(target_time.timetuple()))
    print("Target set to:  {}".format(target_time))
    print("Unix timestamp: {}".format(timestamp))
    return timestamp

def link_attribute(lesson_id, timestamp):
    base_req = 'Invoke-WebRequest -Uri "https://schalter.asvz.ch/tn-api/api/Lessons/'
    query = "/enroll??t=" + str(timestamp * 1000 + 1) + '" `'
    return base_req + str(lesson_id) + query
    
def referer_attribute(lesson_id):
    base_attr = '  "Referer"="https://schalter.asvz.ch/tn/lessons/'
    end = '"'
    return base_attr + str(lesson_id) + end

def auth_attribute():
    token = ""
    try:
        browser = webdriver.Chrome("./chromedriver.exe")
        browser.get('https://schalter.asvz.ch/')
        while(browser.current_url != "https://schalter.asvz.ch/tn/memberships"):
            time.sleep(1)
        time.sleep(1)    
        key = browser.execute_script("return localStorage.key(0)")
        print(f"Key: {key}")
        raw_content = browser.execute_script(f"return localStorage.getItem('{key}')")
        dict_content = json.loads(raw_content)
        token = dict_content['access_token']
        browser.quit()
    except:
        print("Error while retrieving token! :(")
        browser.quit()
        sys.exit()
    base_attr = '  "Authorization"="Bearer '
    end = '"'
    return base_attr + str(token) + end

def parse_request(lesson_id, timestamp):
    file = open("cmd_request")
    raw_request = file.read()
    file.close()
    splice = raw_request.split("\n")
    splice[0] = link_attribute(lesson_id, timestamp)
    splice[5] = auth_attribute()
    splice[12] = referer_attribute(lesson_id)
    temp = "\n".join(splice)
    return temp.strip()

print("Welcome to Absbot")
hour = int(input("Hour of registration start (0-24)"))
minute = int(input("Minute of registration start (0-59)"))
lesson_id = int(input("Id of lesson (xxxxxx)"))

# hour, minute, lesson_id = sanitize_input(sys.argv)
timestamp = timestamp_unix(hour, minute)
request = parse_request(lesson_id, timestamp)
print("Request created")
print(f"Waiting until {hour}:{minute}...")

f = open("req.ps1", "w")
f.write(request)
f.close()

while time.time() <= timestamp:
    pass

print("Sending request")

subprocess.Popen("powershell -ExecutionPolicy Bypass -File req.ps1", shell=True)
time.sleep(1)
f = open("req.ps1", "w")
f.write("")
f.close()
 
try:
    f = open("res")
    lines = f.readlines()
    if "201" in lines[2]:
        print("Operation was successful! :)")
    else:
        print("We were to slow :(, thus no reservation")
    f.close()
except:
    print("Something went wrong :(")
finally:
    f = open("res", "w")
    f.write("")
    f.close()
a = input("Press enter to exit AbsBot")