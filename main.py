# main.py
from urllib.parse import urlparse
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
import httpx

app = FastAPI()

# Allow only your frontend for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://job-website-1.onrender.com",  # frontend URL
        "http://localhost:5500"  # optional for local testing
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/scrape")
def scrape_jobs(
    section: str = Query(None, description="Section to scrape: hot, newest, barishal, or leave empty for homepage"),
    page: int = Query(1, description="Page number for pagination")
):
    if section == "hot":
        url = f"https://bdgovtjob.net/category/hot-jobs/page/{page}/" if page > 1 else "https://bdgovtjob.net/category/hot-jobs/"
    elif section == "newest":
        url = f"https://bdgovtjob.net/page/{page}/?s=&job_category=&deadline=&pub_date=30_days" if page > 1 else "https://bdgovtjob.net/?s=&job_category=&deadline=&pub_date=30_days"
    elif section == "barishal":
        url = f"https://bdgovtjob.net/page/{page}/?s=barishal" if page > 1 else "https://bdgovtjob.net/?s=barishal"
    else:
        url = f"https://bdgovtjob.net/page/{page}/" if page > 1 else "https://bdgovtjob.net/"

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = httpx.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        jobs = []
        for article in soup.find_all("article", class_="post"):
            h2 = article.find("h2", class_="entry-title")
            title = h2.get_text(strip=True) if h2 else None
            link = h2.find("a")["href"] if h2 and h2.find("a") else None

            img_tag = article.find("div", class_="post-image")
            img_url = img_tag.find("img").get("src") if img_tag and img_tag.find("img") else None

            vacancy_box = article.find("div", class_="job-info-box job-vacancy")
            vacancies = vacancy_box.find("div", class_="job-value").get_text(strip=True) if vacancy_box and vacancy_box.find("div", class_="job-value") else None

            deadline_box = article.find("div", class_="job-info-box job-deadline")
            deadline = deadline_box.find("div", class_="job-value").get_text(strip=True) if deadline_box and deadline_box.find("div", class_="job-value") else None

            date_box = article.find("div", class_="job-info-box job-publish-date")
            pub_date = date_box.find("div", class_="job-value").get_text(strip=True) if date_box and date_box.find("div", class_="job-value") else None
            if not pub_date:
                time_tag = article.find("time", class_="entry-date")
                if time_tag: pub_date = time_tag.get_text(strip=True)

            summary_box = article.find("div", class_="entry-summary")
            summary = summary_box.get_text(strip=True) if summary_box else None

            categories = []
            footer = article.find("footer", class_="entry-meta")
            if footer:
                categories = [a.get_text(strip=True) for a in footer.find_all("a", rel="category tag")]

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
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        parsed = urlparse(url)
        if not parsed.netloc.endswith("bdgovtjob.net"):
            return {"error": "Invalid job URL."}
        response = httpx.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        h2 = soup.find("h2", class_="entry-title")
        title = h2.get_text(strip=True) if h2 else None

        img_tag = soup.find("div", class_="post-image")
        image = img_tag.find("img").get("src") if img_tag and img_tag.find("img") else None

        content_div = soup.find("div", class_="entry-content")
        content_html = str(content_div) if content_div else None

        date_box = soup.find("div", class_="job-info-box job-publish-date")
        publish_date = date_box.find("div", class_="job-value").get_text(strip=True) if date_box and date_box.find("div", class_="job-value") else None
        if not publish_date:
            time_tag = soup.find("time", class_="entry-date")
            if time_tag: publish_date = time_tag.get_text(strip=True)

        categories = []
        footer = soup.find("footer", class_="entry-meta")
        if footer:
            categories = [a.get_text(strip=True) for a in footer.find_all("a", rel="category tag")]

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
