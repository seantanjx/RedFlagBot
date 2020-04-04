from bs4 import BeautifulSoup as bs
import requests

account_user = 'dadsaysjokes'

source = requests.get("https://twitter.com/" + account_user, timeout=5).text
soup = bs(source, 'lxml')
print(soup.prettify())
