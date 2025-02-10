from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def google_search_selenium(query):
    """ Searches Google and extracts the featured snippet. """

    # ✅ Set the correct Chrome binary path
    options = Options()
    options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid bot detection

    # ✅ Set the correct ChromeDriver path
    service = Service("/opt/homebrew/bin/chromedriver")  # Use correct path
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(f"https://www.google.com/search?q={query}")

    answer = ""

    try:
        element = driver.find_element("css selector", "b")
        bold_elements = element.find_elements(By.TAG_NAME, "b")
        print(bold_elements)
        for index, bold in enumerate(bold_elements):
            if index < 2:
                answer = element.text.strip()
            
        if answer == "":
            element = driver.find_element("css selector", "dsfaj")
    except Exception as e:
        try:
            element = driver.find_element("css selector", "div.IZ6rdc")
            answer = element.text.strip()
            if answer == "":
                element = driver.find_element("css selector", "dwofjsnif")
        except Exception as e:
            try:
                element = driver.find_element("css selector", "div.PZPZlf.ssJ7i.B5dxMb")
                answer = element.text.strip()
                if answer == "":
                    element = driver.find_element("css selector", "dwofjsnif")
            except Exception as e:
                try:
                    element = driver.find_element("css selector", "div.Z0LcW.t2b5Cf")
                    answer = element.text.strip()
                    if answer == "":
                        element = driver.find_element("css selector", "dwofjsnif")
                except Exception as e:
                    try:
                        element = driver.find_element("css selector", "a.FLP8od")
                        answer = element.text.strip()
                        if answer == "":
                            element = driver.find_element("css selector", "dwofjsnif")
                    except Exception as e:
                        try:
                            element = driver.find_element("css selector", "span.hgKElc")
                            answer = element.text.strip()
                        except Exception as e:
                            print(e)

    driver.quit()
    return answer

query = "When was FRC Crescendo?"
print(google_search_selenium(query))
