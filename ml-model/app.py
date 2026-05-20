from flask import Flask, request, jsonify
from PyPDF2 import PdfReader
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from keybert import KeyBERT
import re

app = Flask(__name__)

# ---------------------------------------------------------
# 1. INITIALIZE PURE UNSUPERVISED MODELS
# ---------------------------------------------------------
print("\n" + "*"*80)
print("🚀 BOOTING UP ENHANCED ATS AI ENGINE...")
print("*"*80)
print("Loading Core NLP Model (all-MiniLM-L6-v2)...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
kw_model = KeyBERT(model=embedding_model)
print("Models loaded successfully! Operating in Smart Tech-Focused Mode.\n")

# ---------------------------------------------------------
# 2. HELPER FUNCTIONS
# ---------------------------------------------------------
def extract_text_from_pdf(pdf_file):
    print("\n" + "="*80)
    print("📄 STEP 0a: PDF EXTRACTION")
    print("="*80)
    print(f"Reading file: {pdf_file.filename}...")
    
    text = ""
    try:
        reader = PdfReader(pdf_file)
        for i, page in enumerate(reader.pages):
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        print(f"✅ Successfully extracted {len(text)} characters from PDF.")
    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
    return text

def clean_text(text):
    # Added hyphen to preserve words like "React-Native" or "Object-Oriented"
    text = re.sub(r'[^a-zA-Z0-9\.\+#\-\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.lower()

def boost_skills_section(text):
    """
    Artificially boosts the mathematical weight of the 'Skills' section 
    so KeyBERT prioritizes technical terms over generic job fluff.
    """
    skill_keywords = ['skills', 'technologies', 'tech stack', 'languages', 
                      'frameworks', 'tools', 'databases', 'requirements', 
                      'qualifications', 'core concepts', 'technologies:']
    
    # Split text by newlines or full stops to evaluate line by line
    sentences = re.split(r'\n|\. ', text)
    boosted_text = text
    
    for sentence in sentences:
        if any(kw in sentence.lower() for kw in skill_keywords):
            # Duplicate the tech-heavy sentences 3 times in the background string
            # to massively increase their TF-IDF / KeyBERT semantic weight
            boosted_text += (" " + sentence) * 3
            
    return boosted_text

def evaluate_formatting(text):
    print("\n" + "="*80)
    print("📏 STEP 0c: RESUME FORMATTING & COMPLETENESS CHECK")
    print("="*80)
    
    text_lower = text.lower()
    score = 0
    
    has_projects = "project" in text_lower
    has_experience = "experience" in text_lower or "employment" in text_lower
    has_education = "education" in text_lower or "degree" in text_lower
    has_metrics = bool(re.search(r'\b\d+\b|\d+%', text))
    
    if has_projects: score += 0.25
    if has_experience: score += 0.25
    if has_education: score += 0.25
    if has_metrics: score += 0.25
    
    print(f"Projects Section Found:   {'✅' if has_projects else '❌'}")
    print(f"Experience Section Found: {'✅' if has_experience else '❌'}")
    print(f"Education Section Found:  {'✅' if has_education else '❌'}")
    print(f"Measurable Metrics Found: {'✅' if has_metrics else '❌'}")
    print(f"Total Formatting Score:   {score * 100}%\n")
    
    return score

# ---------------------------------------------------------
# 3. CORE EXTRACTION PIPELINES (SKILL-PRIORITIZED)
# ---------------------------------------------------------
def extract_smart_keywords(raw_text, cleaned_text, top_n=30):
    # 1. Boost the technical sections
    boosted_text = boost_skills_section(cleaned_text)

    # 2. Extract Unigrams (Highly targets exact hard skills: React, Python, AWS, Docker)
    unigrams = kw_model.extract_keywords(
        boosted_text, keyphrase_ngram_range=(1, 1), stop_words='english', 
        use_mmr=True, diversity=0.2, top_n=int(top_n * 0.6)
    )

    # 3. Extract Bigrams (Targets concepts: Machine Learning, REST API, Web Development)
    bigrams = kw_model.extract_keywords(
        boosted_text, keyphrase_ngram_range=(2, 2), stop_words='english', 
        use_mmr=True, diversity=0.4, top_n=int(top_n * 0.4)
    )

    # 4. Explicit Regex Rescue for Punctuation Tech (C++, Node.js, C#, etc.)
    # KeyBERT sometimes tokenizes out punctuation. We grab them forcefully.
    special_tech = re.findall(r'\b[a-z0-9]+\.[a-z0-9]+\b|\b[a-z]+\+\+\b|\b[a-z]+#\b', raw_text.lower())
    special_tech = list(set(special_tech)) # Remove duplicates

    # Combine all extracted words
    uni_words = [kw[0] for kw in unigrams]
    bi_words = [kw[0] for kw in bigrams]
    combined = special_tech + uni_words + bi_words

    # Deduplicate while preserving priority order (Special -> Unigrams -> Bigrams)
    final_kws = []
    seen = set()
    for kw in combined:
        if kw not in seen and len(kw) > 1: # Ignore single stray letters
            final_kws.append(kw)
            seen.add(kw)

    return final_kws[:top_n]

# ---------------------------------------------------------
# 4. MASTER ANALYSIS ENGINE
# ---------------------------------------------------------
def analyze_resume(resume_text, jd_text):
    # --- CLEANING LOGS ---
    print("\n" + "="*80)
    print("🧹 STEP 0b: TEXT CLEANING & NORMALIZATION")
    print("="*80)
    
    clean_jd = clean_text(jd_text)
    clean_resume = clean_text(resume_text)
    
    print(f"Raw JD Length: {len(jd_text)} chars   -> Cleaned JD Length: {len(clean_jd)} chars")
    print(f"Raw CV Length: {len(resume_text)} chars   -> Cleaned CV Length: {len(clean_resume)} chars")

    if not clean_jd.strip() or not clean_resume.strip():
        print("❌ Error: Blank text provided after cleaning.")
        return {"ats_score": 0, "missing_keywords": [], "suggestions": ["Please provide valid text."]}

    format_score = evaluate_formatting(resume_text)

    # =========================================================
    # STEP 1: INDEPENDENT EXTRACTION
    # =========================================================
    # Extract slightly more for JD to ensure deep technical coverage, and a lot for CV
    jd_keywords = extract_smart_keywords(jd_text, clean_jd, top_n=35)
    resume_keywords = extract_smart_keywords(resume_text, clean_resume, top_n=80)
    
    flat_resume = re.sub(r'[^a-z0-9\s]', ' ', clean_resume)
    
    print("="*80)
    print("🤖 STEP 1: SMART TECH-FOCUSED AI EXTRACTION")
    print("="*80)
    print(f"📄 JD Concepts Extracted ({len(jd_keywords)}):\n{jd_keywords}\n")
    print(f"📝 Resume Concepts Extracted ({len(resume_keywords)}):\n{resume_keywords[:20]}... [Truncated]")
    
    # =========================================================
    # STEP 2: SMART CROSS-MAPPING
    # =========================================================
    print("\n" + "="*80)
    print("🧠 STEP 2: SMART CROSS-MAPPING (Text + Split + Semantic Threshold 65%)")
    print("="*80)
    print(f"{'JD Requirement':<20} | {'Method Used':<12} | {'Resume Match Found':<20} | {'Score'}")
    print("-" * 80)
    
    jd_vecs = embedding_model.encode(jd_keywords)
    resume_vecs = embedding_model.encode(resume_keywords)

    missing_keywords = []
    match_count = 0
    MATCH_THRESHOLD = 0.65 

    for i, jd_kw in enumerate(jd_keywords):
        flat_jd_kw = re.sub(r'[^a-z0-9\s]', ' ', jd_kw)
        
        # 1. THE OBVIOUS CHECK: EXACT TEXT MATCH
        # Using string matching here handles things like "node.js" perfectly
        if jd_kw in clean_resume or re.search(r'\b' + re.escape(flat_jd_kw) + r'\b', flat_resume):
            match_status = "✅ MATCH"
            match_count += 1
            print(f"{jd_kw.title():<20} | {'[TEXT]':<12} | {jd_kw.title():<20} | 100.0% -> {match_status}")
            continue

        # 2. THE NEW FIX: SPLIT-TOKEN MATCH 
        tokens = flat_jd_kw.split()
        if len(tokens) > 1:
            matched_token = None
            # Expanded fluff words so it forces the matcher to find the actual skill, not the verb
            fluff_words = {
                'work', 'experience', 'technologies', 'building', 'develop', 'overview',
                'skills', 'platforms', 'applications', 'knowledge', 'development', 'candidates',
                'projects', 'engineering', 'join', 'responsibilities', 'resume', 'stand', 'teams',
                'required', 'preferred', 'qualifications', 'understanding', 'familiarity', 'strong',
                'using', 'build', 'participate', 'tools', 'environments', 'systems'
            }
            
            for t in tokens:
                if len(t) > 2 and t not in fluff_words:
                    if re.search(r'\b' + re.escape(t) + r'\b', flat_resume):
                        matched_token = t
                        break
            
            if matched_token:
                match_status = "✅ MATCH"
                match_count += 1
                print(f"{jd_kw.title():<20} | {'[SPLIT]':<12} | {matched_token.title():<20} | 100.0% -> {match_status}")
                continue

        # 3. THE SMART FALLBACK: SEMANTIC CROSS-MAPPING
        similarities = cosine_similarity([jd_vecs[i]], resume_vecs)[0]
        max_sim = max(similarities)
        best_match_idx = similarities.argmax()
        best_match_kw = resume_keywords[best_match_idx]
        
        if max_sim >= MATCH_THRESHOLD:
            match_status = "✅ MATCH"
            match_count += 1
        else:
            match_status = "❌ MISSING"
            missing_keywords.append(jd_kw.title())
            
        print(f"{jd_kw.title():<20} | {'[SEMANTIC]':<12} | {best_match_kw.title():<20} | {max_sim*100:>5.1f}% -> {match_status}")

    print("="*80)

    # =========================================================
    # STEP 3: SCORING & SCALING
    # =========================================================
    skill_match_ratio = match_count / len(jd_keywords) if jd_keywords else 1.0

    full_semantic_sim = cosine_similarity(
        embedding_model.encode([clean_resume]), 
        embedding_model.encode([clean_jd])
    )[0][0]
    semantic_score = max(0, min(1, full_semantic_sim))

    # Calculate Final Weighted Score
    final_score = (skill_match_ratio * 40) + (semantic_score * 40) + (format_score * 20)
    final_score = round(final_score, 2)

    # =========================================================
    # STEP 4: INTELLIGENT SUGGESTIONS
    # =========================================================
    suggestions = []
    if format_score < 1.0:
        suggestions.append("Improve your resume formatting. Ensure you have clear sections for Experience, Projects, Education, and use quantifiable metrics.")
    if skill_match_ratio < 0.6:
        suggestions.append(f"You missed several core technical requirements. Try explicitly adding terms like {', '.join(missing_keywords[:3])} to your experience.")
    if semantic_score < 0.4:
        suggestions.append("The overall tone of your resume doesn't align closely with the job description. Mirror the phrasing used in the JD.")
    elif final_score >= 75:
        suggestions.append("Great job! Your resume structurally and semantically aligns well with this role.")

    if not suggestions:
        suggestions.append("Your resume looks solid. Review the missing keywords just to be safe.")

    print("\n" + "="*80)
    print("🏆 FINAL ATS SCORING BREAKDOWN")
    print("="*80)
    print(f"🛠️  Cross-Mapped Keyword Match (40%): {round(skill_match_ratio * 100, 2)}%")
    print(f"🧠 Overall Semantic Score (40%):      {round(semantic_score * 100, 2)}%")
    print(f"📋 Completeness & Formatting (20%):   {round(format_score * 100, 2)}%")
    print(f"⭐ TOTAL ATS SCORE:                   {final_score}%")
    print("="*80 + "\n")

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
    print("\n" + "*"*80)
    print("📥 NEW INCOMING REQUEST: /analyze")
    print("*"*80)
    
    if 'resume' not in request.files or 'job_description' not in request.form:
        print("❌ Error: Missing resume or job description in request.")
        return jsonify({"error": "Missing resume or job description"}), 400

    pdf_file = request.files['resume']
    jd_text = request.form['job_description']

    resume_text = extract_text_from_pdf(pdf_file)
    
    if not resume_text.strip():
        print("❌ Error: Extracted PDF text is blank.")
        return jsonify({"error": "Could not extract text from PDF."}), 400

    analysis_results = analyze_resume(resume_text, jd_text)
    
    print("📤 SENDING RESPONSE BACK TO FRONTEND...")
    return jsonify(analysis_results)

if __name__ == '__main__':
    app.run(debug=True, port=5000)