import os
import json
import sys
import requests
from anthropic import Anthropic

# Load credentials from environment
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
WP_USERNAME = os.environ["WP_USERNAME"]
WP_APP_PASSWORD = os.environ["WP_APP_PASSWORD"]
WP_SITE_URL = os.environ["WP_SITE_URL"].rstrip("/")

# The test post we're generating
POST_TOPIC = "Tub-to-Shower Conversion Garland TX"

# Load knowledge base and voice profile
with open("ghp_knowledge_base.json", "r") as f:
    knowledge_base = json.load(f)

with open("ghp_voice_profile.md", "r") as f:
    voice_profile = f.read()

# Build the prompt
system_prompt = f"""You are writing a blog post for Garland Home Pros, a home remodeling company in Garland, TX.

VOICE PROFILE (follow exactly):
{voice_profile}

COMPANY KNOWLEDGE BASE (use only facts from this):
{json.dumps(knowledge_base, indent=2)}

CRITICAL RULES:
- Match the GHP "trustworthy-craftsman" voice, not generic AI voice
- Target 1400-1900 words
- Include specific pricing from the knowledge base
- Reference specific Garland neighborhoods when relevant
- Include an FAQ section with 4-6 questions
- End with a clear CTA including the phone number (469) 518-0206
- Format in clean HTML (use <h2>, <h3>, <p>, <ul>, <li>, <strong>)
- Do NOT use phrases like "In today's world" or "Let's dive in" or "In conclusion"
- Do NOT use em-dashes that feel like AI tells
- Output ONLY the HTML content. No preamble, no explanation, no markdown fences."""

user_prompt = f"""Write a blog post titled: {POST_TOPIC}

The post should cover:
- What a tub-to-shower conversion actually involves (process, waterproofing, time)
- Specific pricing for Garland TX homeowners ($4,000-$12,000 range from knowledge base)
- Why walk-in showers are usually the right call for master baths in Garland
- What can go wrong (waterproofing failures)
- FAQ section
- CTA to call (469) 518-0206 for a free estimate

Output the post body as clean HTML. Start with the first paragraph — no title tag needed, the post title will be handled separately."""

# Call Claude
print("Calling Claude API...")
client = Anthropic(api_key=ANTHROPIC_API_KEY)

response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=4000,
    system=system_prompt,
    messages=[{"role": "user", "content": user_prompt}]
)

post_content = response.content[0].text
print(f"Generated {len(post_content)} characters of content")

# Build the WordPress post payload
post_data = {
    "title": POST_TOPIC,
    "content": post_content,
    "status": "draft",  # DRAFT, not published
    "categories": [],
    "excerpt": "A tub-to-shower conversion in Garland TX: process, pricing ($4K-$12K range), and what homeowners should know before starting."
}

# Push to WordPress
print(f"Pushing to WordPress at {WP_SITE_URL}...")
wp_endpoint = f"{WP_SITE_URL}/wp-json/wp/v2/posts"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

response = requests.post(
    wp_endpoint,
    json=post_data,
    auth=(WP_USERNAME, WP_APP_PASSWORD),
    headers=headers,
    timeout=30
)

if response.status_code in (200, 201):
    post = response.json()
    print(f"SUCCESS — Draft post created")
    print(f"Post ID: {post['id']}")
    print(f"Edit URL: {WP_SITE_URL}/wp-admin/post.php?post={post['id']}&action=edit")
    sys.exit(0)
else:
    print(f"ERROR — WordPress returned {response.status_code}")
    print(f"Response body: {response.text[:500]}")
    sys.exit(1)
