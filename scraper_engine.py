import requests, re
from bs4 import BeautifulSoup


class Scraper(object):
    def __init__(self, link):
        response = requests.get(link)
        if response.status_code == 200:
            self.page = response.content
        else:
            raise requests.ConnectionError("Couldn't connect to that URL.")

    def scrape_page(self, specific_mp=None):
        mp_list = []  # A list of MP objects which will be returned and passed to database possible insert
        soup = BeautifulSoup(self.page, 'html.parser')
        for entry in soup.findAll("tr"):
            cells = entry.findChildren('td')
            name, twitter_username, constituency, party = "", "", "", ""
            for index, cell in enumerate(cells):
                if index == 2:
                    name = cell.getText()

                elif index == 3:
                    twitter_username = cell.getText()

                elif index == 4:
                    constituency = cell.getText()

                elif index == 5:
                    party = cell.getText()

            if name:  # Check for empty entries
                mp = {
                    'name': name.strip(),
                    'party': party,
                    'constituency': constituency,
                    'twitter_username': twitter_username
                }
                mp_list.append(mp)

        return mp_list


