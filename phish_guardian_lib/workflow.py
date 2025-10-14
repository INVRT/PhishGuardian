import base64
from langgraph.graph import StateGraph, END
from typing import TypedDict, Dict
from langchain_core.messages import HumanMessage
from .config import llm
from .agents import prompts
from .tools import search_online_knowledge, take_screenshot_of_url

# --- The Graph State and helper functions are correct ---
class GraphState(TypedDict):
    webpage_data: dict
    screenshot: str
    specialist_analyses: Dict[str, str]
    visual_analysis_report: str
    verification_results: dict
    judge_verdict: str
    judge_reasoning: str
    malicious_intention: str

def create_agent_chain(prompt):
    return prompt | llm

def image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

# --- All nodes up to the intent agent are correct ---
def run_text_specialists(state: GraphState):
    # ... (no changes needed)
    print("--- Running Text Specialist Agents ---")
    data = state['webpage_data']
    
    text_analyses = {
        "URL Analyst": create_agent_chain(prompts.url_analyst_prompt).invoke(data),
        "HTML Analyst": create_agent_chain(prompts.html_analyst_prompt).invoke(data),
        "Content Analyst": create_agent_chain(prompts.content_analyst_prompt).invoke(data),
        "Brand Analyst": create_agent_chain(prompts.brand_analyst_prompt).invoke(data),
    }
    return {"specialist_analyses": text_analyses}

def run_verification(state: GraphState):
    # ... (no changes needed)
    print("--- Running Verification ---")
    domain = state['webpage_data']['domain']
    
    brand_analyst_response_content = state['specialist_analyses']['Brand Analyst'].content
    try:
        identified_brand = next(line for line in brand_analyst_response_content.split('\n') if 'Identified Brand:' in line).split(':')[1].strip()
        if identified_brand == "N/A": identified_brand = "Unknown"
    except (StopIteration, IndexError):
        identified_brand = "Unknown"

    domain_results = search_online_knowledge.invoke({"query": domain, "search_type": "domain"})
    brand_results = search_online_knowledge.invoke({"query": identified_brand, "search_type": "brand"})
    
    return {"verification_results": {"domain_results": domain_results, "brand_results": brand_results, "identified_brand": identified_brand}}

def run_visual_specialist(state: GraphState):
    # ... (no changes needed)
    print("--- Running Visual Specialist Agent ---")
    legitimate_domains = state['verification_results'].get('brand_results', [])
    original_domain = state['webpage_data']['domain']
    
    if not legitimate_domains:
        visual_report = "Skipped: No legitimate brand domain found for comparison."
    else:
        # --- INTELLIGENT SELECTION LOGIC ---
        # Try to find an exact match for the original domain in the search results.
        # This ensures we compare amazon.com to amazon.com.
        best_match_domain = next((d for d in legitimate_domains if d in original_domain), None)
        
        # If no exact match is found, fall back to the first result.
        if not best_match_domain:
            best_match_domain = legitimate_domains[0]
        
        print(f"--- Visual Comparison Target: {best_match_domain} ---")
        legitimate_url = f"https://{best_match_domain}"
        # --- END OF NEW LOGIC ---

        legit_screenshot_path = take_screenshot_of_url.invoke(legitimate_url)
        
        if "Error:" in legit_screenshot_path:
            visual_report = legit_screenshot_path
        else:

            suspicious_b64 = image_to_base64(state['screenshot'])
            legitimate_b64 = image_to_base64(legit_screenshot_path)
            
            prompt_text = prompts.visual_anomaly_prompt.format(
                suspicious_screenshot="[Suspicious Screenshot Provided]",
                legitimate_screenshot="[Legitimate Screenshot Provided]"
            )
            vision_llm_input = [HumanMessage(content=[
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{suspicious_b64}"}},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{legitimate_b64}"}}
            ])]
            
            report = llm.invoke(vision_llm_input)
            visual_report = report.content

    updated_analyses = state['specialist_analyses']
    updated_analyses['Visual Analyst'] = visual_report
    return {"specialist_analyses": updated_analyses}

# In workflow.py

def run_judge(state: GraphState):
    print("--- Running Judge ---")
    history = {
        "specialists": {k: v.content if hasattr(v, 'content') else v for k, v in state['specialist_analyses'].items()},
        "verification": state['verification_results'],
    }
    
    # The Judge agent will generate a detailed justification
    verdict_text = create_agent_chain(prompts.judge_prompt).invoke({"history": str(history)}).content
    
    # --- ROBUST PARSING LOGIC ---
    # Look for the "Final Verdict:" line and extract the word that follows.
    decision = "BENIGN" # Default to benign if parsing fails
    try:
        verdict_line = next(line for line in verdict_text.split('\n') if 'Final Verdict:' in line)
        if "PHISHING" in verdict_line.upper():
            decision = "PHISHING"
    except (StopIteration, IndexError):
        print("Warning: Could not parse final verdict from Judge. Defaulting to BENIGN.")
    
    return {"judge_verdict": decision, "judge_reasoning": verdict_text}

# --- Node 5: Run Intent Analysis (CORRECTED) ---
def run_intent_agent(state: GraphState):
    print("--- Running Intent Agent ---")
    # CRITICAL FIX: Add the same safety check as the judge to handle strings
    analyses_content = {k: v.content if hasattr(v, 'content') else v for k, v in state['specialist_analyses'].items()}
    intention = create_agent_chain(prompts.intent_agent_prompt).invoke({
        "analyses": str(analyses_content)
    })
    return {"malicious_intention": intention.content}

# --- The rest of the file is correct and requires no changes ---

def should_run_intent_analysis(state: GraphState):
    return "run_intent_agent" if state["judge_verdict"] == "PHISHING" else END

workflow = StateGraph(GraphState)

workflow.add_node("run_text_specialists", run_text_specialists)
workflow.add_node("run_verification", run_verification)
workflow.add_node("run_visual_specialist", run_visual_specialist)
workflow.add_node("run_judge", run_judge)
workflow.add_node("run_intent_agent", run_intent_agent)

workflow.set_entry_point("run_text_specialists")
workflow.add_edge("run_text_specialists", "run_verification")
workflow.add_edge("run_verification", "run_visual_specialist")
workflow.add_edge("run_visual_specialist", "run_judge")
workflow.add_conditional_edges(
    "run_judge",
    should_run_intent_analysis,
    {
        "run_intent_agent": "run_intent_agent",
        END: END
    }
)
workflow.add_edge("run_intent_agent", END)

app = workflow.compile()