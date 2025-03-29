import os
import requests
import concurrent.futures


# ------------------------------------------------------------------------------
# 1. Read the blog content from a file
# ------------------------------------------------------------------------------
BLOG_FILE_PATH = "Understanding_blog.txt"  # Example file name
with open(BLOG_FILE_PATH, "r", encoding="utf-8") as f:
    original_blog_text = f.read()

# ------------------------------------------------------------------------------
# 2. Define helper function to call Claude
# ------------------------------------------------------------------------------
def call_claude_api(prompt, api_key, model="claude-v1.3", max_tokens_to_sample=1000):
    """
    Calls the Claude API with the given prompt and returns the text response.
    NOTE: The actual endpoint and request format below may not be correct
          depending on your particular Claude service instance.
          This is just a sample structure.

    :param prompt: The string prompt you want to send to Claude
    :param api_key: Your Claude/Anthropic API key
    :param model: The Claude model you want to use (e.g. 'claude-v1.3')
    :param max_tokens_to_sample: The maximum number of tokens in the response
    :return: The text response from Claude
    """
    url = "https://api.anthropic.com/v1/complete"  # Example endpoint; adapt to your actual one
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "prompt": prompt,
        "model": model,
        "max_tokens_to_sample": max_tokens_to_sample,
        "temperature": 0.7,  # Example
        "stop_sequences": ["\n\nHuman:"],  # Example
    }

    response = requests.post(url, headers=headers, json=data)
    response_json = response.json()

    # The exact JSON structure might differ depending on your setup.
    # Adjust the key below to match your actual Claude response schema.
    return response_json.get("completion", "")


# ------------------------------------------------------------------------------
# 3. Prepare prompts for the three different "reviewer" agents
# ------------------------------------------------------------------------------

# The “core” request: we ask the agent to focus on:
#   (1) any wrong or partially incorrect scientific/technical facts
#   (2) any incorrect wording or awkward syntax
#   (3) whether it aligns with Biostate AI’s brand tone in the ending paragraph
# You could slightly vary the prompt for each reviewer, or keep them identical.
reviewer_prompt_template = """You are a specialized blog content reviewer for Biostate AI.
Below is a blog post. Please perform the following tasks:

1. Identify any wrong or partially incorrect scientific or technical facts.
2. Identify any incorrect wording or awkward syntax.
3. Check whether the ending paragraph aligns well with Biostate AI’s tone and voice.

Please present your feedback clearly and concisely.

BLOG POST:
---
{blog_text}
---
"""

def make_reviewer_prompt(blog_text):
    return reviewer_prompt_template.format(blog_text=blog_text)

# Three prompts for three separate “reviewers” (these can be slightly tweaked if you want):
reviewer_prompts = [
    make_reviewer_prompt(original_blog_text),
    make_reviewer_prompt(original_blog_text),
    make_reviewer_prompt(original_blog_text),
]

# ------------------------------------------------------------------------------
# 4. Call the three reviewers simultaneously
# ------------------------------------------------------------------------------
api_key = "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" 

def reviewer_task(prompt):
    """Helper function that calls Claude with a reviewer prompt."""
    return call_claude_api(prompt, api_key=api_key)

feedbacks = []
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    future_to_prompt = {executor.submit(reviewer_task, p): p for p in reviewer_prompts}
    for future in concurrent.futures.as_completed(future_to_prompt):
        feedbacks.append(future.result())

# Print the feedback from each reviewer
print("\n=== ORIGINAL BLOG TEXT ===\n")
print(original_blog_text)
print("\n=== FEEDBACK FROM REVIEWERS ===\n")
for i, feedback in enumerate(feedbacks, 1):
    print(f"[Reviewer {i} Feedback]:\n{feedback}\n")


# ------------------------------------------------------------------------------
# 5. Combine the feedback and send to a “rewriter” Claude agent
# ------------------------------------------------------------------------------
rewriter_prompt_template = """You are a rewriting agent for Biostate AI.
Here is the original blog post, followed by feedback from three reviewers.

Your tasks:
1. Incorporate all their feedback to correct any factual inaccuracies.
2. Address any awkward syntax or incorrect wording.
3. Ensure the final blog post has an ending paragraph that aligns with Biostate AI’s brand tone and voice.
4. The revised version should keep as much of the original style as possible, but apply all necessary improvements.

ORIGINAL BLOG POST:
---
{blog_text}
---

REVIEWER FEEDBACKS:
---
1) {feedback_1}

2) {feedback_2}

3) {feedback_3}
---

Please now provide a revised version of the blog post, incorporating these changes, while preserving the original meaning.
Ensure the final version is well-polished.
"""

rewriter_prompt = rewriter_prompt_template.format(
    blog_text=original_blog_text,
    feedback_1=feedbacks[0],
    feedback_2=feedbacks[1],
    feedback_3=feedbacks[2]
)

revised_blog = call_claude_api(rewriter_prompt, api_key=api_key)

# Print the newly generated content
print("\n=== REVISED BLOG POST (Final) ===\n")
print(revised_blog)
