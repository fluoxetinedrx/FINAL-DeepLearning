from goodreadsscraper import GoodReadsScraper
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument("--incognito")
#chrome_options.add_argument("--headless")
#chrome_options.add_argument('--disable-gpu') 
chrome_options.add_argument("--no-sandbox")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--blink-settings=imagesEnabled=false")  


list_url = "https://www.goodreads.com/list/show/1?ref=ls_pl_car_0"

if __name__ == '__main__':
    BBE_scraper = GoodReadsScraper(list_url, chrome_options)
    BBE_scraper.get_book_links() 
    BBE_scraper.get_books() 
