from flask import Flask, request, jsonify
from PyPDF2 import PdfReader
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from keybert import KeyBERT
import re

app = Flask(__name__)

# ---------------------------------------------------------
# 1. INITIALIZE PURE UNSUPERVISED MODELS (ZERO HARDCODING)
# ---------------------------------------------------------
print("Loading Core NLP Model (all-MiniLM-L6-v2)...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
kw_model = KeyBERT(model=embedding_model)
print("Models loaded successfully! Operating in 100% Unsupervised Domain-Clustered Mode.")

# ---------------------------------------------------------
# 2. HELPER FUNCTIONS
# ---------------------------------------------------------
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
    # Preserves technical characters like C++, C#, Node.js
    text = re.sub(r'[^a-zA-Z0-9\.\+#\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.lower()

# ---------------------------------------------------------
# 3. CORE DYNAMIC NLP PIPELINE
# ---------------------------------------------------------
def extract_dynamic_skills(jd_text, top_n=15):
    """
    100% Dictionary-Free Extraction using Semantic Domain Clustering.
    Discovers the core domain of the JD dynamically and filters out structural fluff.
    """
    # Step 1: Cast a wide net using KeyBERT with moderate diversity
    raw_extracted = kw_model.extract_keywords(
        jd_text, 
        keyphrase_ngram_range=(1, 2), 
        stop_words='english', 
        use_mmr=True,     
        diversity=0.5,
        top_n=30
    )
    
    if not raw_extracted:
        return []
        
    # Step 2: Compute vectors for all candidate phrases
    phrases = [item[0] for item in raw_extracted]
    phrase_embeddings = embedding_model.encode(phrases)
    
    # Step 3: Build a Dynamic Domain Anchor Vector
    # We blend the vectors of the top 3 highest-confidence extractions.
    # If the JD is MERN, this automatically becomes a high-density Web Dev vector.
    domain_anchor = (phrase_embeddings[0] + phrase_embeddings[1] + phrase_embeddings[2]) / 3.0
    
    refined_keywords = []
    
    print("\n" + "="*75)
    print("🔬 DEBUG: DYNAMIC DOMAIN CENTROID CLUSTERING (Unsupervised Optimization)")
    print("="*75)
    print(f"{'Extracted Phrase':<25} | {'JD Importance':<15} | {'Domain Clustering':<15}")
    print("-" * 75)

    # Step 4: Re-rank candidates based on their proximity to the Domain Anchor
    for i, (kw, jd_score) in enumerate(raw_extracted):
        domain_similarity = cosine_similarity([phrase_embeddings[i]], [domain_anchor])[0][0]
        
        # Combine contextual importance with structural domain clustering
        combined_score = (jd_score * 0.4) + (domain_similarity * 0.6)
        refined_keywords.append((kw, combined_score, jd_score, domain_similarity))

    # Re-sort the list based on the domain-reinforced score
    refined_keywords.sort(key=lambda x: x[1], reverse=True)
    
    # Print the optimized debugging metrics
    for kw, combined, jd_sc, domain_sc in refined_keywords[:top_n]:
        print(f"{kw.title():<25} | [{jd_sc:.4f}]         | [{domain_sc:.4f}]")
    print("="*75 + "\n")
    
    return [kw[0] for kw in refined_keywords[:top_n]]

def get_semantic_similarity(resume_text, jd_text):
    """Calculates meaning-based similarity using Sentence Transformers."""
    embeddings = embedding_model.encode([resume_text, jd_text])
    sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return max(0, min(1, sim))

def evaluate_formatting_and_completeness(text):
    """Checks structural integrity using section header analysis and metric detection."""
    text_lower = text.lower()
    has_projects = "project" in text_lower
    has_experience = "experience" in text_lower or "employment" in text_lower
    has_education = "education" in text_lower or "degree" in text_lower
    has_metrics = bool(re.search(r'\b\d+\b|\d+%', text))
    
    score = 0
    if has_projects: score += 0.25
    if has_experience: score += 0.25
    if has_education: score += 0.25
    if has_metrics: score += 0.25
    return score, has_projects, has_experience, has_education, has_metrics

# ---------------------------------------------------------
# 4. MASTER ANALYSIS ENGINE
# ---------------------------------------------------------
def analyze_resume(resume_text, jd_text):
    clean_jd = clean_text(jd_text)
    clean_resume = clean_text(resume_text)

    if not clean_jd.strip() or not clean_resume.strip():
        return {"ats_score": 0, "missing_keywords": [], "suggestions": ["Please provide valid text."]}

    # --- PIPELINE STEP 1: Optimized Keyword Match ---
    jd_keywords = extract_dynamic_skills(clean_jd, top_n=15)
    
    missing_keywords = []
    found_count = 0
    
    # Extract individual words from the JD to identify highly frequent structural verbs
    jd_words = clean_jd.split()
    
    for kw in jd_keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', clean_resume):
            found_count += 1
        else:
            tokens = kw.split()
            if len(tokens) == 2:
                # To prevent matching generic terms like "experience", we identify the more
                # unique technical token by choosing the one that is less frequent in the JD text.
                t0_count = jd_words.count(tokens[0])
                t1_count = jd_words.count(tokens[1])
                meaningful_token = tokens[0] if t0_count <= t1_count else tokens[1]
                
                if re.search(r'\b' + re.escape(meaningful_token) + r'\b', clean_resume):
                    found_count += 1
                    continue
            missing_keywords.append(kw.title())

    skill_match_ratio = found_count / len(jd_keywords) if jd_keywords else 1.0

    # --- TERMINAL PRINT: FINAL SELECTIONS ---
    print("\n" + "="*60)
    print("🤖 OMNI-ADAPTIVE AI KEYWORD SELECTION")
    print("="*60)
    print(f"🔝 Verified Core Tech Targets: \n{jd_keywords}\n")
    print(f"❌ Actual Missing Content: \n{missing_keywords}")
    print("="*60)

    # --- PIPELINE STEP 2: Semantic Similarity ---
    semantic_score = get_semantic_similarity(clean_resume, clean_jd)

    # --- PIPELINE STEP 3: Completeness & Formatting ---
    format_score, has_proj, has_exp, has_edu, has_metrics = evaluate_formatting_and_completeness(resume_text)

    # --- Calculate Final Weighted Score ---
    final_score = (skill_match_ratio * 40) + (semantic_score * 40) + (format_score * 20)
    final_score = round(final_score, 2)

    # --- PIPELINE STEP 4: Suggestions ---
    suggestions = []
    if not has_metrics:
        suggestions.append("Quantify your achievements. Add numbers, percentages, or data to show your impact (e.g., 'Improved performance by 20%').")
    if not has_proj:
        suggestions.append("Add a 'Projects' section to showcase practical applications of your skills.")
    if skill_match_ratio < 0.5:
        suggestions.append("You are missing several core requirements identified by the AI. Consider adding the missing keywords if you possess the experience.")
    if semantic_score < 0.4:
        suggestions.append("The overall language of your resume doesn't align closely with the job description. Try mirroring the phrasing and terminology used in the JD.")
    elif final_score >= 75:
        suggestions.append("Great job! Your resume structurally and semantically aligns well with this role.")

    if not suggestions:
        suggestions.append("Your resume looks solid. Review the missing keywords just to be safe.")

    # --- TERMINAL PRINT: FINAL SCORES ---
    print("\n" + "="*60)
    print("🏆 FINAL ATS SCORING BREAKDOWN")
    print("="*60)
    print(f"🛠️  Domain Keyword Match (40%): {round(skill_match_ratio * 100, 2)}%")
    print(f"🧠 Semantic Score (40%):       {round(semantic_score * 100, 2)}%")
    print(f"📋 Completeness (20%):         {round(format_score * 100, 2)}%")
    print(f"⭐ TOTAL ATS SCORE:            {final_score}%")
    print("="*60 + "\n")

    return {
        "ats_score": final_score,
        "breakdown": {
            "keyword_match_score": round(skill_match_ratio * 100, 2),
            "semantic_score": round(semantic_score * 100, 2),
            "completeness_score": round(format_score * 100, 2)
        },
        "missing_keywords": missing_keywords[:15],
        "suggestions": suggestions
    }

# ---------------------------------------------------------
# 5. API ROUTES
# ---------------------------------------------------------
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