import os
import csv
import time
import urllib.request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# cài đặt chrome driver
chrome_options = Options()
# duyệt web ở chế độ ẩn danh
chrome_options.add_argument("--incognito")
# khởi động Chorme mà ko hiển thị GUI
#chrome_options.add_argument("--headless")   ko dùng dc
chrome_options.add_argument("--no-sandbox")
#chrome_options.add_argument('--disable-gpu') 
# tắt thông báo đang được chạy bởi phần mềm tự động của google
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
#vô hiệu hóa extension tự động của Selenium
chrome_options.add_experimental_option("useAutomationExtension", False)
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--blink-settings=imagesEnabled=false") 


class GoodReadsScraper:
    """
    Attributes:
        driver (WebDriver): WebDriver được selenium sử dụng, sẽ chỉ được khởi tạo khi cần.
        book_links (danh sách dict): Danh sách chứa url sách, phiếu bầu và điểm lấy từ danh sách GR.
        books (danh sách dict): Danh sách từ điển chứa thông tin sách đã được thu thập.
        broken (danh sách dict): Danh sách các liên kết bị hỏng trong GR, hữu ích để thử thu thập lại.
        list_url (chuỗi): URL của danh sách GR mục tiêu cần thu thập.
        chrome_options (Tùy chọn): Các tùy chọn trình điều khiển được WebDriver sử dụng, bao gồm các chế độ không có giao diện.
        robots_disallow (danh sách chuỗi): Danh sách URL không được phép trong GR robots.txt
    """

    def __init__(self, list_url, driver_options=chrome_options):
        self.driver = ""
        self.book_links = []
        self.books = []
        self.list_url = list_url
        self.chrome_options = driver_options
        self.robots_disallow = self.__get_robots_disallow()

    def __get_title(self):
        title = self.driver.find_element(By.XPATH, '//h1[@class="Text Text__title1"]').text
        return title

    def __get_author(self):
        author = self.driver.find_element(By.XPATH, '//span[@class="ContributorLink__name"]').text
        return author

    def __get_description(self):
        description = self.driver.find_element(By.XPATH, '//span[@class="Formatted"]').text
        return description

    def __get_genres(self):
        label_elements = self.driver.find_elements(By.CLASS_NAME, "BookPageMetadataSection__genreButton")
        genres = [label.text for label in label_elements]
        return genres

    def __get_robots_disallow(self):
        self.driver = webdriver.Chrome(options=self.chrome_options)

        # Lấy những URL bị cấm từ file robot.txt
        try:
            self.driver.get("https://www.goodreads.com/robots.txt")
            robots_disallow = self.driver.find_element(By.XPATH, "//body").text.split("\n")
            robots_disallow = [
                line.replace("Disallow: ", "")
                for line in robots_disallow
                if "Disallow" in line
            ]
        except NoSuchElementException:
            robots_disallow = ""

        self.driver.close()
        return robots_disallow

    def __rem_disallowed_links(self):
        clean_list = []
        for link in self.book_links:
            if (
                link.get("bookUrl")
                .split(".com")[1]
                .split(".")[0]
                .split("_")[0]
                .split("-")[0]
                not in self.robots_disallow
            ):
                clean_list.append(link)
        return clean_list

    def links_to_csv(self, file):
        if not self.book_links:
            print("No book links to save.")
            return
        keys = self.book_links[0].keys()

        with open(file, "w") as f:
            csv_writer = csv.DictWriter(f, keys, quoting=csv.QUOTE_NONNUMERIC)
            csv_writer.writeheader()
            csv_writer.writerows(self.book_links)

    def csv_to_links(self, file):
        self.book_links = []
        with open(file, "rt") as f:
            csv_reader = csv.DictReader(f, quoting=csv.QUOTE_NONNUMERIC)
            for row in csv_reader:
                self.book_links.append(row)

    def books_to_csv(self, file):
        if not self.books:
            print("no book")
            return
        keys = self.books[0].keys()

        with open(file, "w") as f:
            csv_writer = csv.DictWriter(f, keys, quoting=csv.QUOTE_NONNUMERIC)
            csv_writer.writeheader()
            csv_writer.writerows(self.books)

    def csv_to_books(self, file):
        self.books = []
    
        with open(file, "rt") as f:
            csv_reader = csv.DictReader(f, quoting=csv.QUOTE_NONNUMERIC)
            for row in csv_reader:
                self.books.append(row)

    #lấy các link sách
    def get_book_links(self):
        start_time = time.time()
        driver = webdriver.Chrome(options=self.chrome_options)
        #driver = webdriver.Chrome()
        # lấy số lượng page
        driver.get(str(self.list_url))
        page = driver.find_elements(By.XPATH, '//div[@class="pagination"]//a')
        pages =  [link.get_attribute('href') for link in page]
        if len(pages) != 0:
            pages = len(pages) - 2
        else:
            pages = 1

        for page in range(1, pages + 1):
            if page % 10 == 0:
                print("Retrieving links on page " + str(page))

            # mở trang mục tiêu
            if page != 1:
                driver.get(str(self.list_url) + "?page=" + str(page))
    
            # lấy link của các sách trong page hiện tại
            book_titles = driver.find_elements(By.CLASS_NAME, "bookTitle")
          
            for i in range(len(book_titles)):  
                book_info = {"bookUrl": book_titles[i].get_attribute("href")}
                self.book_links.append(book_info)
                
        # Lưu link vào file csv
        self.links_to_csv("links_" + str(self.list_url.split("/")[-1]) + ".csv")
        end_time = time.time()
        print("--- %s seconds ---" % (round(end_time - start_time, 2)))
        driver.close()

    def get_books(self, start_=0, end_=0):
        start_time = time.time()
        # Ko lấy dữ liệu từ những link bị cấm
        self.book_links = self.__rem_disallowed_links()

        if end_ > len(self.book_links) or end_ == 0:
            end_ = len(self.book_links)
        self.driver = webdriver.Chrome(options=self.chrome_options)

        for i in range(start_, end_):
            # truy cập vào url của sách
            self.driver.get(self.book_links[i].get("bookUrl"))

            # in ra vào tiến trình
            if i % 500 == 0:
                print(i)
            elif i % 100 == 0:
                print(
                    " " + str(int((i - start_) * 100 / (end_ - start_))) + "% ", end=""
                )
            elif i % 10 == 0:
                print(".", end="")

            # thử lại 10 lần khi xảy ra lỗi trang
            for attempt in range(10):
                try:
                    title = self.__get_title()
                except NoSuchElementException:
                    print("\n ooops, try: " + str(i))
                    time.sleep(20 + attempt ** 2 * 20)
                else:
                    break
            else:
                print("Cannot finish scraping, saving progress.")
                self.books_to_csv("books_" + str(start_) + "_" + str(i - 1) + ".csv")
                self.links_to_csv("broken_links_" + str(i - 1) + ".csv")

            # tạo thông tin sách
            book = {
                "title": title,
                "author": self.__get_author(),
                "description": self.__get_description(),
                "genres": self.__get_genres()
            }
            self.books.append(book)

            # Partial save
            if i % 10 == 0:
                self.books_to_csv(
                    "partial_book_scrape_" + str(start_) + "_" + str(end_) + ".csv"
                )
                self.links_to_csv(
                    "partial_broken_links_" + str(start_) + "_" + str(end_) + ".csv"
                )

        # lưu các sách vừa crawl đc vào một file
        self.books_to_csv(
            "books_"
            + str(self.list_url.split("/")[-1])
            + "_"
            + str(start_)
            + "_"
            + str(end_)
            + ".csv"
        )
        if len(self.broken) != 0:
            self.links_to_csv(
                "broken_links_"
                + str(self.list_url.split("/")[-1])
                + "_"
                + str(start_)
                + "_"
                + str(end_)
                + ".csv"
            )

        # xoá các file chưa hoàn thiện
        os.remove("partial_book_scrape_" + str(start_) + "_" + str(end_) + ".csv")
        os.remove("partial_broken_links_" + str(start_) + "_" + str(end_) + ".csv")

        end_time = time.time()
        print("--- %s seconds ---" % (round(end_time - start_time, 2)))
        self.driver.close()

  