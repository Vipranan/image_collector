import os
import time
import requests
import shutil
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import streamlit as st

def download_image(url, save_path):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
    except Exception:
        pass
    return False

def scrape_linkedin_profile(driver, profile_url, folder):
    wait = WebDriverWait(driver, 10)
    profile_name = "unknown_user"
    folder_name = os.path.join(folder, "LinkedIn")
    os.makedirs(folder_name, exist_ok=True)
    try:
        driver.get(profile_url)
        profile_name = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.text-heading-xlarge"))
        ).text
    except Exception:
        pass

    # Try multiple selectors for the profile image
    img_url = None
    selectors = [
        "img.pv-top-card-profile-picture__image",
        "img.profile-photo-edit__preview",
        "img.pv-top-card-profile-picture__image--show"
    ]
    for selector in selectors:
        try:
            img_tag = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            img_url = img_tag.get_attribute("src")
            if img_url and img_url.startswith("http"):
                break
        except Exception:
            continue
    if img_url:
        download_image(img_url, os.path.join(folder_name, "profile.jpg"))
    with open(os.path.join(folder_name, "profile.txt"), "w", encoding="utf-8") as f:
        f.write(f"Name: {profile_name}\nProfile URL: {profile_url}\n")
    return folder_name

def scrape_substack_profile(name, folder):
    username = name.lower().replace(' ', '').replace('.', '')
    url = f"https://{username}.substack.com"
    folder_name = os.path.join(folder, "Substack")
    os.makedirs(folder_name, exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, "html.parser")
            title = soup.title.text.strip() if soup.title else name
            og_img = soup.find("meta", property="og:image")
            img_url = og_img["content"] if og_img and og_img.get("content") else None
            if not img_url:
                img = soup.find("img")
                img_url = img['src'] if img and img.has_attr('src') else None
            if img_url:
                download_image(img_url, os.path.join(folder_name, "profile.jpg"))
            with open(os.path.join(folder_name, "profile.txt"), "w", encoding="utf-8") as f:
                f.write(f"Title: {title}\nProfile URL: {url}\n")
            return folder_name
    except Exception:
        pass
    return None

def scrape_medium_profile(name, folder):
    username = name.lower().replace(' ', '').replace('.', '')
    url = f"https://medium.com/@{username}"
    folder_name = os.path.join(folder, "Medium")
    os.makedirs(folder_name, exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, "html.parser")
            title = soup.title.text.strip() if soup.title else name
            og_img = soup.find("meta", property="og:image")
            img_url = og_img["content"] if og_img and og_img.get("content") else None
            if not img_url:
                img = soup.find("img")
                img_url = img['src'] if img and img.has_attr('src') else None
            if img_url:
                download_image(img_url, os.path.join(folder_name, "profile.jpg"))
            with open(os.path.join(folder_name, "profile.txt"), "w", encoding="utf-8") as f:
                f.write(f"Title: {title}\nProfile URL: {url}\n")
            return folder_name
    except Exception:
        pass
    return None

def scrape_duckduckgo_profile(name, folder):
    url = f"https://duckduckgo.com/?q={name.replace(' ', '+')}&t=h_&ia=about"
    folder_name = os.path.join(folder, "DuckDuckGo")
    os.makedirs(folder_name, exist_ok=True)
    try:
        r = requests.get(url)
        if r.status_code == 200:
            with open(os.path.join(folder_name, "profile.txt"), "w", encoding="utf-8") as f:
                f.write(f"Search URL: {url}\n")
            return folder_name
    except Exception:
        pass
    return None

def zip_folder(folder_path, zip_path):
    shutil.make_archive(zip_path, 'zip', folder_path)
    return zip_path + ".zip"

def main():
    st.title("Universal Profile Scraper")
    st.write("Enter a name and select platforms to scrape profile info and images. Results are saved in folders you can browse and download.")

    name = st.text_input("Enter Name (LinkedIn/Medium/Substack username):")
    platforms = st.multiselect(
        "Select Platforms",
        ["LinkedIn", "Substack", "Medium", "DuckDuckGo"],
        default=["LinkedIn"]
    )
    scrape_btn = st.button("Scrape Profile")

    if scrape_btn and name.strip():
        main_folder = os.path.join(os.getcwd(), name.replace(" ", "_"))
        if os.path.exists(main_folder):
            shutil.rmtree(main_folder)
        os.makedirs(main_folder, exist_ok=True)
        st.info(f"Scraping profiles for: {name}")

        folders = []
        if "LinkedIn" in platforms:  # If user selected LinkedIn
            load_dotenv()  # Load environment variables from .env file
            LI_AT_COOKIE = os.getenv("LI_AT_COOKIE")  # Get the LinkedIn session cookie
            chrome_options = Options()  # Set up Chrome options for Selenium
            chrome_options.add_argument("--headless=new")  # Run Chrome in headless mode (no GUI)
            chrome_options.add_argument("--disable-gpu")  # Disable GPU (recommended for headless)
            chrome_options.add_argument("--no-sandbox")  # Disable sandbox (for some environments)
            chrome_options.binary_location = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"  # Use Brave browser
            service = Service(ChromeDriverManager().install())  # Set up ChromeDriver
            driver = webdriver.Chrome(service=service, options=chrome_options)  # Start Chrome browser
            try:
                driver.get("https://www.linkedin.com")  # Go to LinkedIn homepage
                time.sleep(2)  # Wait for page to load
                driver.delete_all_cookies()  # Remove any existing cookies
                driver.add_cookie({  # Add the li_at cookie for authentication
                    'name': 'li_at',
                    'value': LI_AT_COOKIE,
                    'domain': '.linkedin.com',
                    'path': '/',
                    'secure': True,
                    'httpOnly': True
                })
                driver.get("https://www.linkedin.com/feed/")  # Go to LinkedIn feed (requires login)
                time.sleep(2)  # Wait for page to load
                # Check if redirected to login page (cookie invalid/expired)
                if "login" in driver.current_url:
                    st.error("Your LinkedIn session cookie (li_at) is invalid or expired. Please update it in your .env file.")
                else:
                    # If cookie is valid, build profile URL and scrape
                    profile_url = f"https://www.linkedin.com/in/{name.lower().replace(' ', '-')}/"
                    folder = scrape_linkedin_profile(driver, profile_url, main_folder)
                    folders.append(folder)
            except Exception as e:
                st.warning(f"LinkedIn scraping failed: {e}")  # Show warning if any error occurs
            finally:
                driver.quit()  # Always close the browser
        if "Substack" in platforms:
            folder = scrape_substack_profile(name, main_folder)
            if folder:
                folders.append(folder)
        if "Medium" in platforms:
            folder = scrape_medium_profile(name, main_folder)
            if folder:
                folders.append(folder)
        if "DuckDuckGo" in platforms:
            folder = scrape_duckduckgo_profile(name, main_folder)
            if folder:
                folders.append(folder)

        if folders:
            st.success("Scraping complete!")
            zip_path = zip_folder(main_folder, main_folder)
            with open(zip_path, "rb") as f:
                st.download_button(
                    label="Download All Profiles as ZIP",
                    data=f.read(),  # Read file into memory
                    file_name=os.path.basename(zip_path),
                    mime="application/zip"
                )
            st.write("Browse your profile images below:")
            for folder in folders:
                st.write(f"**{os.path.basename(folder)}**")
                for file in os.listdir(folder):
                    file_path = os.path.join(folder, file)
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                        st.image(file_path, caption=file)
        else:
            st.error("No profiles found or scraping failed.")

if __name__ == "__main__":
    main()