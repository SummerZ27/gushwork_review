
#api_key = "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" 

import concurrent.futures
from anthropic import Anthropic

# --------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------
API_KEY = "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" 
MODEL_NAME = "claude-3-sonnet-20240229"
MAX_TOKENS = 1024

# --------------------------------------------------------------------
# Claude helper function you provided
# --------------------------------------------------------------------
def ask_claude(prompt, question):
    client = Anthropic(api_key=API_KEY)
    full_message = f"{prompt}\n\nQuestion: {question}"
    try:
        message = client.messages.create(
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": full_message}]
        )
        # The 'message.content' might be a list of chunks depending on version.
        # Adjust indexing if necessary.
        return message.content[0].text
    except Exception as e:
        return f"Error occurred: {str(e)}"

# --------------------------------------------------------------------
# Prompts
# --------------------------------------------------------------------
# A. Single prompt for the reviewers
reviewer_prompt = (
    "You are a specialized blog content reviewer for Biostate AI.\n"
    "Please do the following:\n\n"
    "1. Identify any wrong or partially incorrect scientific or technical facts.\n"
    "2. Identify any incorrect wording or awkward syntax.\n"
    "3. Determine whether the ending paragraph aligns with Biostate AI’s tone and voice.\n\n"
    "Be concise but thorough in your feedback."
)

# B. Rewriter prompt template
rewriter_prompt_template = (
    "You are a rewriting agent for Biostate AI.\n"
    "Here is the original blog post, followed by feedback from three reviewers.\n\n"
    "Your tasks:\n"
    "1. Incorporate all their feedback to correct any factual inaccuracies.\n"
    "2. Fix awkward syntax or incorrect wording.\n"
    "3. Ensure the final post has an ending paragraph that aligns with Biostate AI’s brand tone/voice.\n"
    "4. Preserve as much of the original style and meaning as possible.\n\n"
    "ORIGINAL BLOG POST:\n"
    "---\n{original}\n---\n\n"
    "REVIEWER FEEDBACKS:\n"
    "---\n1) {f1}\n\n2) {f2}\n\n3) {f3}\n---\n\n"
    "Now please provide a fully revised version of the blog."
)

# --------------------------------------------------------------------
# Helper functions
# --------------------------------------------------------------------
def review_blog(blog_text):
    """
    Calls your custom ask_claude() function with reviewer_prompt
    and the blog_text as the question.
    """
    return ask_claude(reviewer_prompt, blog_text)

def rewrite_blog(original_text, feedbacks):
    """
    Calls ask_claude() with the rewriter_prompt_template, injecting
    the original blog text plus all feedback from the 3 reviewers.
    """
    combined_prompt = rewriter_prompt_template.format(
        original=original_text,
        f1=feedbacks[0],
        f2=feedbacks[1],
        f3=feedbacks[2]
    )
    return ask_claude(combined_prompt, "Please provide the revised text now.")

# --------------------------------------------------------------------
# Main flow
# --------------------------------------------------------------------
if __name__ == "__main__":
    # 1. Read the .txt file
    txt_file_path = "Understanding_blog.txt"  # Change to your file
    with open(txt_file_path, "r", encoding="utf-8") as f:
        original_blog_text = f.read()

    # 2. Send the text to 3 reviewers (in parallel)
    num_reviewers = 3
    feedbacks = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_reviewers) as executor:
        futures = [executor.submit(review_blog, original_blog_text) for _ in range(num_reviewers)]
        for f in concurrent.futures.as_completed(futures):
            feedbacks.append(f.result())

    # 3. Print the original blog content
    print("\n=== ORIGINAL BLOG TEXT ===\n")
    print(original_blog_text)

    # 4. Print the feedback from each reviewer
    print("\n=== FEEDBACK FROM REVIEWERS ===\n")
    for i, feedback in enumerate(feedbacks, 1):
        print(f"[Reviewer {i} Feedback]:\n{feedback}\n")

    # 5. Pass everything to the rewriter
    revised_blog = rewrite_blog(original_blog_text, feedbacks)

    # 6. Print the newly revised blog content
    print("\n=== REVISED BLOG POST (Final) ===\n")
    print(revised_blog)
