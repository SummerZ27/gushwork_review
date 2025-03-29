from flask import Flask, render_template, request, Response, jsonify
import concurrent.futures
import json
from anthropic import Anthropic

app = Flask(__name__)

# --------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------
API_KEY = "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" 
MODEL_NAME = "claude-3-sonnet-20240229"
MAX_TOKENS = 4096

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
        # Adjust indexing if needed based on API response structure.
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
    "Be concise but thorough and accurate in your feedback. For any of these fields, if u don't think there are any wrong or incorrect information, you can also answer no."
)

rewriter_prompt_template = (
    "You are a rewriting agent for Biostate AI.\n"
    "Here is the original blog post, followed by feedback from three reviewers.\n\n"
    "Your tasks:\n"
    "1. Incorporate all their feedback to correct any factual inaccuracies.\n"
    "2. Fix awkward syntax or incorrect wording.\n"
    "3. Ensure the final post has an ending paragraph that aligns with Biostate AI’s brand tone/voice.\n"
    "4. Preserve as much of the original style and meaning as possible. Don't feel the need to paraphrase, keep the original wording if there are no feedbacks to change them. Kepp the Sources and Citations and footnotes exactly the same.\n\n"
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
# Streaming Endpoint
# --------------------------------------------------------------------
@app.route('/stream', methods=['POST'])
def stream():
    # Validate file input
    file = request.files.get('file')
    if not file:
        return jsonify(error="No file provided"), 400
    try:
        original_text = file.read().decode('utf-8')
    except Exception as e:
        return jsonify(error=str(e)), 400

    def generate():
        # 1. Immediately yield the original text
        yield f"data: {json.dumps({'event': 'original', 'content': original_text})}\n\n"
        
        # 2. Process three reviewer feedbacks sequentially so that they are streamed in order.
        feedbacks = []
        for i in range(3):
            feedback = review_blog(original_text)
            feedbacks.append(feedback)
            yield f"data: {json.dumps({'event': 'feedback', 'index': i+1, 'content': feedback})}\n\n"
        
        # 3. Generate the revised blog post using all feedback
        revised = rewrite_blog(original_text, feedbacks)
        yield f"data: {json.dumps({'event': 'revised', 'content': revised})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
