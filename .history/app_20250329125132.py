from flask import Flask, render_template, request, jsonify
import concurrent.futures
from anthropic import Anthropic

app = Flask(__name__)

# --------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------
API_KEY = "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" 
MODEL_NAME = "claude-3-sonnet-20240229"
MAX_TOKENS = 1024

# --------------------------------------------------------------------
# Claude helper function
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
        # Adjust indexing if needed based on API response
        return message.content[0].text
    except Exception as e:
        return f"Error occurred: {str(e)}"

# --------------------------------------------------------------------
# Prompts
# --------------------------------------------------------------------
reviewer_prompt = (
    "You are a specialized blog content reviewer for Biostate AI.\n"
    "Please do the following:\n\n"
    "1. Identify any wrong or partially incorrect scientific or technical facts.\n"
    "2. Identify any incorrect wording or awkward syntax.\n"
    "3. Determine whether the ending paragraph aligns with Biostate AI’s tone and voice.\n\n"
    "Be concise but thorough in your feedback."
)

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
    return ask_claude(reviewer_prompt, blog_text)

def rewrite_blog(original_text, feedbacks):
    combined_prompt = rewriter_prompt_template.format(
        original=original_text,
        f1=feedbacks[0],
        f2=feedbacks[1],
        f3=feedbacks[2]
    )
    return ask_claude(combined_prompt, "Please provide the revised text now.")

# --------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_file():
    # Check if the file part is present
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        original_text = file.read().decode('utf-8')
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    # 1. Call three reviewers in parallel
    num_reviewers = 3
    feedbacks = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_reviewers) as executor:
        futures = [executor.submit(review_blog, original_text) for _ in range(num_reviewers)]
        for future in concurrent.futures.as_completed(futures):
            feedbacks.append(future.result())

    # 2. Get revised blog post
    revised_blog = rewrite_blog(original_text, feedbacks)

    # 3. Return JSON with all data
    return jsonify({
        "original": original_text,
        "feedbacks": feedbacks,
        "revised": revised_blog
    })

if __name__ == '__main__':
    app.run(debug=True)
