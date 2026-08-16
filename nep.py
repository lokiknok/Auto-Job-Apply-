import csv
import time
import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ==========================================
# 1. CONFIGURATION
# ==========================================
NAUKRI_EMAIL = "lohithv0126@gmail.com"
NAUKRI_PASSWORD = "9043871380@l"

TELEGRAM_BOT_TOKEN = "8855459956:AAEQYEvJ38OFDV7AkrfyfsSAGXU0N7eS4aM"
TELEGRAM_CHAT_ID = "6272891729"

SEARCH_URL_KEYWORD = "python"
TARGET_TITLE_MATCH = "python"
MAX_PAGES_TO_SEARCH = 2

MY_DEFAULT_INFO = {
    "full_name": "Your Full Name",
    "email": NAUKRI_EMAIL,
    "phone": "9876543210",
    "experience": "3",
    "notice_period": "15",
    "current_ctc": "8",
    "expected_ctc": "12",
    "city": "Bangalore"
}

# CSV Report Containers
auto_applied_jobs = []
external_applied_jobs = []

# ==========================================
# 2. TELEGRAM NOTIFIERS (TEXT & DOCUMENT)
# ==========================================
def send_telegram_alert(job_title, company, posted_date, url, status="APPLIED"):
    """
    Sends Telegram notifications categorized by application type 
    and displays the job announcement/posted date.
    """
    if "EXTERNAL" in status:
        icon = "🔗"
        header = "*ACTION REQUIRED: APPLY ON COMPANY SITE*"
        instructions = "👇 *Click the link below to manually complete application:*"
    elif "AUTO-APPLIED" in status:
        icon = "✅"
        header = "*AUTO-APPLIED ON NAUKRI*"
        instructions = "⚡ *Application completed automatically.*"
    else:
        icon = "ℹ️"
        header = "*JOB UPDATE*"
        instructions = ""

    message = (
        f"{icon} {header}\n\n"
        f"📌 *Role:* {job_title}\n"
        f"🏢 *Company:* {company}\n"
        f"📅 *Posted:* {posted_date}\n"
        f"⚡ *Status:* {status}\n\n"
        f"{instructions}\n"
        f"🔗 [Direct Job Link]({url})"
    )
    
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        res = requests.post(api_url, data=payload, timeout=5)
        if res.status_code == 200:
            print("   -> [Telegram Alert Delivered]")
        else:
            print(f"   -> [Telegram Error]: Status code {res.status_code}")
    except Exception as e:
        print(f"   -> [Telegram Connection Error]: {e}")

def send_telegram_file(file_path, caption=""):
    """
    Sends a local file (e.g., CSV report) directly to Telegram.
    """
    if not os.path.exists(file_path):
        print(f"   -> [Telegram Error]: File not found: {file_path}")
        return

    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    
    try:
        with open(file_path, "rb") as file_to_send:
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption
            }
            files = {
                "document": file_to_send
            }
            res = requests.post(api_url, data=payload, files=files, timeout=30)
            if res.status_code == 200:
                print(f"   -> [Telegram File Delivered]: {file_path}")
            else:
                print(f"   -> [Telegram File Error]: Status code {res.status_code}")
    except Exception as e:
        print(f"   -> [Telegram File Connection Error]: {e}")

# ==========================================
# 3. NAUKRI INTERNAL QUESTIONNAIRE HANDLER
# ==========================================
def fill_naukri_questionnaire(driver):
    """Answers dynamic questionnaire popups hosted inside Naukri."""
    print("   -> Questionnaire popup detected. Answering questions...")
    max_steps = 5

    for step in range(max_steps):
        time.sleep(2)
        
        # 1. Fill inputs
        inputs = driver.find_elements(By.XPATH, '//input[@type="text" or @type="number" or not(@type)] | //textarea')
        for inp in inputs:
            try:
                if inp.is_displayed() and inp.is_enabled():
                    val = inp.get_attribute("value")
                    if not val:
                        ctx = ((inp.get_attribute("placeholder") or "") + " " + (inp.get_attribute("name") or "")).lower()
                        inp.clear()
                        if "notice" in ctx:
                            inp.send_keys(MY_DEFAULT_INFO["notice_period"])
                        elif "expected" in ctx or "exp ctc" in ctx:
                            inp.send_keys(MY_DEFAULT_INFO["expected_ctc"])
                        elif "current" in ctx or "cur ctc" in ctx:
                            inp.send_keys(MY_DEFAULT_INFO["current_ctc"])
                        elif "location" in ctx or "city" in ctx:
                            inp.send_keys(MY_DEFAULT_INFO["city"])
                        else:
                            inp.send_keys(MY_DEFAULT_INFO["experience"])
            except:
                pass

        # 2. Select radios/checkboxes
        radios = driver.find_elements(By.XPATH, '//input[@type="radio" or @type="checkbox"]')
        for radio in radios:
            try:
                if radio.is_displayed() and not radio.is_selected():
                    driver.execute_script("arguments[0].click();", radio)
            except:
                pass

        # 3. Submit popup step
        action_btns = driver.find_elements(
            By.XPATH, 
            '//button[contains(translate(text(), "SUBMIT", "submit"), "submit") or '
            'contains(translate(text(), "CONTINUE", "continue"), "continue") or '
            'contains(translate(text(), "SAVE", "save"), "save") or '
            'contains(translate(text(), "NEXT", "next"), "next") or '
            'contains(translate(text(), "APPLY", "apply"), "apply")]'
        )
        
        clicked = False
        for btn in action_btns:
            try:
                if btn.is_displayed():
                    driver.execute_script("arguments[0].click();", btn)
                    clicked = True
                    time.sleep(2)
                    break
            except:
                pass

        if not clicked:
            break

# ==========================================
# 4. CORE APPLICATION & ROUTING ENGINE
# ==========================================
def process_job_application(driver):
    """
    Distinguishes between direct Naukri applications and external company site redirects.
    """
    time.sleep(2)

    # 1. Check if already applied
    if driver.find_elements(By.XPATH, '//*[contains(text(),"Already Applied") or contains(text(),"already applied")]'):
        print("   -> Status: Already Applied.")
        return False, "ALREADY APPLIED", driver.current_url

    # 2. Detect "Apply on company site" buttons
    company_site_btns = driver.find_elements(
        By.XPATH, 
        '//button[contains(translate(text(), "COMPANY SITE", "company site"), "company site") or contains(translate(text(), "WEBSITE", "website"), "website")] | '
        '//a[contains(translate(text(), "COMPANY SITE", "company site"), "company site") or contains(translate(text(), "WEBSITE", "website"), "website")]'
    )
    
    if company_site_btns and company_site_btns[0].is_displayed():
        print("   -> Identified: External Company Site Apply button.")
        # Click button to grab final external URL if it opens in a new tab
        driver.execute_script("arguments[0].click();", company_site_btns[0])
        time.sleep(3)
        
        if len(driver.window_handles) > 2:
            driver.switch_to.window(driver.window_handles[-1])
        
        external_url = driver.current_url
        print(f"   -> Redirect Link Captured: {external_url}")
        return True, "EXTERNAL COMPANY SITE (MANUAL APPLY)", external_url

    # 3. Detect Direct Naukri Apply Button
    naukri_apply_xpath = (
        '//button[not(contains(translate(@class, "SAVE", "save"), "save")) and '
        '(normalize-space(text())="Apply" or contains(translate(text(), "APPLY", "apply"), "apply"))] | '
        '//div[contains(@class, "apply-button") and not(contains(@class, "save"))]'
    )

    apply_candidates = driver.find_elements(By.XPATH, naukri_apply_xpath)
    
    valid_apply_btn = None
    for btn in apply_candidates:
        try:
            btn_text = btn.text.strip().lower()
            if "save" not in btn_text and "bookmark" not in btn_text and btn.is_displayed():
                valid_apply_btn = btn
                break
        except:
            continue

    if valid_apply_btn:
        print(f"   -> Found Direct Naukri Apply Button: '{valid_apply_btn.text.strip()}'")
        driver.execute_script("arguments[0].click();", valid_apply_btn)
        time.sleep(3)

        # Handle questionnaire if opened
        drawers = driver.find_elements(By.XPATH, '//div[contains(@class,"drawer") or contains(@class,"chat") or contains(@class,"modal") or contains(@class,"tuple")]')
        if drawers:
            fill_naukri_questionnaire(driver)

        return True, "AUTO-APPLIED ON NAUKRI", driver.current_url

    print("   -> Status: Skipped. No apply button matched.")
    return False, "NO APPLY BUTTON FOUND", driver.current_url

# ==========================================
# 5. CSV REPORT GENERATOR & TELEGRAM DISPATCHER
# ==========================================
def save_and_send_csv_reports(auto_list, external_list):
    """Exports structured data to two CSV files and sends them to Telegram."""
    headers = ["Job Title", "Company", "Posted Date", "URL", "Status"]

    auto_filename = "naukri_auto_applied_report.csv"
    external_filename = "naukri_external_apply_report.csv"

    # 1. Write Direct Auto-Applied Report
    with open(auto_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        for job in auto_list:
            writer.writerow([job["title"], job["company"], job["posted"], job["url"], job["status"]])

    # 2. Write External Company Site Report
    with open(external_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        for job in external_list:
            writer.writerow([job["title"], job["company"], job["posted"], job["url"], job["status"]])

    print("\n==========================================")
    print("      CSV REPORTS GENERATED SUCCESSFULLY   ")
    print("==========================================")
    print(f"1. Direct Auto-Applied CSV : {auto_filename} ({len(auto_list)} entries)")
    print(f"2. External Apply CSV      : {external_filename} ({len(external_list)} entries)")

    # 3. Send CSV files to Telegram
    print("\nSending CSV reports to Telegram...")
    if auto_list:
        send_telegram_file(auto_filename, caption=f"📊 *Auto-Applied Jobs Report* ({len(auto_list)} entries)")
    else:
        print("   -> Auto-Applied CSV is empty. Skipping Telegram upload.")

    if external_list:
        send_telegram_file(external_filename, caption=f"🔗 *External Apply Jobs Report* ({len(external_list)} entries)")
    else:
        print("   -> External Apply CSV is empty. Skipping Telegram upload.")

# ==========================================
# 6. MAIN AUTOMATION RUNNER
# ==========================================
driver = webdriver.Chrome()
driver.maximize_window()
wait = WebDriverWait(driver, 8)

try:
    print("Logging into Naukri...")
    driver.get("https://www.naukri.com/nlogin/login")
    
    wait.until(EC.presence_of_element_located((By.ID, "usernameField"))).send_keys(NAUKRI_EMAIL)
    driver.find_element(By.ID, "passwordField").send_keys(NAUKRI_PASSWORD)
    driver.find_element(By.XPATH, '//button[@type="submit"]').click()
    time.sleep(5)

    for page in range(1, MAX_PAGES_TO_SEARCH + 1):
        print(f"\n--- Scanning Page {page} ---")
        driver.get(f"https://www.naukri.com/{SEARCH_URL_KEYWORD}-jobs-{page}")
        time.sleep(4)

        job_cards = driver.find_elements(By.CSS_SELECTOR, "div.srp-jobtuple-wrapper")
        if not job_cards:
            print("No job cards found.")
            break

        for index in range(len(job_cards)):
            try:
                cards = driver.find_elements(By.CSS_SELECTOR, "div.srp-jobtuple-wrapper")
                if index >= len(cards):
                    break
                
                card = cards[index]
                title_elem = card.find_element(By.XPATH, ".//a[contains(@class, 'title')]")
                job_title = title_elem.text
                
                # Extract Company Name
                try:
                    company = card.find_element(By.XPATH, ".//a[contains(@class, 'comp-name')]").text
                except:
                    company = "Unknown Company"

                # Extract Announcement / Posted Date
                try:
                    posted_date = card.find_element(By.XPATH, ".//span[contains(@class, 'type') or contains(@class, 'timestamp') or contains(@class, 'job-post-day')]").text
                except:
                    posted_date = "Recently Posted"

                if TARGET_TITLE_MATCH.lower() not in job_title.lower():
                    continue

                print(f"\nTarget Found: {job_title} at {company} (Posted: {posted_date})")

                # Open job details tab
                job_url = title_elem.get_attribute("href")
                driver.execute_script("window.open(arguments[0], '_blank');", job_url)
                time.sleep(3)

                driver.switch_to.window(driver.window_handles[-1])

                # Process Application Strategy
                should_notify, status_msg, final_url = process_job_application(driver)
                
                # Record to CSV lists & Send Telegram Notification
                job_data = {
                    "title": job_title,
                    "company": company,
                    "posted": posted_date,
                    "url": final_url,
                    "status": status_msg
                }

                if "EXTERNAL" in status_msg:
                    external_applied_jobs.append(job_data)
                    send_telegram_alert(job_title, company, posted_date, final_url, status=status_msg)
                elif "AUTO-APPLIED" in status_msg:
                    auto_applied_jobs.append(job_data)
                    send_telegram_alert(job_title, company, posted_date, final_url, status=status_msg)

                # Return cleanly to main search tab
                while len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[-1])
                    driver.close()
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(1)

            except Exception as e:
                print(f"   -> Exception handled: {e}")
                while len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[-1])
                    driver.close()
                driver.switch_to.window(driver.window_handles[0])
                continue

except Exception as e:
    print(f"Critical execution failure: {e}")
finally:
    driver.quit()
    # Save the dual CSV reports and send them as document attachments on Telegram
    save_and_send_csv_reports(auto_applied_jobs, external_applied_jobs)
    print("\nAutomation task completed cleanly.")