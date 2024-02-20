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
    # Meetup.com likes to change the html, might have to update this
    event_list = soup.find_all("ul", class_="flex-col")[0]
    events = []
    for event in event_list.children:
        try:
            link = event.find_all("a")[0]['href']
            title = event.find_all("span")[0].string
            datetime = event.find_all("time")[0].contents[0].string
            descriptions = event.find_all("div", class_=re.compile("utils_cardDescription.+"))[0]
            # Limit to the first 4 paragraphs
            description = ''.join(list(descriptions.strings)[:7])
            events.append({
                "link": link,
                "title": title,
                "datetime": datetime,
                "description": description
            })
        except:
            print("Failure while parsing event.")
            print(event.prettify())
            traceback.print_exc()

    # Post new events
    for event in events:
        if event['link'] in past_events:
            continue
        print("New event found, posting...")
        # Cannot post to webhook with over 2000 characters
        event["description"] = event["description"][:1800]
        req = {
            "content": '\n\n'.join([event["title"], event["datetime"], event["description"], event["link"]])
        }
        res = requests.post(PHACK_POST_URL, json=req)
        if res.status_code // 100 != 2:
            print(f"Return Status: {res.status_code}")
            print(res.text)
            return
        print(f"\"{event['title']}\" posted.")
        past_events.append(event['link'])

    json.dump(past_events, open(PHACK_EVENT_FILE, "w"))
    return

def main():
    print(f"{asctime()} : Running Webhook")
    pacific_hackers_webhook()
    return

if __name__ == "__main__":
    main()
