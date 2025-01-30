import requests
import os
from bs4 import BeautifulSoup
import re
import json
import traceback
from time import asctime
from datetime import datetime

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PHACK_EVENT_FILE = "past_events.json"

def get_pacific_hackers_events():
    phack_scrape_url = "https://www.meetup.com/pacifichackers/events/"

    # Get meetup event
    res = requests.get(phack_scrape_url)
    if res.status_code // 100 != 2:
        print(f"Return Status: {res.status_code}")
        print("Failed to obtain remote posting")
        return
    
    # Parse event details
    soup = BeautifulSoup(res.text, 'html.parser')
    # All the event details are stored in a json script below the html... what????
    souper = soup.find_all("script", id="__NEXT_DATA__", type="application/json")
    if len(souper) == 0:
        print("Failed to drink the soup! '__NEXT_DATA__' script was not found.")
        return
    json_soup = json.loads(souper[0].string)

    events = []
    for state_type, val in json_soup["props"]["pageProps"]["__APOLLO_STATE__"].items():
        if "Event" not in state_type:
            continue
        # Loop through every single event in the json
        try:
            events.append({
                "id": val["id"],
                "link": val["eventUrl"],
                "title": "## " + val["title"],
                "datetime": "### " + datetime.fromisoformat(val["dateTime"]).strftime('%a %d %b %Y, %I:%M%p'),
                "description": '\n\n'.join(val["description"].split('\n\n')[:6])    # Only keep the first 6 paragraphs
            })
        except:
            print("Failure while parsing event.")
            print(json.dumps(val, indent=4))
            traceback.print_exc()
    
    return events
    

def post_to_discord(events):
    if os.path.exists(PHACK_EVENT_FILE):
        past_events = json.load(open(PHACK_EVENT_FILE, "r"))
    else:
        past_events = []
    
    # Post new events
    for event in events:
        if event["id"] in past_events:
            continue
        print("New event found, posting...")
        # Cannot post to webhook with over 2000 characters
        event["description"] = event["description"][:1800]
        req = {
            "content": '\n'.join([event["title"], event["datetime"], event["description"], event["link"]])
        }
        res = requests.post(WEBHOOK_URL, json=req)
        if res.status_code // 100 != 2:
            print(f"Return Status: {res.status_code}")
            print(res.text)
            return
        print(f"\"{event['title']}\" posted.")
        past_events.append(event["id"])

    json.dump(past_events, open(PHACK_EVENT_FILE, "w"))
    return


def main():
    print(f"{asctime()} : Getting Event Info")
    event_data = get_pacific_hackers_events()
    print(f"{asctime()} : Posting Event data to Discord")
    post_to_discord(event_data)
    return

if __name__ == "__main__":
    main()
