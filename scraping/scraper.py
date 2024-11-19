from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    ElementClickInterceptedException,
    StaleElementReferenceException
)
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote
from datetime import datetime
import time

class ThreadsScraper:
    
    def __init__(self, base_url, chromedriver):
        self.base_url = base_url
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless=new')

        # Optimize performance
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-extensions')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_argument('--disable-infobars')
        self.chrome_options.add_argument('--ignore-certificate-errors')
        self.chrome_options.add_argument('--disable-logging')
        self.chrome_options.add_argument('--disable-popup-blocking')
        self.chrome_options.add_argument('--enable-automation')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('--start-maximized')
        self.chrome_options.add_argument('--incognito')
        self.chrome_options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
        )

        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option("useAutomationExtension", False)
        self.chrome_options.add_argument('--log-level=3')
        self.driver = webdriver.Chrome(service=Service(chromedriver), options=self.chrome_options)

        # Adjust WebDriver to appear more human
        self.driver.execute_cdp_cmd(
            "Network.setUserAgentOverride",
            {"userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"},
        )
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        self.wait = WebDriverWait(self.driver, 20)
        self.is_logged_in = False
    
    def login(self, username, password):
        """Log into Threads using Instagram credentials with improved error handling"""
        if self.is_logged_in:
            return True

        try:
            # Handle cookies popup
            def handle_cookies():
                try:
                    print("Looking for the Accept Cookies button...")
                    accept_cookies_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//div[text()='Allow all cookies']"))
                    )
                    accept_cookies_button.click()
                    print("Accepted cookies")
                except Exception as e:
                    print(f"Could not find or click the Accept Cookies button: {str(e)}")
                    self.driver.save_screenshot("accept_cookies_error.png")

            # Check if credentials are provided
            if username is None or password is None:
                print("Attempting anonymous access...")
                self.driver.get(self.base_url + "/login/")
                time.sleep(2)
                handle_cookies()

                try:
                    print("Selecting 'Use without a profile'...")
                    use_without_profile_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//a[@href='/nonconsent/']//span[text()='Use without a profile']"))
                    )
                    use_without_profile_button.click()
                    print("Successfully selected 'Use without a profile'")
                    self.is_logged_in = True
                    return True
                except Exception as e:
                    print(f"Failed to select 'Use without a profile': {str(e)}")
                    self.driver.save_screenshot("use_without_profile_error.png")
                    return False

                # Select "Use without a profile"
                try:
                    print("Selecting 'Use without a profile'...")
                    use_without_profile_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//div[text()='Use without a profile']"))
                    )
                    use_without_profile_button.click()
                    print("Successfully selected 'Use without a profile'")
                    self.is_logged_in = True
                    return True
                except Exception as e:
                    print(f"Failed to select 'Use without a profile': {str(e)}")
                    self.driver.save_screenshot("use_without_profile_error.png")
                    return False

            print("Attempting to log in...")
            self.driver.get(self.base_url + "/login/?show_choice_screen=false")
            time.sleep(2)
            handle_cookies()

            # Navigate to the login form
            try:
                login_div = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Log in')]")))
                login_div.click()
                print("Clicked login div, redirecting to login page...")
            except Exception as e:
                print(f"Failed to click the login div: {str(e)}")
                self.driver.save_screenshot("login_div_error.png")
                return False

            # Fill in username
            try:
                print("Waiting for login form...")
                username_input = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Username, phone or email']"))
                )
                print("Found username input")
                username_input.clear()
                username_input.send_keys(username)
                time.sleep(1)
            except Exception as e:
                print(f"Error locating or filling the username input: {str(e)}")
                self.driver.save_screenshot("username_input_error.png")
                return False

            # Fill in password
            try:
                print("Entering password...")
                password_input = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Password']"))
                )
                password_input.clear()
                password_input.send_keys(password + Keys.RETURN)  # Press Enter to submit
                time.sleep(2)
            except Exception as e:
                print(f"Error entering password or submitting form: {str(e)}")
                self.driver.save_screenshot("password_submit_error.png")
                return False

            # Verify login success or detect 2FA
            try:
                print("Checking login success...")
                if self.wait.until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "svg[aria-label='Search']")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "svg[aria-label='Home']")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Search']"))
                    )
                ):
                    print("Login successful!")
                    self.is_logged_in = True
                    return True
            except TimeoutException:
                # Check for 2FA prompt
                try:
                    print("Login not confirmed. Checking for 2FA prompt...")
                    if self.wait.until(
                        EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Security code']"))
                    ):
                        print("2FA detected. Use an account with 2FA disabled for this script.")
                        return False
                except TimeoutException:
                    print("No 2FA prompt detected. Login failed.")
                except Exception as e:
                    print(f"Unexpected error during 2FA detection: {str(e)}")

            # If neither login success nor 2FA detected, assume login failed
            print("Login failed.")
            self.driver.save_screenshot("login_failure.png")
            return False

        except Exception as e:
            print(f"Login failed: {str(e)}")
            self.driver.save_screenshot("login_failed_error.png")
            return False
    
    
    def extract_post_data(self, post_element):
        """Extract data from a post element"""
        try:
            text_element = post_element.find('div', class_='x1a6qonq x6ikm8r x10wlt62 xj0a0fe x126k92a x6prxxf x7r5mf7')
            text = text_element.get_text(strip=True) if text_element else ""
            
            date_element = post_element.find('time')
            date_posted = date_element.get('datetime') if date_element else ""
            
            return {
                "text": text,
                "date_posted": date_posted
            }
        except Exception as e:
            print(f"Error extracting post data: {str(e)}")
            return None

    def extract_reply_data(self, reply_element):
        """Extract data from a reply element including both original post and reply"""
        try:
            # Find all divs that could contain post content
            content_divs = reply_element.find_all('div', class_='x1a2a7pz x1n2onr6')
            
            if len(content_divs) < 2:
                print("Warning: Could not find both original post and reply divs")
                return None
                
            # Extract data from original post (first div)
            original_post_div = content_divs[0]
            original_post_text = original_post_div.find(
                'div', 
                class_='x1a6qonq x6ikm8r x10wlt62 xj0a0fe x126k92a x6prxxf x7r5mf7'
            )
            original_post_date = original_post_div.find('time')
            original_post_author = original_post_div.find('span', class_='x6s0dn4 x78zum5 x1q0g3np') 
            # Extract data from reply (second div)
            reply_div = content_divs[1]
            reply_text = reply_div.find(
                'div', 
                class_='x1a6qonq x6ikm8r x10wlt62 xj0a0fe x126k92a x6prxxf x7r5mf7'
            )
            reply_date = reply_div.find('time')
            
            return {
                "original_post": {
                    "text": original_post_text.get_text(strip=True) if original_post_text else "",
                    "date_posted": original_post_date.get('datetime') if original_post_date else "",
                    "author": original_post_author.get_text(strip=True) if original_post_author else ""
                },
                "reply": {
                    "text": reply_text.get_text(strip=True) if reply_text else "",
                    "date_posted": reply_date.get('datetime') if reply_date else ""
                }
            }
            
        except Exception as e:
            print(f"Error extracting reply data: {str(e)}")
            return None

    def extract_repost_data(self, repost_element):
        """Extract data from a repost element"""
        try:
            text_element = repost_element.find('div', class_='x1a6qonq x6ikm8r x10wlt62 xj0a0fe x126k92a x6prxxf x7r5mf7')
            text = text_element.get_text(strip=True) if text_element else ""
            
            date_element = repost_element.find('time')
            date_posted = date_element.get('datetime') if date_element else ""
            
            original_poster_element = repost_element.find('span', class_='x6s0dn4 x78zum5 x1q0g3np')
            original_poster = original_poster_element.get_text(strip=True) if original_poster_element else ""
            
            return {
                "text": text,
                "date_posted": date_posted,
                "original_poster": original_poster
            }
        except Exception as e:
            print(f"Error extracting repost data: {str(e)}")
            return None

    def scroll_and_collect_content(self, content_type='posts'):
        """Scroll and collect content with progress tracking"""
        print(f"Starting to collect {content_type}...")
        previous_content_count = 0
        same_count_iterations = 0
        max_same_count = 3
        collected_content = {}
        content_index = 1

        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            if content_type == 'posts':
                elements = soup.find_all('div', class_='x78zum5 xdt5ytf')
                for element in elements[len(collected_content):]:
                    post_data = self.extract_post_data(element)
                    if post_data:
                        collected_content[f"post {content_index}"] = post_data
                        content_index += 1
                        
            elif content_type == 'replies':
                elements = soup.find_all('div', class_='x78zum5 xdt5ytf')
                for element in elements[len(collected_content):]:
                    reply_data = self.extract_reply_data(element)
                    if reply_data:
                        collected_content[f"reply {content_index}"] = reply_data
                        content_index += 1
                        
            elif content_type == 'reposts':
                elements = soup.find_all('div', class_='x78zum5 xdt5ytf')
                for element in elements[len(collected_content):]:
                    repost_data = self.extract_repost_data(element)
                    if repost_data:
                        collected_content[f"repost {content_index}"] = repost_data
                        content_index += 1

            current_content_count = len(elements)
            print(f"Found {len(collected_content)} {content_type} so far...")

            if current_content_count == previous_content_count:
                same_count_iterations += 1
                if same_count_iterations >= max_same_count:
                    break
            else:
                same_count_iterations = 0

            previous_content_count = current_content_count
            time.sleep(2)

        return collected_content
        
    def fetch_profile(self, username):
        url = f"{self.base_url}/@{username}"
        profile_data = {
            "username": username,
            "name": "",
            "profile_picture": "",
            "bio": "",
            "followers": "",
            "external_links": "",
            "instagram": "",
            "posts_count": 0,
            "posts": {},
            "replies_count": 0,
            "replies": {},
            "reposts_count": 0,
            "reposts": {}
        }
        self.driver.get(url)
        time.sleep(2)

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')    
        
        name = soup.find('h1', {"dir": "auto"})
        if name:
            profile_data['name'] = name.get_text(strip=True)
        else:
            profile_data['name'] = "Name not found"
        
        
        profile_picture = soup.find('meta',{'property':'og:image'})
        if profile_picture:
            image_url = profile_picture.get('content')
            if image_url:
                profile_data['profile_picture'] = image_url
            else:
                profile_data['profile_picture'] = "Profile picture not found"
        else:
            profile_data['profile_picture'] = "Profile picture not found"
        
        
        bio = self.driver.find_element(By.XPATH, '(//span[@dir="auto"])[4]')
        if bio:
                profile_data['bio'] = bio.text.strip()
        else:
                profile_data['bio'] = "Bio not found"
        
        
        followers = self.driver.find_element(By.XPATH, '(//span[@dir="auto"])[5]')
        if followers:
                profile_data['followers'] = followers.text.strip().replace('followers', '').strip()
        else:
                profile_data['followers'] = "Followers not found"
        
        
        external_links = soup.find_all('link', {"rel": "me"}) 
        if external_links:
                profile_data['external_links'] = [link.get('href') for link in external_links]
        else:
                profile_data['external_links'] = "External links not found"
        
        try:
            instagram = self.driver.find_element(By.XPATH, '//a[contains(@href, "threads.net") and contains(@href, "instagram.com")]')
            if instagram:
                instagram_url = instagram.get_attribute('href')
                if 'u=' in instagram_url:
                    parsed_url = urlparse(instagram_url)
                    query_params = parse_qs(parsed_url.query)
                    instagram_url = query_params.get('u', [None])[0]
                    if instagram_url:
                        profile_data['instagram'] = unquote(instagram_url)
                    else:
                        profile_data['instagram'] = "Instagram URL not found in 'u' parameter"
                else:
                    profile_data['instagram'] = instagram_url
        except Exception as e:
            print(f"Instagram link not found: {str(e)}")
            profile_data['instagram'] = "Instagram link not found"

         # Collect posts
        print("Collecting posts...")
        posts = self.scroll_and_collect_content('posts')
        profile_data["posts"] = posts
        profile_data["posts_count"] = len(posts)

        # Collect replies
        print("Collecting replies...")
        self.driver.get(f"{url}/replies")
        time.sleep(2)
        replies = self.scroll_and_collect_content('replies')
        profile_data["replies"] = replies
        profile_data["replies_count"] = len(replies)

        # Collect reposts
        print("Collecting reposts...")
        self.driver.get(f"{url}/reposts")
        time.sleep(2)
        reposts = self.scroll_and_collect_content('reposts')
        profile_data["reposts"] = reposts
        profile_data["reposts_count"] = len(reposts)

        return {username: profile_data}