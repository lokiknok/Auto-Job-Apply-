# Auto-Job-Apply-
An automated Python script that searches Indeed for target roles, auto-applies via "Easily Apply," handles dynamic multi-step forms, extracts external company application links, and delivers real-time job alerts alongside dual CSV reports directly to a Telegram bot. Features undetected Chrome integration to bypass bot detection.
# 🚀 Naukri Automated Job Application System

An intelligent Python automation tool designed to automate job searching and applications on **Naukri.com**. The script handles both direct on-platform applications and external company site redirects, generates structured CSV reports, and sends real-time updates directly to a Telegram bot.

---

## ✨ Features

* **Automated Login & Search:** Authenticates with Naukri and scans job listings based on keywords, experience, and target locations.
* **Smart Application Engine:**
  * **Direct Apply:** Automatically completes multi-step questionnaires (notice period, CTC, experience).
  * **External Redirect Detection:** Identifies external employer sites, captures direct application links, and logs them for manual follow-up.
* **Real-time Telegram Alerts:** Sends instant notifications for applied jobs and external application links.
* **Dual CSV Reporting:** Exports structured reports (`auto_applied.csv` and `external_applied.csv`) and sends them directly to your Telegram chat.
* **Anti-Bot Bypass:** Uses `undetected-chromedriver` to prevent automated browser detection and CAPTCHA triggers.

---

## 🛠️ Tech Stack

* **Language:** Python 3.x
* **Browser Automation:** Selenium, `undetected-chromedriver`
* **Notifications & Data:** Requests, CSV, Telegram Bot API

---

## 📋 Prerequisites

Before running the script, ensure you have Python installed along with the required dependencies:

```bash
pip install undetected-chromedriver selenium requests
