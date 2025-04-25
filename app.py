from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import urllib.parse

app = Flask(__name__)

def scrape_jobs(keyword, location):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    except Exception as e:
        return {"error": f"Failed to initialize ChromeDriver: {e}"}

    url = "https://india.recruit.net/"
    all_jobs = {}

    try:
        print("Loading homepage...")
        driver.get(url)
        print("Loaded homepage")

        try:
            keyword_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "query"))
            )
            keyword_input.clear()
            keyword_input.send_keys(keyword)
            print("Filled keyword input")
        except Exception as e:
            return {"error": f"Error filling keyword input: {e}"}

        if location:
            try:
                location_input = driver.find_element(By.NAME, "location")
                location_input.clear()
                location_input.send_keys(location)
                print(f"Filled location input with: {location}")
            except Exception as e:
                return {"error": f"Error filling location input: {e}"}

        try:
            search_button = driver.find_element(By.CLASS_NAME, "btn-search")
            search_button.click()
            print("Clicked search button")
        except Exception as e:
            return {"error": f"Error clicking search button: {e}"}

        max_pages = 5
        current_page = 1

        while current_page <= max_pages:
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span.date.green"))
                )
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(5)
                print(f"Page {current_page} loaded and scrolled")

                soup = BeautifulSoup(driver.page_source, "html.parser")
                print(f"Page Title: {soup.title.text}")

                job_elements = soup.find_all("div", class_="meta")
                if not job_elements:
                    print("No job listings found on this page.")
                    break

                for job in job_elements:
                    link_elem = job.find_parent().find("div", class_="title").find("h2").find("a") if job.find_parent().find("div", class_="title") else None
                    link = link_elem.get("href", str(id(job))) if link_elem else str(id(job))

                    if link not in all_jobs:
                        all_jobs[link] = {
                            "title": "N/A",
                            "company": "N/A",
                            "location": "N/A",
                            "date_posted": "N/A",
                            "description": "N/A",
                            "link": link
                        }

                    title_elem = job.find_parent().find("div", class_="title").find("h2").find("a") if job.find_parent().find("div", class_="title") else None
                    if title_elem and all_jobs[link]["title"] == "N/A":
                        all_jobs[link]["title"] = title_elem.get("title", "N/A")

                    site_span = job.find("span", class_="site")
                    if site_span:
                        a_tags = site_span.find_all("a")
                        if len(a_tags) >= 2:
                            if all_jobs[link]["company"] == "N/A":
                                all_jobs[link]["company"] = a_tags[0].text.strip()
                            if all_jobs[link]["location"] == "N/A":
                                all_jobs[link]["location"] = a_tags[1].text.strip()

                    date_elem = job.find("span", class_="date green")
                    if date_elem and all_jobs[link]["date_posted"] == "N/A":
                        all_jobs[link]["date_posted"] = date_elem.text.strip()

                    description_elem = job.find_parent().find(["p", "div", "span"], class_=lambda x: x and "description" in x.lower()) if job.find_parent() else None
                    if description_elem and all_jobs[link]["description"] == "N/A":
                        all_jobs[link]["description"] = description_elem.text.strip()

                if current_page < max_pages:
                    current_url = driver.current_url
                    params = dict(urllib.parse.parse_qs(urllib.parse.urlparse(current_url).query))
                    params["pageNo"] = str(current_page + 1)
                    new_url = "https://india.recruit.net/search.html?" + urllib.parse.urlencode(params, doseq=True)
                    driver.get(new_url)
                    current_page += 1
                else:
                    break

            except Exception as e:
                print(f"Error processing page {current_page}: {e}")
                break

        jobs_list = list(all_jobs.values())
        job_df = pd.DataFrame(jobs_list)
        csv_path = "job_listings.csv"
        job_df.to_csv(csv_path, index=False, encoding="utf-8")
        return {"jobs": jobs_list, "status": "success"}

    except Exception as e:
        return {"error": f"Error in main block: {e}"}
    finally:
        driver.quit()

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Courses for Careers</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-900 text-white font-sans min-h-screen flex flex-col">
        <!-- Header Section -->
        <header class="bg-gray-800 py-8 text-center">
            <div class="flex justify-center items-center mb-4">
                <img src="https://imgur.com/a/yy0MEmf" alt="Courses for Careers Logo" class="h-16 mr-4">
                <h1 class="text-4xl md:text-5xl font-bold text-teal-400">Courses for Careers</h1>
            </div>
            <p class="text-2xl md:text-3xl font-semibold text-orange-400 italic">"Har Ghar Harvard"</p>
        </header>

        <!-- Main Section with Input Boxes -->
        <main class="flex-grow flex items-center justify-center py-10">
            <div class="max-w-md w-full px-4">
                <h2 class="text-xl md:text-2xl font-semibold text-gray-200 mb-6 text-center">Find Your Dream Job</h2>
                <div class="space-y-4">
                    <!-- Keyword Input -->
                    <div>
                        <label for="keyword" class="block text-sm font-medium text-gray-300 mb-1">Keyword</label>
                        <input type="text" id="keyword" placeholder="e.g., software engineer" class="w-full px-4 py-2 bg-gray-700 text-white border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-400">
                    </div>
                    <!-- Location Input -->
                    <div>
                        <label for="location" class="block text-sm font-medium text-gray-300 mb-1">Location</label>
                        <input type="text" id="location" placeholder="e.g., bangalore" class="w-full px-4 py-2 bg-gray-700 text-white border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-400">
                    </div>
                    <!-- Search Button -->
                    <button onclick="searchJobs()" class="w-full px-4 py-2 bg-teal-500 text-white font-semibold rounded-md hover:bg-teal-600 transition duration-200">Search Jobs</button>
                </div>
                <div id="results" class="mt-6"></div>
            </div>
        </main>

        <!-- Footer -->
        <footer class="bg-gray-800 text-center py-4">
            <p class="text-gray-400">© 2025 Courses for Careers. All rights reserved.</p>
        </footer>

        <script>
            async function searchJobs() {
                const keyword = document.getElementById('keyword').value;
                const location = document.getElementById('location').value;
                const resultsDiv = document.getElementById('results');

                if (!keyword) {
                    resultsDiv.innerHTML = '<p class="text-red-400">Please enter a keyword.</p>';
                    return;
                }

                resultsDiv.innerHTML = '<p class="text-gray-300">Searching...</p>';

                try {
                    const response = await fetch('/search', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ keyword, location })
                    });
                    const data = await response.json();

                    if (data.error) {
                        resultsDiv.innerHTML = `<p class="text-red-400">${data.error}</p>`;
                    } else if (data.jobs) {
                        if (data.jobs.length === 0) {
                            resultsDiv.innerHTML = '<p class="text-yellow-400">No jobs found.</p>';
                        } else {
                            let table = `
                                <h3 class="text-lg font-semibold text-gray-200 mb-2">Job Listings</h3>
                                <div class="overflow-x-auto">
                                    <table class="min-w-full bg-gray-800 shadow-md rounded-lg">
                                        <thead class="bg-gray-700">
                                            <tr>
                                                <th class="py-2 px-4 text-left text-gray-300">Title</th>
                                                <th class="py-2 px-4 text-left text-gray-300">Company</th>
                                                <th class="py-2 px-4 text-left text-gray-300">Location</th>
                                                <th class="py-2 px-4 text-left text-gray-300">Date Posted</th>
                                                <th class="py-2 px-4 text-left text-gray-300">Link</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                            `;
                            data.jobs.forEach(job => {
                                table += `
                                    <tr class="border-t border-gray-600">
                                        <td class="py-2 px-4">${job.title}</td>
                                        <td class="py-2 px-4">${job.company}</td>
                                        <td class="py-2 px-4">${job.location}</td>
                                        <td class="py-2 px-4">${job.date_posted}</td>
                                        <td class="py-2 px-4"><a href="${job.link}" target="_blank" class="text-teal-400 hover:underline">${job.link.length > 50 ? job.link.substring(0, 50) + '...' : job.link}</a></td>
                                    </tr>
                                `;
                            });
                            table += '</tbody></table></div>';
                            resultsDiv.innerHTML = table;
                        }
                    }
                } catch (error) {
                    resultsDiv.innerHTML = '<p class="text-red-400">Error fetching jobs.</p>';
                }
            }
        </script>
    </body>
    </html>
    """

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    keyword = data.get('keyword', '')
    location = data.get('location', '')
    result = scrape_jobs(keyword, location)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)