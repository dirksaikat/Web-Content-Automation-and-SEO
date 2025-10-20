# app/routes.py
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from bs4 import BeautifulSoup
import re

# ✅ use relative imports (recommended when inside a package)
from scraper import scrape_google_results
from prompt_builder import build_prompt_by_type
from chatgpt_api import get_chatgpt_response
from db import store_serp_results, save_article, setup_database
from wp_publisher import publish_to_wordpress, inject_meta_tags, upload_image_to_wordpress
from image_fetcher import fetch_image_for_paragraph


router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    # Renders templates/index.html (same behavior as Flask's render_template)
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/", response_class=HTMLResponse)
def generate_article(
    request: Request,
    keyword: str = Form(...),
    article_type: str = Form(...),
):
    setup_database()

    # Step 1: Scrape Google
    results = scrape_google_results(keyword)
    store_serp_results(keyword, results)

    # Step 2: Generate content
    prompt = build_prompt_by_type(article_type, keyword, results)
    prompt += '\n\nAlso include a <meta name="description" content="..."> tag.'
    content = get_chatgpt_response(prompt)

    # Step 3: Extract meta description
    meta_description = ""
    meta_match = re.search(
        r'<meta name=["\']description["\'] content=["\'](.+?)["\']\s*/?>',
        content,
        re.IGNORECASE,
    )
    if meta_match:
        meta_description = meta_match.group(1).strip()

    # Step 4: Clean HTML
    content = re.sub(r"```(?:html)?\n?(.*?)```", r"\1", content, flags=re.DOTALL).strip()
    soup = BeautifulSoup(content, "html.parser")

    # Step 5: Title
    h1_tag = soup.find("h1")
    if h1_tag:
        post_title = h1_tag.get_text().strip()
        if keyword.lower() not in post_title.lower():
            post_title = f"{keyword.title()} – {post_title}"
        h1_tag.decompose()
    else:
        post_title = keyword.title()

    # Step 6: Remove noise
    for tag in soup(["head", "style", "script"]):
        tag.decompose()

    # Step 7: Wrap loose text in <p>
    for el in soup.find_all():
        if el.name is None and el.string and el.string.strip():
            new_tag = soup.new_tag("p")
            new_tag.string = el.string.strip()
            el.replace_with(new_tag)

    # Step 8: Style tags
    style_map = {
        "h1": "font-size: 2.25rem; line-height: 1.2; font-weight: bold;",
        "h2": "font-size: 1.875rem; line-height: 1.3; font-weight: bold;",
        "h3": "font-size: 1.5rem; line-height: 1.4; font-weight: bold;",
        "h4": "font-size: 1.25rem; line-height: 1.5; font-weight: bold;",
        "p": "font-size: 1.125rem; line-height: 1.75;",
    }
    for tag_name, style in style_map.items():
        for tag in soup.find_all(tag_name):
            tag["style"] = style

    # Step 9: Fallback meta description
    if not meta_description:
        first_para = soup.find("p")
        if first_para:
            intro = first_para.get_text().strip()
            cleaned_intro = re.sub(r"^[^a-zA-Z0-9]+", "", intro)
            meta_description = (
                cleaned_intro[:160]
                if cleaned_intro.lower().startswith(keyword.lower())
                else f"{keyword}. {cleaned_intro}"[:160]
            )
        else:
            meta_description = f"{keyword} helps businesses automate processes and grow."

    # Step 10: Emphasize keyword intro
    first_para = soup.find("p")
    if first_para and keyword.lower() not in first_para.get_text().lower():
        new_intro = soup.new_tag("p")
        new_intro.string = keyword
        first_para.insert_before(new_intro)

    # Step 11: Insert SEO-optimized images per paragraph
    paragraphs = soup.find_all("p")
    for para in paragraphs:
        query = para.get_text().strip()
        if not query:
            continue

        image_url = fetch_image_for_paragraph(query)
        if image_url:
            img_tag = soup.new_tag("img", src=image_url, alt=query)
            img_tag["style"] = "margin: 1rem 0; max-width: 100%; height: auto;"
            para.insert_after(img_tag)

    # Final content
    formatted_html = str(soup)
    save_article(keyword, post_title, meta_description, formatted_html)

    # Publish
    post_slug = keyword.lower().replace(" ", "-")
    post_id = publish_to_wordpress(post_title, formatted_html, status="draft", slug=post_slug)

    # Meta
    if post_id:
        inject_meta_tags(
            post_id,
            meta_title=post_title,
            meta_description=meta_description,
            meta_keywords=keyword,
        )

    html = f"""
        <h2>✅ Article Generated</h2>
        <p><strong>Post Title:</strong> {post_title}</p>
        <p><strong>Meta Description:</strong> {meta_description}</p>
        <hr><h3>Preview:</h3><div>{formatted_html}</div>
    """
    return HTMLResponse(content=html, status_code=200)
