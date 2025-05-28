from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
#  soup.find('a', href=re.compile('.*ukrainian_cities.mp3'), class_='audio-module-listen').parent.parent['data-audio']
# '{"uid":"nx-s1-5411751:nx-s1-5472563-1","available":true,"duration":216,"title":"Russia launches massive drone and missile assaults on Ukrainian cities","audioUrl":"https:\\/\\/ondemand.npr.org\\/anon.npr-mp3\\/npr\\/me\\/2025\\/05\\/20250526_me_russia_launches_massive_drone_and_missile_assaults_on_ukrainian_cities.mp3?size=3470360&d=216863&e=nx-s1-5411751&sc=siteplayer","storyUrl":"https:\\/\\/www.npr.org\\/2025\\/05\\/26\\/nx-s1-5411751\\/russia-launches-massive-drone-and-missile-assaults-on-ukrainian-cities","slug":"Europe","program":"Morning Edition","affiliation":"","song":"","artist":"","album":"","track":0,"type":"segment","subtype":"other","skipSponsorship":false,"hasAdsWizz":false,"isStreamAudioType":false}'
# >>> import json
# >>> audio_data = json.loads(soup.find('a', href=re.compile('.*ukrainian_cities.mp3'), class_='audio-module-listen').pare\
# nt.parent['data-audio'])
# >>> audio_data['uid']
# 'nx-s1-5411751:nx-s1-5472563-1'
# >>> audio_data['title']
# 'Russia launches massive drone and missile assaults on Ukrainian cities'
site = 'https://www.npr.org/programs/morning-edition/2025/05/26/morning-edition-for-may-26-2025'

def get_soup(url: str) -> BeautifulSoup:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # Example: Navigate to a page (replace with actual URL)
        page.goto(url)
        html = page.content()
        soup = BeautifulSoup(html, "lxml")
        # Example: Print the page title
        # print(soup.title.string if soup.title else "No title found.")
        browser.close()
        return soup

def main():
    soup = get_soup(site)

    # Find correspondents
    # Morning edition
    articles = soup.find_all('article', class_='rundown-segment')
    for article in articles:
        byline_p = article.find('p', class_='byline-container--inline')
        if byline_p:
            spans = byline_p.find_all('span', class_='byline byline--inline')
            if len(spans) == 1 and spans[0].get_text(strip=True) != 'Hosts':
                # Do something with articles that have exactly one byline span
                correspondent_name = spans[0].get_text(strip=True)
                audio_url = article.find('a', class_='audio-module-listen', href=re.compile('.*.mp3')).get("href").split('?', 1)[0]
                print(correspondent_name)
                print(audio_url)

    # Find audio url
    # soup.find('article', class_='rundown-segment').find('a', class_='audio-module-listen', href=re.compile('.*.mp3')).get("href")

# each day
# run script to pull all audio segments with correspondents

if __name__ == "__main__":
    main()