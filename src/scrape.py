import os
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options

def get_bits_driver_login(driver):
    try:
        element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
    except:
        driver.quit()

    username = driver.find_element_by_name("j_username")
    password = driver.find_element_by_name("j_password")

    username.send_keys("f2015615@pilani.bits-pilani.ac.in")
    password.send_keys("2015B3A40615P")

    driver.find_element_by_name("_eventId_proceed").click()

    try:
        element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "_eventId_proceed"))
        )
    except:
        driver.quit()

    driver.find_element_by_name("_eventId_proceed").click()

    return driver

def get_logged_in_driver():
    options = Options()
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference("browser.download.dir","/home/sameer/Projects/Political-leaning/webscraping")
    options.set_preference("browser.download.useDownloadDir", True)
    options.set_preference("browser.download.viewableInternally.enabledTypes", "")
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
    options.set_preference("pdfjs.disabled", True)
    options.add_argument("--disable-browser-side-navigation")
    driver = webdriver.Firefox(firefox_options=options)

    acm_dl_home_url = "https://dl.acm.org/"
    driver.get(acm_dl_home_url)

    try:
        element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Sign in"))
        )
    except:
        driver.quit()
    driver.find_element_by_link_text("Sign in").click()

    try:
        element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Institutional Login"))
        )
    except:
        driver.quit()
    driver.find_element_by_link_text("Institutional Login").click()

    try:
        element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Select your institution:"))
        )
    except:
        driver.quit()
    driver.find_element_by_link_text("Select your institution:").click()

    try:
        element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "search-box-li"))
        )
    except:
        driver.quit()
    driver.find_element_by_class_name("search-box-li").click()    
    search_box = driver.find_element_by_class_name("search-input")
    search_box.send_keys("BITS Pilani")

    try:
        element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='bits-pilani']"))
        )
    except:
        driver.quit()
    driver.find_element_by_css_selector("a[href*='bits-pilani']").click() 

    return get_bits_driver_login(driver)

if __name__ == "__main__":
    folder_location = r'/home/sameer/Projects/Political-leaning/webscraping'
    if not os.path.exists(folder_location):
        os.mkdir(folder_location)

    driver = get_logged_in_driver()
    print("Driver returned")

    accepted_papers_url = "https://facctconference.org/2020/acceptedpapers.html"
    response_accepted_papers = requests.get(accepted_papers_url)
    accepted_soup = BeautifulSoup(response_accepted_papers.text, "html.parser")  

    i = 0
    """
    sample_url = "https://dl.acm.org/doi/pdf/10.1145/3351095.3372833"
    with open('/home/sameer/Projects/Political-leaning/webscraping/sample', "wb") as f:
        f.write(session.get(sample_url).content)

    driver.get(sample_url)

    """
    for link in accepted_soup.select("a[href*='10.1145']"):
        filename = os.path.join(folder_location, link['href'].split('/')[-1]) 
        pdfLink = link['href'].replace("abs", "pdf")
        print (filename)
        print (i)
        i += 1
        driver.get(pdfLink)
        """
        with open(filename, 'wb') as f:
            f.write(session.get(pdfLink).content)
        """
    print ("Done!")