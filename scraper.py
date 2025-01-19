from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import time
from openai_helper import get_dynamic_css_selector
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def wait_for_element(driver, selector, timeout=10):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return element
        except StaleElementReferenceException:
            time.sleep(1)
            continue
    return None

def wait_for_elements(driver, selector, timeout=10):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            elements = WebDriverWait(driver, timeout).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
            )
            return elements
        except StaleElementReferenceException:
            time.sleep(1)
            continue
    return []

def extract_text_safely(element):
    max_retries = 3
    for _ in range(max_retries):
        try:
            return element.text.strip()
        except StaleElementReferenceException:
            time.sleep(1)
        except Exception as e:
            print(f"Error extracting text: {e}")
            return ""
    return ""

def extract_rating(rating_element):
    max_retries = 3
    for _ in range(max_retries):
        try:
            stars = rating_element.find_elements(By.CSS_SELECTOR, '.jdgm-star')
            rating = 0
            for star in stars:
                try:
                    classes = star.get_attribute('class')
                    if 'jdgm--on' in classes:
                        rating += 1
                    elif 'jdgm--half' in classes:
                        rating += 0.5
                except StaleElementReferenceException:
                    continue
            return str(rating) if rating > 0 else "5"
        except StaleElementReferenceException:
            time.sleep(1)
        except Exception as e:
            print(f"Error extracting rating: {e}")
            return "5"
    return "5"

def extract_reviews(url, max_pages=10):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    service = Service('/usr/bin/chromedriver-linux64/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)
    driver.implicitly_wait(10)
    
    try:
        driver.get(url)
        time.sleep(10)
        html_content = driver.page_source
        print("Extracting dynamic CSS selectors using OpenAI...")
        css_selectors = get_dynamic_css_selector(html_content)
        if not css_selectors or not all(key in css_selectors for key in ["title", "body", "rating", "reviewer", "pagination"]):
            raise ValueError("Invalid CSS selectors returned by OpenAI.")
        
        if not css_selectors:
            raise ValueError("Failed to extract CSS selectors from OpenAI.")
        
        print("Using the following CSS selectors:", css_selectors)
        
        reviews = []
        page_number = 1
        max_retries = 3
        
        while page_number <= max_pages:
            print(f"Scraping page {page_number} of maximum {max_pages} pages...")
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    wait_for_element(driver, '.jdgm-rev-widg__reviews')
                    time.sleep(2)
                    review_containers = wait_for_elements(driver, '.jdgm-rev')
                    
                    if not review_containers:
                        print("No reviews found on this page")
                        return {"reviews_count": len(reviews), "reviews": reviews}
                    
                    for container in review_containers:
                        try:
                            title = extract_text_safely(container.find_element(By.CSS_SELECTOR, '.jdgm-rev__title')) if container.find_elements(By.CSS_SELECTOR, '.jdgm-rev__title') else ""
                            body = extract_text_safely(container.find_element(By.CSS_SELECTOR, '.jdgm-rev__body'))
                            reviewer = extract_text_safely(container.find_element(By.CSS_SELECTOR, '.jdgm-rev__author')) if container.find_elements(By.CSS_SELECTOR, '.jdgm-rev__author') else ""
                            
                            if body:
                                rating = extract_rating(container.find_element(By.CSS_SELECTOR, '.jdgm-rev__rating'))
                                
                                reviews.append({
                                    "title": title,
                                    "body": body,
                                    "rating": rating,
                                    "reviewer": reviewer
                                })
                        except (StaleElementReferenceException, NoSuchElementException) as e:
                            print(f"Error processing review: {e}")
                            continue
                    
                    if page_number >= max_pages:
                        print(f"Reached maximum number of pages ({max_pages})")
                        return {"reviews_count": len(reviews), "reviews": reviews}
                    
                    next_buttons = driver.find_elements(By.CSS_SELECTOR, f'.jdgm-paginate__page[data-page="{page_number + 1}"]')
                    if not next_buttons or not any(btn.is_displayed() for btn in next_buttons):
                        print("No next page button found")
                        return {"reviews_count": len(reviews), "reviews": reviews}
                    
                    next_button = next(btn for btn in next_buttons if btn.is_displayed())
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", next_button)
                    
                    time.sleep(3)
                    page_number += 1
                    break
                    
                except Exception as e:
                    print(f"Error on page {page_number}, attempt {retry_count + 1}: {e}")
                    retry_count += 1
                    if retry_count >= max_retries:
                        print("Max retries reached, returning collected reviews")
                        return {"reviews_count": len(reviews), "reviews": reviews}
                    time.sleep(2)
            
    finally:
        driver.quit()