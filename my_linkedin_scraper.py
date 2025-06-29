'''

Created on 11 June 2025

@author: S Deepika Sri

source:

'''

import os
import time
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def download_image(url, save_path):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print("Downloaded:", save_path)
        else:
            print(f"Failed to download {url}")
    except Exception as e:
        print(f"Error downloading {url}:", e)

def scrape_profile(driver, profile_url):
    driver.get(profile_url)
    wait = WebDriverWait(driver, 15)

    try:
        profile_name = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.text-heading-xlarge"))
        ).text
        print("Profile Name:", profile_name)
    except Exception as e:
        print("Could not get profile name:", e)
        profile_name = "unknown_user"

    folder_name = profile_name.replace(" ", "_")
    os.makedirs(folder_name, exist_ok=True)

    try:
        img_tag = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "img.profile-photo-edit__preview"))
        )
        profile_img_url = img_tag.get_attribute("src")
        print("Profile photo URL:", profile_img_url)
        download_image(profile_img_url, os.path.join(folder_name, "profile.jpg"))
    except Exception as e:
        print("Couldn't find profile image:", e)

    # Click on the Images tab
    try:
        wait = WebDriverWait(driver, 10)
        images_tab_button = wait.until(EC.presence_of_element_located((
            By.XPATH, "//span[text()='Images']/ancestor::button"
        )))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", images_tab_button)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", images_tab_button)
        print("Clicked 'Images' tab")
        time.sleep(5)
    except Exception as e:
        print("Couldn't click 'Images' tab:", e)
        return

    # Click 'Show all images' link
    try:
        show_all_images_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[.//span[normalize-space()='Show all images']]"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", show_all_images_link)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", show_all_images_link)
        print("Clicked 'Show all images' link")
        time.sleep(5)
    except Exception as e:
        print("Could not click 'Show all images':", e)
        return

    # Now extract images from the new "all images" page
    try:
        image_elements = driver.find_elements(By.CSS_SELECTOR, "ul.display-flex.flex-wrap.list-style-none.justify-flex-start img")
        print(f"Found {len(image_elements)} image(s).")

        for i, img in enumerate(image_elements):
            src = img.get_attribute("src")
            if src and "media.licdn.com" in src:
                save_path = os.path.join(folder_name, f"image_{i+1}.jpg")
                download_image(src, save_path)
    except Exception as e:
        print("Error extracting post images:", e)

if __name__ == "__main__":
    load_dotenv()
    LI_AT_COOKIE = os.getenv("LI_AT_COOKIE")

    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    # Optional: run headless
    # chrome_options.add_argument("--headless=new")

    # Use webdriver-manager to automatically download and use the correct ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Visit domain first
        driver.get("https://www.linkedin.com")
        time.sleep(2)
        driver.delete_all_cookies()

        # Set li_at cookie
        driver.add_cookie({
            'name': 'li_at',
            'value': LI_AT_COOKIE,
            'domain': '.linkedin.com',
            'path': '/',
            'secure': True,
            'httpOnly': True
        })

        # Refresh to apply session
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(3)

        if "login" in driver.current_url:
            print("Login failed or cookie expired.")
        else:
            print("Logged in using li_at cookie.")
            # Scrape profile
            scrape_profile(driver, "https://www.linkedin.com/in/santhosh---v/")

    finally:
        driver.quit()