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
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def download_image(url, save_path):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print("Downloaded:", save_path)
            return True
        else:
            print(f"Failed to download {url}")
            return False
    except Exception as e:
        print(f"Error downloading {url}:", e)
        return False

def scrape_profile(driver, profile_url):
    driver.get(profile_url)
    wait = WebDriverWait(driver, 20)
    
    # Wait for page to fully load
    time.sleep(5)

    try:
        # Try multiple selectors for profile name
        profile_name = None
        name_selectors = [
            "h1.text-heading-xlarge",
            "h1.inline.t-24.v-align-middle.break-words",
            "h1[class*='text-heading']",
            "div.ph5 h1"
        ]
        
        for selector in name_selectors:
            try:
                profile_name = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                ).text
                if profile_name:
                    print(f"Profile Name: {profile_name}")
                    break
            except:
                continue
        
        if not profile_name:
            print("Could not get profile name with any selector")
            profile_name = "unknown_user"
    except Exception as e:
        print("Could not get profile name:", e)
        profile_name = "unknown_user"

    folder_name = profile_name.replace(" ", "_")
    os.makedirs(folder_name, exist_ok=True)

    # Try to get profile image
    try:
        img_url = None
        img_selectors = [
            "img.pv-top-card-profile-picture__image",
            "img.profile-photo-edit__preview",
            "button.pv-top-card-profile-picture img",
            "img[class*='profile-photo']",
            "img[class*='profile-picture']"
        ]
        
        for selector in img_selectors:
            try:
                img_tag = driver.find_element(By.CSS_SELECTOR, selector)
                img_url = img_tag.get_attribute("src")
                if img_url and img_url.startswith("http"):
                    print("Profile photo URL:", img_url)
                    download_image(img_url, os.path.join(folder_name, "profile.jpg"))
                    break
            except:
                continue
        
        if not img_url:
            print("Couldn't find profile image with any selector")
    except Exception as e:
        print("Error getting profile image:", e)

    # Navigate to the Posts/Activity section
    print("\n=== Scraping Posts ===")
    try:
        # Click on "Posts" or "Activity" tab
        activity_selectors = [
            "//a[contains(@href, '/recent-activity/')]",
            "//button[contains(., 'Posts')]",
            "//a[contains(., 'Posts')]",
            "//button[contains(., 'Activity')]"
        ]
        
        activity_button = None
        for selector in activity_selectors:
            try:
                activity_button = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                break
            except:
                continue
        
        if activity_button:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", activity_button)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", activity_button)
            print("Clicked 'Posts/Activity' section")
            time.sleep(5)
        else:
            print("Could not find Posts/Activity section, scrolling to load posts on main profile")
            # Scroll down to load posts on the main profile page
            for _ in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
    except Exception as e:
        print("Error navigating to posts:", e)

    # Scroll to load more posts
    print("Scrolling to load posts...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_attempts = 0
    max_scrolls = 5
    
    while scroll_attempts < max_scrolls:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        scroll_attempts += 1
        print(f"Scrolled {scroll_attempts}/{max_scrolls} times")

    # Extract posts and their content
    print("\n=== Extracting Posts ===")
    try:
        # Find all post containers
        post_selectors = [
            "div.feed-shared-update-v2",
            "div[data-id*='urn:li:activity']",
            "article",
            "div.profile-creator-shared-feed-update__container"
        ]
        
        posts = []
        for selector in post_selectors:
            try:
                posts = driver.find_elements(By.CSS_SELECTOR, selector)
                if posts:
                    print(f"Found {len(posts)} posts using selector: {selector}")
                    break
            except:
                continue
        
        if not posts:
            print("No posts found")
            return
        
        # Create a posts folder
        posts_folder = os.path.join(folder_name, "posts")
        os.makedirs(posts_folder, exist_ok=True)
        
        post_count = 0
        for idx, post in enumerate(posts[:20], 1):  # Limit to first 20 posts
            try:
                print(f"\nProcessing post {idx}...")
                post_folder = os.path.join(posts_folder, f"post_{idx}")
                os.makedirs(post_folder, exist_ok=True)
                
                # Extract post text
                try:
                    text_selectors = [
                        "span.break-words",
                        "div.feed-shared-text",
                        "div.update-components-text",
                        "span[dir='ltr']"
                    ]
                    
                    post_text = ""
                    for text_sel in text_selectors:
                        try:
                            text_elem = post.find_element(By.CSS_SELECTOR, text_sel)
                            post_text = text_elem.text.strip()
                            if post_text and len(post_text) > 10:
                                break
                        except:
                            continue
                    
                    if post_text:
                        with open(os.path.join(post_folder, "post_text.txt"), "w", encoding="utf-8") as f:
                            f.write(post_text)
                        print(f"  Saved post text ({len(post_text)} chars)")
                except Exception as e:
                    print(f"  Could not extract text: {e}")
                
                # Extract images from post
                try:
                    img_elements = post.find_elements(By.CSS_SELECTOR, "img")
                    img_count = 0
                    
                    for img in img_elements:
                        try:
                            src = img.get_attribute("src")
                            if src and "media.licdn.com" in src and not src.endswith(".gif"):
                                # Skip small icons and profile pictures
                                if "profile-displayphoto" in src or "company-logo" in src:
                                    continue
                                
                                save_path = os.path.join(post_folder, f"image_{img_count+1}.jpg")
                                if download_image(src, save_path):
                                    img_count += 1
                        except Exception as e:
                            continue
                    
                    if img_count > 0:
                        print(f"  Downloaded {img_count} image(s)")
                except Exception as e:
                    print(f"  Error extracting images: {e}")
                
                post_count += 1
                
            except Exception as e:
                print(f"  Error processing post {idx}: {e}")
                continue
        
        print(f"\n=== Successfully processed {post_count} posts ===")
        
    except Exception as e:
        print("Error extracting posts:", e)

if __name__ == "__main__":
    load_dotenv()
    LI_AT_COOKIE = os.getenv("LI_AT_COOKIE")

    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    # Optional: run headless
    # chrome_options.add_argument("--headless=new")
    
    # Set Brave browser binary location for macOS
    chrome_options.binary_location = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

    # Let Selenium Manager handle the driver automatically
    driver = webdriver.Chrome(options=chrome_options)

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
            scrape_profile(driver, "https://www.linkedin.com/in/syed-ahmed-a1a3202b1/")

    finally:
        driver.quit()