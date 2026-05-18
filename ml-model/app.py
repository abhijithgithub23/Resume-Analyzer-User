from flask import Flask, request, jsonify
from PyPDF2 import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

app = Flask(__name__)

def extract_text_from_pdf(pdf_file):
    text = ""
    try:
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            text += page.extract_text() + " "
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text

def analyze_resume(resume_text, jd_text):
    clean_resume = clean_text(resume_text)
    clean_jd = clean_text(jd_text)

    # 1. ATS Match Score using TF-IDF & Cosine Similarity
    documents = [clean_resume, clean_jd]
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(documents)
    match_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    
    # Convert to percentage
    score_percentage = round(match_score * 100, 2)

    # 2. Keyword Analysis (Basic approach: finding words in JD not in Resume)
    vectorizer_jd = TfidfVectorizer(stop_words='english')
    vectorizer_jd.fit([clean_jd])
    jd_keywords = set(vectorizer_jd.get_feature_names_out())
    
    resume_words = set(clean_resume.split())
    missing_keywords = list(jd_keywords - resume_words)

    # 3. Suggestions based on score
    suggestions = []
    if score_percentage < 50:
        suggestions.append("Your resume lacks many core keywords from the job description. Consider adding the missing skills.")
    elif score_percentage < 75:
        suggestions.append("Good match, but try to rephrase your bullet points to exactly match the job description terminology.")
    else:
        suggestions.append("Excellent match! Ensure your formatting is clean and easy for standard ATS software to parse.")

    return {
        "ats_score": score_percentage,
        "missing_keywords": missing_keywords[:15], # Return top 15 missing keywords
        "suggestions": suggestions
    }

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
    # Running on port 5000
    app.run(debug=True, port=5000)