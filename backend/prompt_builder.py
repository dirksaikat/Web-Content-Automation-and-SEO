import random

# ---------- Global SEO Instructions ----------
SEO_INSTRUCTIONS = """
Instructions:
- Write an engaging introduction that includes the main keyword.
- Create clear headings and subheadings using H2 and H3 tags.
- Use the reference titles/URLs only as inspiration. Do not copy.
- Include the primary keyword naturally throughout the article (minimum 5 times).
- Use semantic variations of the keyword (LSI keywords).
- Keep the tone informative and helpful.
- Add a short FAQ section with 3–5 common questions related to the topic.
- Conclude with a CTA (call to action) encouraging the reader to take the next step.
- Link out to external resources.
- Add DoFollow links pointing to external resources.
- Add internal links in your content.
- Generate a <meta name="description" content="..."> HTML tag with a 150–160 character summary that starts with the focus keyword.
Target word count: 1000–1200 words.
Write in HTML format (using <h2>, <p>, <ul>, etc.) so it can be published directly to a website.
"""

# ---------- Reference Formatter ----------
def format_refs(refs):
    return "\n".join([f"- {title} ({url})" for title, url in refs])

# ---------- Prompt Templates ----------
# ---------- Informational ----------
def info_prompt_1(k, r): return f"Write an in-depth, SEO-optimized article about '{k}' using these references:\n{format_refs(r)}\n\n{SEO_INSTRUCTIONS}"
def info_prompt_2(k, r): return f"Explain the topic '{k}' in detail with subheadings and sources:\n{format_refs(r)}\n\n{SEO_INSTRUCTIONS}"
def info_prompt_3(k, r): return f"Generate a detailed educational article targeting '{k}' based on:\n{format_refs(r)}\n\n{SEO_INSTRUCTIONS}"
def info_prompt_4(k, r): return f"Create a keyword-optimized blog post on '{k}'. Reference:\n{format_refs(r)}\n\n{SEO_INSTRUCTIONS}"
def info_prompt_5(k, r): return f"You're an expert. Write an informational post on '{k}' using:\n{format_refs(r)}\n\n{SEO_INSTRUCTIONS}"

# ---------- How To ----------
def howto_prompt_1(k, r): return f"Write a step-by-step guide on '{k}' with these sources:\n{format_refs(r)}\n\n{SEO_INSTRUCTIONS}"
def howto_prompt_2(k, r): return f"Create a tutorial on '{k}' for beginners:\n{format_refs(r)}\n\n{SEO_INSTRUCTIONS}"
def howto_prompt_3(k, r): return f"Explain how to do '{k}' step-by-step. Use:\n{format_refs(r)}\n\n{SEO_INSTRUCTIONS}"
def howto_prompt_4(k, r): return f"Teach readers how to accomplish '{k}' using:\n{format_refs(r)}\n\n{SEO_INSTRUCTIONS}"
def howto_prompt_5(k, r): return f"Develop an actionable guide for '{k}'. Reference:\n{format_refs(r)}\n\n{SEO_INSTRUCTIONS}"

# ---------- Listicle ----------
def listicle_prompt_1(k, r): return f"Make a top-10 list blog post on '{k}' using:\n{format_refs(r)}\n\n{SEO_INSTRUCTIONS}"
def listicle_prompt_2(k, r): return f"List key points or items around the topic '{k}'. Sources:\n{format_refs(r)}\n\n{SEO_INSTRUCTIONS}"
def listicle_prompt_3(k, r): return f"Write a listicle article about '{k}' using:\n{format_refs(r)}\n\n{SEO_INSTRUCTIONS}"
def listicle_prompt_4(k, r): return f"Highlight important facts or ideas on '{k}'. Use:\n{format_refs(r)}\n\n{SEO_INSTRUCTIONS}"
def listicle_prompt_5(k, r): return f"Give readers a quick-list blog on '{k}'. Sources:\n{format_refs(r)}\n\n{SEO_INSTRUCTIONS}"

# ---------- Comparison ----------
def comp_prompt_1(k, r): return f"Write a detailed comparison post on '{k}'. Use:\n{format_refs(r)}\n\n{SEO_INSTRUCTIONS}"
def comp_prompt_2(k, r): return f"Compare features, pros and cons of '{k}' with these:\n{format_refs(r)}\n\n{SEO_INSTRUCTIONS}"
def comp_prompt_3(k, r): return f"Create a comparison guide on '{k}' using:\n{format_refs(r)}\n\n{SEO_INSTRUCTIONS}"
def comp_prompt_4(k, r): return f"Write an unbiased comparison blog for '{k}' based on:\n{format_refs(r)}\n\n{SEO_INSTRUCTIONS}"
def comp_prompt_5(k, r): return f"Develop a pros/cons based comparison of '{k}'. Ref:\n{format_refs(r)}\n\n{SEO_INSTRUCTIONS}"

# ---------- Ultimate Guide ----------
def guide_prompt_1(k, r): return f"Create a full ultimate guide on '{k}' using:\n{format_refs(r)}\n\n{SEO_INSTRUCTIONS}"
def guide_prompt_2(k, r): return f"Write a comprehensive long-form post titled 'The Ultimate Guide to {k}'\n{format_refs(r)}\n\n{SEO_INSTRUCTIONS}"
def guide_prompt_3(k, r): return f"Generate an advanced guide on '{k}' based on:\n{format_refs(r)}\n\n{SEO_INSTRUCTIONS}"
def guide_prompt_4(k, r): return f"Teach everything about '{k}' in one article using:\n{format_refs(r)}\n\n{SEO_INSTRUCTIONS}"
def guide_prompt_5(k, r): return f"Make a step-by-step in-depth guide for '{k}' with:\n{format_refs(r)}\n\n{SEO_INSTRUCTIONS}"

# ---------- Prompt Dictionary ----------
PROMPT_BATCHES = {
    "informational": [info_prompt_1, info_prompt_2, info_prompt_3, info_prompt_4, info_prompt_5],
    "howto": [howto_prompt_1, howto_prompt_2, howto_prompt_3, howto_prompt_4, howto_prompt_5],
    "listicle": [listicle_prompt_1, listicle_prompt_2, listicle_prompt_3, listicle_prompt_4, listicle_prompt_5],
    "comparison": [comp_prompt_1, comp_prompt_2, comp_prompt_3, comp_prompt_4, comp_prompt_5],
    "ultimate_guide": [guide_prompt_1, guide_prompt_2, guide_prompt_3, guide_prompt_4, guide_prompt_5],
}

# ---------- Prompt Builder ----------
def build_prompt_by_type(article_type, keyword, titles_urls):
    prompt_func = random.choice(PROMPT_BATCHES.get(article_type, PROMPT_BATCHES["informational"]))
    return prompt_func(keyword, titles_urls)
