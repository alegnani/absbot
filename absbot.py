import time
import os 
import datetime
from datetime import date
import sys
import time
import os

def sanitize_input(inputs):
    lenght = len(inputs)
    if lenght != 4:
        print("Expected 3 parameters, found {}\n\
            Usage:   absbot <hour in 24 hour format> <minute> <lesson id>\n\
            Example: absbot 15 30 295430".format(len(sys.argv) - 1))
        exit()

    try:
        hour = int(inputs[1])
        minute = int(inputs[2])
        lesson_id = int(inputs[3])
    except:
        print("The arguments have to be valid numbers!")
        exit()

    if  hour < 0 or hour > 23:
        print("Expected hour parameter in range [0-23]")
        exit()
    if minute < 0 or minute > 59:
        print("Expected minute parameter in range [0-59]")
        exit()

    try:
        file = open("token")
    except:
        print("No token file found! Creating one...")
        os.popen("touch token")
        exit()
    try:
        file = open("request")
    except:
    	print("Not request file found!Creating one...")
    	os.popen("touch request")
    	exit()
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
    base_req = "curl 'https://schalter.asvz.ch/tn-api/api/Lessons/"
    query = "/enroll??t=" + str(timestamp * 1000 + 1) + "' \\"
    return base_req + str(lesson_id) + query
    
def referer_attribute(lesson_id):
    base_attr = "  -H 'Referer: https://schalter.asvz.ch/tn/lessons/"
    end = "' \\"
    return base_attr + str(lesson_id) + end

def auth_attribute():
    try:
        token = open("token").read().rsplit()[1]
    except:
    	print("Token file is empty!")
    	exit()
    base_attr = "  -H 'Authorization: Bearer "
    end = "' \\"
    return base_attr + str(token) + end

def parse_request(lesson_id, timestamp):
    file = open("request")
    raw_request = file.read()
    file.close()
    splice = raw_request.split("\n")
    splice[0] = link_attribute(lesson_id, timestamp)
    splice[4] = auth_attribute()
    splice[-5] = referer_attribute(lesson_id)
    temp = "\n".join(splice)
    return temp.strip()



hour, minute, lesson_id = sanitize_input(sys.argv)
timestamp = timestamp_unix(hour, minute)
request = parse_request(lesson_id, timestamp)

# print("#" * 32)
# print("Raw request: ")

print(request)
# print("\n + "#" * 32)
# print()



# print("Waiting...")
while time.time() <= timestamp:
    pass

print("huhuhhhhhuhuhuhuh")

stream = os.popen(request)
print(stream.read())
