import requests
import os
from dotenv import load_dotenv
from base64 import b64encode
from urllib.parse import urlparse
import mimetypes

# Load environment variables
load_dotenv()

WP_SITE = os.getenv("WP_SITE")
WP_USER = os.getenv("WP_USER")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

# Build Auth token
credentials = f"{WP_USER}:{WP_APP_PASSWORD}"
token = b64encode(credentials.encode()).decode("utf-8")

HEADERS = {
    "Authorization": f"Basic {token}",
    "Content-Type": "application/json",
    "User-Agent": "WordPressMetaAgent/1.0"
}

def publish_to_wordpress(title, content, status="draft", slug=None):
    """
    Creates a WordPress post using REST API and returns the post ID.
    """
    url = f"{WP_SITE}/wp-json/wp/v2/posts"
    data = {
        "title": title,
        "content": content,
        "status": status
    }

    if slug:
        data["slug"] = slug

    try:
        response = requests.post(url, headers=HEADERS, json=data, timeout=10)
        if response.status_code == 201:
            print("✅ Post created successfully.")
            return response.json().get("id")
        else:
            print(f"❌ Failed to create post: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print("❌ Exception during post creation:", e)
        return None

def inject_meta_tags(post_id, meta_title=None, meta_description=None, meta_keywords=None):
    """
    Injects SEO meta tags using custom plugin API.
    """
    url = f"{WP_SITE}/wp-json/meta-injector/v1/inject/"
    data = {
        "post_id": post_id,
        "meta_title": meta_title,
        "meta_description": meta_description,
        "meta_keywords": meta_keywords
    }

    try:
        response = requests.post(url, headers=HEADERS, json=data, timeout=10)
        if response.status_code == 200:
            print("✅ Meta tags injected successfully.")
        else:
            print(f"❌ Failed to inject meta tags: {response.status_code}")
            print(response.text)
    except Exception as e:
        print("❌ Exception during meta injection:", e)

def upload_image_to_wordpress(image_url):
    """
    Uploads an image from URL to WordPress and returns new media URL.
    """
    try:
        response = requests.get(image_url, stream=True, timeout=10)
        if response.status_code != 200:
            print(f"❌ Failed to download image: {response.status_code}")
            return None

        # Determine filename
        parsed = urlparse(image_url)
        filename = os.path.basename(parsed.path)
        if not filename:
            filename = "image.jpg"

        # Infer MIME type
        content_type = mimetypes.guess_type(filename)[0] or "image/jpeg"

        # Prepare headers (no Content-Type or Content-Disposition!)
        headers = {
            "Authorization": f"Basic {token}",
            "User-Agent": "Mozilla/5.0"
        }

        files = {
            "file": (filename, response.content, content_type)
        }

        upload_url = f"{WP_SITE}/wp-json/wp/v2/media"
        upload_response = requests.post(upload_url, headers=headers, files=files, timeout=15)

        if upload_response.status_code in [200, 201]:
            image_wp_url = upload_response.json().get("source_url")
            print(f"✅ Image uploaded to WordPress: {image_wp_url}")
            return image_wp_url
        else:
            print(f"❌ Upload failed: {upload_response.status_code}")
            print(upload_response.text)
            return None

    except Exception as e:
        print("❌ Exception during image upload:", str(e))
        return None
