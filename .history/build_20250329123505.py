
#api_key = "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" 

import os
import concurrent.futures
from docx import Document
from anthropic import Anthropic  # Make sure you've installed the "anthropic" library

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------
API_KEY = "YOUR_CLAUDE_API_KEY"  # Replace with your real key
MODEL_NAME = "claude-3-sonnet-20240229"
MAX_TOKENS = 1024

# ---------------------------------------------------------------------
# Claude helper function you provided
# ---------------------------------------------------------------------
def ask_claude(prompt, question):
    client = Anthropic(api_key=API_KEY)
    full_message = f"{prompt}\n\nQuestion: {question}"
    try:
        message = client.messages.create(
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": full_message}]
        )
        # The 'message.content' in the anthropic library typically returns
        # a list of "chunks" or a single chunk object. Adjust indexing if needed.
        return message.content[0].text
    except Exception as e:
        return f"Error occurred: {str(e)}"

# ---------------------------------------------------------------------
# 1. Function to read .docx file text
# ---------------------------------------------------------------------
def read_docx(file_path):
    """
    Reads the .docx file at file_path and returns the concatenated text of all paragraphs.
    """
    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs]
    return "\n".join(paragraphs)

# ---------------------------------------------------------------------
# 2. Build reviewer prompt
# ---------------------------------------------------------------------
reviewer_prompt = (
    "You are a specialized blog content reviewer for Biostate AI.\n"
    "Please do the following:\n\n"
    "1. Identify any wrong or partially incorrect scientific or technical facts.\n"
    "2. Identify any incorrect wording or awkward syntax.\n"
    "3. Determine whether the ending paragraph aligns with Biostate AI’s tone and voice.\n\n"
    "Be concise but thorough in your feedback."
)

# ---------------------------------------------------------------------
# 3. Prepare a function to call each reviewer
# ---------------------------------------------------------------------
def review_blog(blog_text):
    """
    Calls your custom ask_claude() function with the same prompt and the blog text as the 'question'.
    Returns the review feedback from Claude.
    """
    return ask_claude(reviewer_prompt, blog_text)

# ---------------------------------------------------------------------
# 4. Build rewriter prompt
# ---------------------------------------------------------------------
rewriter_prompt_template = (
    "You are a rewriting agent for Biostate AI.\n"
    "Here is the original blog post, followed by feedback from three reviewers.\n\n"
    "Your tasks:\n"
    "1. Incorporate all their feedback to correct factual inaccuracies.\n"
    "2. Fix awkward syntax or incorrect wording.\n"
    "3. Ensure the final post has an ending paragraph that aligns with Biostate AI’s brand tone/voice.\n"
    "4. Preserve as much of the original style and meaning as possible.\n\n"
    "ORIGINAL BLOG POST:\n"
    "---\n{original}\n---\n\n"
    "REVIEWER FEEDBACKS:\n"
    "---\n1) {f1}\n\n2) {f2}\n\n3) {f3}\n---\n\n"
    "Now provide a fully revised version."
)

def rewrite_blog(original_text, feedback_list):
    """
    Calls ask_claude() with the rewriter prompt, passing in
    the original blog text and the three reviewer feedbacks.
    Returns the newly revised blog text.
    """
    combined_prompt = rewriter_prompt_template.format(
        original=original_text,
        f1=feedback_list[0],
        f2=feedback_list[1],
        f3=feedback_list[2]
    )
    # We can set the 'question' part to something brief, since the real content is in combined_prompt:
    return ask_claude(combined_prompt, "Please provide the revised text now.")

# ---------------------------------------------------------------------
# 5. Main logic
# ---------------------------------------------------------------------
if __name__ == "__main__":
    # (A) Read the .docx file
    docx_file_path = "my_blog_post.docx"  # Replace with your actual file path
    original_blog_text = read_docx(docx_file_path)

    # (B) Send to 3 reviewers in parallel
    num_reviewers = 3
    feedbacks = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_reviewers) as executor:
        futures = [executor.submit(review_blog, original_blog_text) for _ in range(num_reviewers)]
        for f in concurrent.futures.as_completed(futures):
            feedbacks.append(f.result())

    # (C) Print the original blog content
    print("\n=== ORIGINAL BLOG TEXT ===\n")
    print(original_blog_text)

    # (D) Print the feedback from each reviewer
    print("\n=== FEEDBACK FROM REVIEWERS ===\n")
    for i, fb in enumerate(feedbacks, 1):
        print(f"[Reviewer {i} Feedback]:\n{fb}\n")

    # (E) Pass everything to the rewriter
    revised_blog = rewrite_blog(original_blog_text, feedbacks)

    # (F) Print the newly generated, revised blog content
    print("\n=== REVISED BLOG POST (Final) ===\n")
    print(revised_blog)
