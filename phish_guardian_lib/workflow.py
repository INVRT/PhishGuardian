from langgraph.graph import StateGraph, END
from typing import TypedDict, Dict
from .config import llm
from .agents import prompts
from .tools.online_search import search_online_knowledge
from .tools import take_screenshot_of_url

# --- 1. Define Graph State ---
class GraphState(TypedDict):
    screenshot: str  # Path to the suspicious screenshot
    specialist_analyses: Dict[str, str]
    visual_analysis_report: dict # To store the visual agent's findings
    verification_results: dict
    judge_verdict: str
    judge_reasoning: str
    malicious_intention: str

# Helper to create agent chains
def create_agent_chain(prompt):
    return prompt | llm

# --- Node 1: Run Specialist Agents ---
def run_specialists(state: GraphState):
    print("--- Running Specialist Agents ---")
    data = state['webpage_data']
    
    # In a real scenario, you could run these in parallel
    analyses = {
        "URL Analyst": create_agent_chain(prompts.url_analyst_prompt).invoke(data),
        "HTML Analyst": create_agent_chain(prompts.html_analyst_prompt).invoke(data),
        "Content Analyst": create_agent_chain(prompts.content_analyst_prompt).invoke(data),
        "Brand Analyst": create_agent_chain(prompts.brand_analyst_prompt).invoke(data)
    }
    return {"specialist_analyses": analyses}

# --- Node 2: Run Verification ---
def run_verification(state: GraphState):
    print("--- Running Verification ---")
    domain = state['webpage_data']['domain']
    # A more advanced agent could extract the brand from the Brand Analyst's response
    # Dynamically get the brand from the Brand Analyst's response
    brand_analyst_response = state['specialist_analyses']['Brand Analyst']
    # This is a simple parsing. You might need a more robust method
    # depending on the exact output format of your Brand Analyst.
    try:
        # Assuming the agent's output is something like "Claim: Impersonating Microsoft. Evidence: ..."
        identified_brand = brand_analyst_response.content.split("Impersonating ")[1].split(".")[0]
    except IndexError:
        identified_brand = "Unknown"

    brand_results = search_online_knowledge.invoke({"query": identified_brand, "search_type": "brand"})
        
    domain_results = search_online_knowledge.invoke({"query": domain, "search_type": "domain"})
    
    return {"verification_results": {"domain": domain_results, "brand": brand_results}}


def run_visual_analysis(state: GraphState):
    print("--- Running Visual Anomaly Agent ---")

    legitimate_domains = state['verification_results'].get('brand_results', [])
    if not legitimate_domains:
        return {"visual_analysis_report": {"error": "No legitimate domain found for comparison."}}

    # Use the new, dedicated screenshot tool
    legitimate_url = f"http://{legitimate_domains[0]}"
    legit_screenshot_path = take_screenshot_of_url.invoke(legitimate_url)

    if "Error:" in legit_screenshot_path:
        return {"visual_analysis_report": {"error": legit_screenshot_path}}

    # The rest of the function remains the same...
    report = create_agent_chain(prompts.visual_anomaly_prompt).invoke({
        "suspicious_screenshot": state['screenshot'],
        "legitimate_screenshot": legit_screenshot_path
    })

    return {"visual_analysis_report": report}

# --- Node 3: Run the Judge ---
def run_judge(state: GraphState):
    print("--- Running Judge ---")
    history = {
        "specialists": state['specialist_analyses'],
        "verification": state['verification_results'],
        "visual_analysis": state['visual_analysis_report'] 
    }
    verdict = create_agent_chain(prompts.judge_prompt).invoke({"history": str(history)})
    # In a real app, you'd parse this more robustly
    decision = "PHISHING" if "PHISHING" in verdict.content.upper() else "BENIGN"
    return {"judge_verdict": decision, "judge_reasoning": verdict.content}

# --- Node 4: Run Intent Analysis (Conditional) ---
def run_intent_agent(state: GraphState):
    print("--- Running Intent Agent ---")
    intention = create_agent_chain(prompts.intent_agent_prompt).invoke({
        "analyses": str(state['specialist_analyses'])
    })
    return {"malicious_intention": intention.content}

# --- Conditional Edge Logic ---
def should_run_intent_analysis(state: GraphState):
    if state["judge_verdict"] == "PHISHING":
        return "run_intent_agent"
    else:
        return "end"

# --- 4. Assemble the Graph ---
# --- Update 4. Assemble the Graph ---
workflow = StateGraph(GraphState)

# Add all nodes, including the new one
workflow.add_node("run_specialists", run_specialists)
workflow.add_node("run_verification", run_verification)
workflow.add_node("run_visual_analysis", run_visual_analysis) # New node
workflow.add_node("run_judge", run_judge)
workflow.add_node("run_intent_agent", run_intent_agent)

# Define the new workflow sequence
workflow.set_entry_point("run_specialists")
workflow.add_edge("run_specialists", "run_verification")
workflow.add_edge("run_verification", "run_visual_analysis") # New edge
workflow.add_edge("run_visual_analysis", "run_judge")       # New edge
workflow.add_conditional_edges(
    "run_judge",
    should_run_intent_analysis,
    {"run_intent_agent": "run_intent_agent", "end": END}
)
workflow.add_edge("run_intent_agent", END)

# Compile the app
app = workflow.compile()