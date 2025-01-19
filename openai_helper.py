from openai import OpenAI
import json
import os

api_key = os.environ.get("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY is not at all set. Check your environment variables.")

client = OpenAI(api_key=api_key)

def get_dynamic_css_selector(html_content):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": f"""
                You are required to identify CSS selectors for extracting specific review-related information 
                from a webpage. Provide the output as a **strict JSON object** with no additional comments, 
                explanations, or formatting. The JSON object must contain the following keys:
                - `title`: CSS selector for review titles
                - `body`: CSS selector for review bodies
                - `rating`: CSS selector for review ratings (and detailed logic if required, such as counting 'on' or 'filled' stars).
                - `reviewer`: CSS selector for reviewer names
                - `pagination`: CSS selector for pagination buttons (if available)
                
                If extracting ratings requires analyzing classes like 'on', 'filled', or similar, provide logic in a nested key 
                under `rating` such as "logic".

                If a specific selector is not available, leave its value as an empty string.

                Example format:
                {{
                    "title": ".review-title-class",
                    "body": ".review-body-class",
                    "rating": {{
                        "selector": ".rating-class",
                        "logic": "Count child elements with class 'on' or 'filled' to determine the rating."
                    }},
                    "reviewer": ".review-author-class",
                    "pagination": ".pagination-class"
                }}
                
                HTML content:
                {html_content}
                """
            }
        ]
    )

    response_text = completion.choices[0].message.content.strip()

    try:
        selectors = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response from OpenAI: {response_text}\nError: {str(e)}")

    required_keys = ["title", "body", "rating", "reviewer", "pagination"]
    for key in required_keys:
        if key not in selectors:
            raise ValueError(f"Missing key in OpenAI response: {key}")

    return selectors