import sqlite3
from bs4 import BeautifulSoup
from selenium import webdriver
import time

conn = sqlite3.connect("db/test.db")
cur = conn.cursor()
cur.execute(
    "CREATE TABLE IF NOT EXISTS items (id integer PRIMARY KEY, name text, price integer, item_number integer, img_url text, origin_metric text, description text, width text, height text, depth text)")
options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('window-size=1920x1080')
options.add_argument("disable-gpu")
driver = webdriver.Chrome(executable_path="chromedriver.exe", chrome_options=options)
driver.set_page_load_timeout(30)
driver.implicitly_wait(3)


def get_clean_price(soup_price):
    if soup_price and soup_price.text:
        clean_price = soup_price.text.strip()
        raw_price = filter(lambda x: x.isnumeric(), clean_price)
        return "".join(raw_price)


def parse_metric(metric_text):
    metrics = metric_text.split("\n")

    main_metric = {"width": 0, 'height': 0, 'depth': 0}
    for m in metrics:
        if m.find("폭") is 0:
            val = m.replace("폭: ", "")
            main_metric["width"] = val
        elif m.find("깊이") is 0:
            val = m.replace("깊이: ", "")
            main_metric["depth"] = val
        elif m.find("높이") is 0:
            val = m.replace("높이: ", "")
            main_metric["height"] = val
    return main_metric


def crawl_show_page(item_id, queue):
    cur.execute("SELECT * FROM items where id=?", (item_id,))
    rows = cur.fetchall()
    if len(rows) > 0 and len(queue) > 0:
        return list(filter(lambda queue_id: queue_id != item_id, queue))

    path = ("https://www.ikea.com/kr/ko/catalog/products/%s/" % (item_id))

    try:
        driver.get(path)
        time.sleep(2)
    except:
        time.sleep(10)
        print("TIMEOUT")
        return queue

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    try:
        name = soup.find("span", id="name", class_="productName").get_text(strip="true")
        price = soup.find("span", id="price1", class_="packagePrice")
        item_number = soup.find("div", id="itemNumber", class_="floatLeft").get_text(strip="true")
        main_img = soup.find("img", id="productImg").attrs["src"]
        description = soup.find("div", id="custMaterials").get_text(strip="true")
        metric = soup.find("div", id="metric").get_text("\n", strip="true")
        clean_price = get_clean_price(price)
        img_url = "https://www.ikea.com" + main_img
        main_metrics = parse_metric(metric)
        print(name)
    except:
        print("FAILED TO PARSE HTML at ", path)

    try:
        sql = "INSERT OR IGNORE INTO items(id, name, price, item_number, img_url, origin_metric, description, width, height, depth) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        cur.execute(sql, (
            item_id, name, clean_price, item_number, img_url, metric, description, main_metrics["width"],
            main_metrics["height"],
            main_metrics["depth"]), )
        conn.commit()
    except:
        pass

    links = soup.find_all("a")
    for link in links:
        try:
            href = link.attrs["href"]
            if href and ("https://www.ikea.com/kr/ko/catalog/products/" in href):
                trim_left = href.replace("https://www.ikea.com/kr/ko/catalog/products/", "")
                right_index = trim_left.find("/?")
                if right_index > 0:
                    new_id = trim_left[0:right_index]
                    if new_id not in queue:
                        queue.append(new_id)
        except KeyError:
            pass

    left_queue = list(filter(lambda queue_id: queue_id != item_id, queue))
    print("left queue " + str(len(left_queue)))
    print("saved")
    return left_queue


job_queue = []
crawl_show_page("80363426", job_queue)
while len(job_queue) is not 0:
    new_queue = crawl_show_page(job_queue[0], job_queue)
    job_queue = new_queue

driver.quit()
conn.close()
