
# Cleaned up imports
from urllib.parse import urlparse
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
import httpx

app = FastAPI()

# Allow all origis for development (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://job-website-1.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/scrape")
def scrape_jobs(
    section: str = Query(None, description="Section to scrape: hot, newest, barishal, or leave empty for homepage"),
    page: int = Query(1, description="Page number for pagination")
):
    # Determine URL based on section
    if section == "hot":
        url = f"https://bdgovtjob.net/category/hot-jobs/page/{page}/" if page > 1 else "https://bdgovtjob.net/category/hot-jobs/"
    elif section == "newest":
        url = f"https://bdgovtjob.net/page/{page}/?s=&job_category=&deadline=&pub_date=30_days" if page > 1 else "https://bdgovtjob.net/?s=&job_category=&deadline=&pub_date=30_days"
    elif section == "barishal":
        url = f"https://bdgovtjob.net/page/{page}/?s=barishal" if page > 1 else "https://bdgovtjob.net/?s=barishal"
    else:
        url = f"https://bdgovtjob.net/page/{page}/" if page > 1 else "https://bdgovtjob.net/"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        print(f"[DEBUG] Requesting URL: {url}")
        response = httpx.get(url, headers=headers)
        print(f"[DEBUG] Response status: {response.status_code}")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        jobs = []
        for article in soup.find_all("article", class_="post"):
            # Title and link
            h2 = article.find("h2", class_="entry-title")
            title = h2.get_text(strip=True) if h2 else None
            link = h2.find("a")["href"] if h2 and h2.find("a") else None

            # Image
            img_tag = article.find("div", class_="post-image")
            img_url = None
            if img_tag and img_tag.find("img"):
                img_url = img_tag.find("img").get("src")

            # Vacancies
            vacancy_box = article.find("div", class_="job-info-box job-vacancy")
            vacancies = None
            if vacancy_box:
                val = vacancy_box.find("div", class_="job-value")
                vacancies = val.get_text(strip=True) if val else None

            # Deadline
            deadline_box = article.find("div", class_="job-info-box job-deadline")
            deadline = None
            if deadline_box:
                val = deadline_box.find("div", class_="job-value")
                deadline = val.get_text(strip=True) if val else None

            # Publish date
            pub_date = None
            date_box = article.find("div", class_="job-info-box job-publish-date")
            if date_box:
                val = date_box.find("div", class_="job-value")
                pub_date = val.get_text(strip=True) if val else None
            # Fallback: try to find a time tag
            if not pub_date:
                time_tag = article.find("time", class_="entry-date")
                if time_tag:
                    pub_date = time_tag.get_text(strip=True)

            # Short summary
            summary_box = article.find("div", class_="entry-summary")
            summary = summary_box.get_text(strip=True) if summary_box else None

            # Categories
            categories = []
            footer = article.find("footer", class_="entry-meta")
            if footer:
                cat_links = footer.find_all("a", rel="category tag")
                categories = [a.get_text(strip=True) for a in cat_links]

            jobs.append({
                "title": title,
                "link": link,
                "image": img_url,
                "vacancies": vacancies,
                "deadline": deadline,
                "publish_date": pub_date,
                "summary": summary,
                "categories": categories
            })

        return {"url": url, "section": section, "jobs": jobs}
    except Exception as e:
        return {"error": str(e), "url": url, "section": section, "jobs": []}

@app.get("/job_details")
def job_details(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        # Validate URL is from bdgovtjob.net for security
        parsed = urlparse(url)
        if not parsed.netloc.endswith("bdgovtjob.net"):
            return {"error": "Invalid job URL."}
        response = httpx.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract main content
        h2 = soup.find("h2", class_="entry-title")
        title = h2.get_text(strip=True) if h2 else None
        image = None
        img_tag = soup.find("div", class_="post-image")
        if img_tag and img_tag.find("img"):
            image = img_tag.find("img").get("src")
        content_div = soup.find("div", class_="entry-content")
        content_html = str(content_div) if content_div else None
        publish_date = None
        date_box = soup.find("div", class_="job-info-box job-publish-date")
        if date_box:
            val = date_box.find("div", class_="job-value")
            publish_date = val.get_text(strip=True) if val else None
        if not publish_date:
            time_tag = soup.find("time", class_="entry-date")
            if time_tag:
                publish_date = time_tag.get_text(strip=True)
        # Categories
        categories = []
        footer = soup.find("footer", class_="entry-meta")
        if footer:
            cat_links = footer.find_all("a", rel="category tag")
            categories = [a.get_text(strip=True) for a in cat_links]

        return {
            "title": title,
            "image": image,
            "content_html": content_html,
            "publish_date": publish_date,
            "categories": categories,
            "url": url
        }
    except Exception as e:
        return {"error": str(e), "url": url}