from flask import Flask, request, jsonify
from PyPDF2 import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

app = Flask(__name__)

def extract_text_from_pdf(pdf_file):
    """Extracts text from the uploaded PDF file."""
    text = ""
    try:
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            text += page.extract_text() + " "
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def clean_text(text):
    """
    Cleans text while preserving critical tech symbols like +, #, .
    (e.g., ensures C++, Node.js, C# are not destroyed by standard tokenizers).
    """
    # Remove special characters except alphanumeric, spaces, dot, plus, and hash
    text = re.sub(r'[^a-zA-Z0-9\.\+#\s]', ' ', text)
    # Condense multiple spaces into one
    text = re.sub(r'\s+', ' ', text)
    return text.lower()

def analyze_resume(resume_text, jd_text):
    clean_jd = clean_text(jd_text)
    clean_resume = clean_text(resume_text)

    if not clean_jd.strip() or not clean_resume.strip():
        return {"ats_score": 0, "missing_keywords": [], "suggestions": ["Please provide valid text for both documents."]}

    # 1. Initialize Dynamic NLP Vectorizer (TF-IDF)
    # - stop_words='english': Automatically removes generic words (the, is, at, which, etc.)
    # - ngram_range=(1, 2): Captures single words ("Python") AND two-word phrases ("Machine Learning", "Full Stack")
    # - token_pattern: Custom regex to ensure terms like "C++" and "Node.js" are captured as single tokens
    vectorizer = TfidfVectorizer(
        stop_words='english',
        ngram_range=(1, 2),
        token_pattern=r'(?u)\b[a-zA-Z0-9\.\+#]{2,}\b'
    )

    try:
        # 2. Vectorize both documents to build the dynamic vocabulary
        tfidf_matrix = vectorizer.fit_transform([clean_resume, clean_jd])
        
        # 3. Calculate Overall ATS Score (Cosine Similarity)
        match_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        score_percentage = round(match_score * 100, 2)

        # 4. Extract Dynamic Keywords
        # Get all words identified across both documents
        feature_names = vectorizer.get_feature_names_out()
        
        # Get the mathematical weight (importance) of each word in the Job Description
        jd_vector = tfidf_matrix[1].toarray()[0]
        # Get the weight of each word in the Resume
        resume_vector = tfidf_matrix[0].toarray()[0]

        # Sort the Job Description words by their importance score (highest to lowest)
        top_jd_indices = jd_vector.argsort()[::-1]

        missing_keywords = []
        extracted_jd_keywords = []

        # 5. Determine the top requirements and check if they are missing
        for idx in top_jd_indices:
            word = feature_names[idx]
            importance_score = jd_vector[idx]
            
            # If the score is 0, we have passed all words actually in the JD
            if importance_score == 0:
                break
            
            # Filter out pure numbers and very short noise
            if not word.isnumeric() and len(word) > 2:
                extracted_jd_keywords.append(word)

                # If this highly important JD word has a score of 0 in the resume, it is missing
                if resume_vector[idx] == 0:
                    missing_keywords.append(word)

            # Cap the dynamic extraction at the top 30 most heavily weighted JD terms
            # to avoid picking up obscure noise at the bottom of the description
            if len(extracted_jd_keywords) >= 30:
                break

        # 6. Dynamic Suggestions
        suggestions = []
        if score_percentage < 40:
            suggestions.append("Your resume needs significant tailoring. Focus on integrating the missing core requirements into your experience sections.")
        elif score_percentage < 75:
            suggestions.append("Good start! To improve your score, ensure you naturally weave the identified missing keywords into your project descriptions.")
        else:
            suggestions.append("Excellent match! Your resume strongly aligns with the mathematical core of this job description.")

        return {
            "ats_score": score_percentage,
            "missing_keywords": missing_keywords[:15], # Return the top 15 most important missing words
            "suggestions": suggestions
        }

    except ValueError:
        return {"ats_score": 0, "missing_keywords": [], "suggestions": ["Could not extract meaningful keywords. Please provide more text."]}

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'resume' not in request.files or 'job_description' not in request.form:
        return jsonify({"error": "Missing resume or job description"}), 400

    pdf_file = request.files['resume']
    jd_text = request.form['job_description']

    resume_text = extract_text_from_pdf(pdf_file)
    
    if not resume_text.strip():
        return jsonify({"error": "Could not extract text from PDF."}), 400

    analysis_results = analyze_resume(resume_text, jd_text)
    return jsonify(analysis_results)

if __name__ == '__main__':
    app.run(debug=True, port=5000)