import os
import google.generativeai as genai
from typing import List, Dict, Any
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def get_gemini_model():
    """
    Get a Gemini model instance. Falls back if API key is not configured.
    """
    if not api_key:
        return None
    try:
        # Use gemini-3.5-flash for fast and cost-effective text analysis
        return genai.GenerativeModel("gemini-3.5-flash")
    except Exception as e:
        print(f"Error initializing Gemini model: {e}")
        return None

def analyze_headline_evolution(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Use Gemini to analyze the historical edits of a single article's headline.
    """
    model = get_gemini_model()
    if not model:
        # Return fallback mock/analytical response if API key is missing
        return get_fallback_evolution_analysis(history)
        
    # Format the timeline for the prompt
    timeline_str = ""
    for idx, entry in enumerate(history):
        status = "Original" if idx == 0 else "Edit"
        timeline_str += f"- {entry['datetime']} ({status}): \"{entry['headline']}\"\n"
        
    prompt = f"""
    You are an expert media analyst specializing in news bias, stealth editing, and linguistic framing.
    
    Below is a timeline of changes made to the headline of a single news article over time:
    {timeline_str}
    
    Please analyze this sequence of changes and provide a detailed report in JSON format. The JSON must contain the following keys exactly:
    1. "summary": A brief 2-3 sentence overview of the shift in headline tone/intent.
    2. "original_vs_final": A comparison of the starting headline and the ending headline.
    3. "framing_techniques": A list of specific framing or linguistic techniques used in the edits (e.g., active/passive voice, emotional priming, bias shift, clickbait optimization, euphemisms, softening of blame).
    4. "narrative_shift": Describe what story or narrative the outlet is trying to project at the end compared to the start.
    5. "manipulation_index": A score from 0 to 10 (where 0 is completely neutral/informational correction, and 10 is high-level psychological framing/manipulation), with a brief 1-sentence justification.
    6. "sentiment_shift": A comparison of the sentiment (e.g., Neutral -> Fear-mongering, or Accusatory -> Softened).
    
    Return ONLY the raw JSON string. Do not include markdown code block formatting (like ```json).
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Strip markdown json block if model ignored prompt instructions
        if text.startswith("```"):
            text = re.sub(r"^```json\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        return json.loads(text)
    except Exception as e:
        print(f"Error generating AI analysis: {e}")
        return get_fallback_evolution_analysis(history)

def analyze_topic_drift(headlines_by_date: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Analyze the shift in topic framing across different milestones (e.g., 1M, 3M, 6M, 1Y ago).
    """
    model = get_gemini_model()
    if not model:
        return get_fallback_topic_analysis(headlines_by_date)
        
    # Format the data for the prompt
    data_str = ""
    for period, articles in headlines_by_date.items():
        data_str += f"\n--- Period: {period} ---\n"
        if not articles:
            data_str += "No articles found.\n"
        for art in articles[:8]: # Limit to top 8 per period to fit context comfortably
            data_str += f"- [{art.get('section', 'news')}] \"{art['headline']}\" (URL: {art['url']})\n"
            
    prompt = f"""
    You are an expert media analyst specializing in historical discourse, propaganda tracking, and media narrative framing.
    
    Below is a collection of headlines gathered from the same news outlet/topic at different historical milestones (e.g., Today, 1 Month Ago, 3 Months Ago, 6 Months Ago, 1 Year Ago):
    {data_str}
    
    Analyze how the coverage, framing, tone, and agenda of this topic evolved across these milestones. Provide a detailed report in JSON format containing the following keys:
    1. "executive_summary": A summary of how the narrative shifted over the timeline.
    2. "timeline_milestones": A dict mapping each period (e.g., "1_month_ago", "3_months_ago", etc.) to a 1-sentence description of the dominant framing during that time.
    3. "bias_evolution": An explanation of how editorial bias or political stance shifted over time (e.g., did they become more sympathetic, hostile, alarmist, or dismissive?).
    4. "key_buzzwords": A list of prominent buzzwords, emotional triggers, or loaded terms that appeared or disappeared over the months.
    5. "editorial_intent": The likely agenda or goal behind the shift in coverage framing.
    6. "polarization_rating": A rating from 0 to 10 of how polarized/opinionated the headlines became over time, with a brief explanation.
    
    Return ONLY the raw JSON string. Do not include markdown code block formatting.
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"Error generating AI topic analysis: {e}")
        return get_fallback_topic_analysis(headlines_by_date)

def get_fallback_evolution_analysis(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Provide a rule-based fallback analysis if the Gemini API is unavailable.
    """
    if len(history) < 2:
        return {
            "summary": "Insufficient data to perform a comparison.",
            "original_vs_final": "Need at least two unique headlines.",
            "framing_techniques": [],
            "narrative_shift": "No changes recorded.",
            "manipulation_index": 0,
            "sentiment_shift": "N/A"
        }
        
    orig = history[0]["headline"]
    final = history[-1]["headline"]
    
    # Very basic rule-based analysis
    diff_len = len(final) - len(orig)
    words_orig = set(orig.lower().split())
    words_final = set(final.lower().split())
    added = words_final - words_orig
    removed = words_orig - words_final
    
    techniques = []
    if diff_len < -10:
        techniques.append("Headline shortening (brevity optimization)")
    elif diff_len > 10:
        techniques.append("Detail addition (clarity optimization)")
        
    common_clickbait = ["why", "how", "what", "reveals", "shocking", "crisis", "slams", "blasts"]
    if any(w in final.lower() for w in common_clickbait) and not any(w in orig.lower() for w in common_clickbait):
        techniques.append("Sensationalism / Clickbait optimization")
        
    return {
        "summary": "Rule-based analysis: The headline was updated over time. Original: '{}' -> Final: '{}'.".format(orig, final),
        "original_vs_final": "Original: '{}'\nFinal: '{}'".format(orig, final),
        "framing_techniques": techniques or ["Linguistic adjustments / general edit"],
        "narrative_shift": "Words added: {}. Words removed: {}.".format(list(added)[:5], list(removed)[:5]),
        "manipulation_index": 3 if techniques else 1,
        "sentiment_shift": "Basic edit detected. Check API key configuration for deeper AI insights."
    }

def get_fallback_topic_analysis(headlines_by_date: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Provide a fallback analysis for topic drift if Gemini is unavailable.
    """
    summary_parts = []
    milestones = {}
    
    for period, articles in headlines_by_date.items():
        count = len(articles)
        milestones[period] = f"Found {count} articles."
        if articles:
            summary_parts.append(f"In the {period} period, articles like '{articles[0]['headline']}' were published.")
            
    return {
        "executive_summary": "Fallback report: " + " ".join(summary_parts) if summary_parts else "No historical articles collected to analyze.",
        "timeline_milestones": milestones,
        "bias_evolution": "Requires Gemini API Key for deep political/bias evolution mapping.",
        "key_buzzwords": ["Configure GEMINI_API_KEY in .env file to enable NLP keyword extraction."],
        "editorial_intent": "General news tracking.",
        "polarization_rating": 2,
        "polarization_explanation": "Basic collection mode. Install API key for linguistic bias analytics."
    }
