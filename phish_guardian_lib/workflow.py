import base64
from langgraph.graph import StateGraph, END
from typing import TypedDict, Dict
# 1. IMPORT THE CORRECT MESSAGE CLASS
from langchain_core.messages import HumanMessage
from .config import llm
from .agents import prompts
from .tools import search_online_knowledge, take_screenshot_of_url

# --- The rest of the file is the same until run_visual_analysis ---

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

# Specialist and Verification nodes are correct...
def run_specialists(state: GraphState):
    print("--- Running Specialist Agents ---")
    data = state['webpage_data']
    
    analyses = {
        "URL Analyst": create_agent_chain(prompts.url_analyst_prompt).invoke(data),
        "HTML Analyst": create_agent_chain(prompts.html_analyst_prompt).invoke(data),
        "Content Analyst": create_agent_chain(prompts.content_analyst_prompt).invoke(data),
        "Brand Analyst": create_agent_chain(prompts.brand_analyst_prompt).invoke(data)
    }
    return {"specialist_analyses": analyses}

def run_verification(state: GraphState):
    print("--- Running Verification ---")
    domain = state['webpage_data']['domain']
    
    brand_analyst_response_content = state['specialist_analyses']['Brand Analyst'].content
    try:
        identified_brand = next(line for line in brand_analyst_response_content.split('\n') if 'Evidence:' in line).split(':')[1].strip()
    except (StopIteration, IndexError):
        identified_brand = "Unknown"

    domain_results = search_online_knowledge.invoke({"query": domain, "search_type": "domain"})
    brand_results = search_online_knowledge.invoke({"query": identified_brand, "search_type": "brand"})
    
    return {"verification_results": {"domain_results": domain_results, "brand_results": brand_results, "identified_brand": identified_brand}}


# --- Node 3: Run Visual Anomaly Analysis (CORRECTED) ---
def run_visual_analysis(state: GraphState):
    print("--- Running Visual Anomaly Agent ---")
    legitimate_domains = state['verification_results'].get('brand_results', [])
    if not legitimate_domains:
        return {"visual_analysis_report": "Error: No legitimate domain found for comparison."}

    legitimate_url = f"https://{legitimate_domains[0]}"
    legit_screenshot_path = take_screenshot_of_url.invoke(legitimate_url)

    if "Error:" in legit_screenshot_path:
        return {"visual_analysis_report": legit_screenshot_path}

    suspicious_b64 = image_to_base64(state['screenshot'])
    legitimate_b64 = image_to_base64(legit_screenshot_path)

    # 2. Get the formatted text from the prompt
    prompt_text = prompts.visual_anomaly_prompt.format(
        suspicious_screenshot="[Suspicious Screenshot Provided]",
        legitimate_screenshot="[Legitimate Screenshot Provided]"
    )

    # 3. CONSTRUCT THE CORRECT HumanMessage OBJECT
    vision_llm_input = [
        HumanMessage(
            content=[
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{suspicious_b64}"}},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{legitimate_b64}"}}
            ]
        )
    ]
    
    report = llm.invoke(vision_llm_input)
    
    return {"visual_analysis_report": report.content}


# --- The rest of the file is correct ---

def run_judge(state: GraphState):
    print("--- Running Judge ---")
    history = {
        "specialists": {k: v.content for k, v in state['specialist_analyses'].items()},
        "verification": state['verification_results'],
        "visual_analysis": state.get('visual_analysis_report', 'Not available')
    }
    verdict = create_agent_chain(prompts.judge_prompt).invoke({"history": str(history)})
    
    decision = "PHISHING" if "PHISHING" in verdict.content.upper() else "BENIGN"
    return {"judge_verdict": decision, "judge_reasoning": verdict.content}

def run_intent_agent(state: GraphState):
    print("--- Running Intent Agent ---")
    analyses_content = {k: v.content for k, v in state['specialist_analyses'].items()}
    intention = create_agent_chain(prompts.intent_agent_prompt).invoke({
        "analyses": str(analyses_content)
    })
    return {"malicious_intention": intention.content}

def should_run_intent_analysis(state: GraphState):
    return "run_intent_agent" if state["judge_verdict"] == "PHISHING" else END

workflow = StateGraph(GraphState)

workflow.add_node("run_specialists", run_specialists)
workflow.add_node("run_verification", run_verification)
workflow.add_node("run_visual_analysis", run_visual_analysis)
workflow.add_node("run_judge", run_judge)
workflow.add_node("run_intent_agent", run_intent_agent)

workflow.set_entry_point("run_specialists")
workflow.add_edge("run_specialists", "run_verification")
workflow.add_edge("run_verification", "run_visual_analysis")
workflow.add_edge("run_visual_analysis", "run_judge")
workflow.add_conditional_edges("run_judge", should_run_intent_analysis, { "run_intent_agent": "run_intent_agent", END: END })
workflow.add_edge("run_intent_agent", END)

app = workflow.compile()