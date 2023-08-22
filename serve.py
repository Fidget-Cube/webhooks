import requests
import dotenv
import os
from bs4 import BeautifulSoup
import re
import json
import traceback
from time import asctime

dotenv.load_dotenv()
TEST_URL = os.getenv("TEST_URL")
PHACK_POST_URL = os.getenv("PHACK_POST_URL")
PHACK_EVENT_FILE = os.getenv("PHACK_EVENT_FILE")

def pacific_hackers_webhook():
    phack_base_url = "https://www.meetup.com"
    phack_scrape_url = "https://www.meetup.com/pacifichackers/events/"
    past_events = json.load(open(PHACK_EVENT_FILE, "r"))

    # Get meetup event
    res = requests.get(phack_scrape_url)
    if res.status_code // 100 != 2:
        print(f"Return Status: {res.status_code}")
        print("Failed to obtain remote posting")
        return
    
    # Parse event details
    soup = BeautifulSoup(res.text, 'html.parser')
    event_list = soup.find_all("ul", class_="eventList-list")[0].find_all("li", class_="list-item")
    events = []
    for event in event_list:
        try:
            link = phack_base_url + event.find_all("a", class_="eventCard--link")[0]['href']
            title = event.find_all("a", class_="eventCardHead--title")[0].string
            date = event.find_all("span", class_="eventTimeDisplay-startDate")[0].contents[0].string
            time = event.find_all("span", class_="eventTimeDisplay-startDate")[1].contents[0].string + " PST"
            descriptions = [desc.contents for desc in event.find_all(class_=re.compile("description-markdown--.+"))]
            description = ""
            for item in descriptions:
                temp = ""
                for i in item:
                    if i.string:
                        temp += i.string
                description += temp + '\n'
            events.append({
                "link": link,
                "title": title,
                "date": date,
                "time": time,
                "description": description
            })
        except:
            print("Failure while parsing event.")
            print(event.prettify())
            traceback.print_exc()

    # Post new events
    for event in events:
        if event in past_events:
            continue
        req = {
            "content": '\n\n'.join([event["title"], event["date"] + ', ' + event["time"], event["description"], event["link"]])
        }
        res = requests.post(PHACK_POST_URL, json=req)
        if res.status_code // 100 != 2:
            print(f"Return Status: {res.status_code}")
            print(res.text)
            return
        past_events.append(event)

    json.dump(past_events, open(PHACK_EVENT_FILE, "w"))
    return

def main():
    print(f"{asctime()} : Running Webhook")
    pacific_hackers_webhook()
    return

if __name__ == "__main__":
    main()
