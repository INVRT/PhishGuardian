# workflow.py

import json
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict
from langchain_core.messages import HumanMessage, AIMessage
from .config import llm
from .agents import prompts
from .tools import search_online_knowledge, take_screenshot_of_url
from .utils import image_to_base64 # Assuming image_to_base64 is in utils.py

# --- CONSTANTS ---
MAX_DEBATE_ROUNDS = 2

# --- UPDATED GRAPH STATE ---
class GraphState(TypedDict):
    webpage_data: dict
    screenshot: str
    specialist_analyses: Dict[str, str] # Holds the analysis of the *current* round
    debate_history: List[Dict] # A list to store the history of each round's analyses
    round_number: int
    consensus_reached: str
    verification_results: dict
    judge_verdict: str
    judge_reasoning: str
    malicious_intention: str

# --- Agent Chain Creator ---
def create_agent_chain(prompt):
    return prompt | llm

# --- NODES FOR THE GRAPH ---

# Node 1: Initial Analysis (Round 1)
def initial_analysis(state: GraphState):
    print("--- Running Initial Analysis (Round 1) ---")
    data = state['webpage_data']
    
    # Run text specialists
    text_analysts = {
        "URL Analyst": create_agent_chain(prompts.url_analyst_prompt),
        "HTML Analyst": create_agent_chain(prompts.html_analyst_prompt),
        "Content Analyst": create_agent_chain(prompts.content_analyst_prompt),
        "Brand Analyst": create_agent_chain(prompts.brand_analyst_prompt),
    }
    
    current_analyses = {}
    for name, agent_chain in text_analysts.items():
        result = agent_chain.invoke(data)
        current_analyses[name] = result.content
        print(f"--- {name} (Round 1) ---")
        print(result.content)

    # Run verification in parallel with initial analysis for efficiency
    domain = data['domain']
    try:
        # Extract identified brand from Brand Analyst's response
        brand_response = current_analyses['Brand Analyst']
        identified_brand = next(line for line in brand_response.split('\n') if 'Identified Brand:' in line).split(':')[1].strip()
        if identified_brand.lower() == "n/a": identified_brand = "Unknown"
    except (StopIteration, IndexError):
        identified_brand = "Unknown"
        
    domain_results = search_online_knowledge.invoke({"query": domain, "search_type": "domain"})
    brand_results = search_online_knowledge.invoke({"query": identified_brand, "search_type": "brand"})
    verification_results = {"domain_results": domain_results, "brand_results": brand_results, "identified_brand": identified_brand}
    print(f"--- Verification Results ---\n{json.dumps(verification_results, indent=2)}")

    # Visual analysis is also part of the initial data gathering
    # This logic remains the same
    legitimate_domains = verification_results.get('brand_results', [])
    original_domain = data['domain']
    if not legitimate_domains:
        visual_report = "Skipped: No legitimate brand domain found for comparison."
    else:
        best_match_domain = next((d for d in legitimate_domains if d in original_domain), legitimate_domains[0])
        print(f"--- Visual Comparison Target: {best_match_domain} ---")
        legitimate_url = f"https://{best_match_domain}"
        legit_screenshot_path = take_screenshot_of_url.invoke(legitimate_url)
        if "Error:" in legit_screenshot_path:
            visual_report = legit_screenshot_path
        else:
            suspicious_b64 = image_to_base64(state['screenshot'])
            legitimate_b64 = image_to_base64(legit_screenshot_path)
            vision_llm_input = [HumanMessage(content=[
                {"type": "text", "text": prompts.visual_anomaly_prompt.template},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{suspicious_b64}"}},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{legitimate_b64}"}}
            ])]
            report = llm.invoke(vision_llm_input)
            visual_report = report.content
    
    current_analyses['Visual Analyst'] = visual_report
    print(f"--- Visual Analyst Report ---\n{visual_report}")

    # Store the results
    round_summary = {"round": 1, "analyses": current_analyses}
    
    return {
        "specialist_analyses": current_analyses,
        "debate_history": [round_summary],
        "round_number": 1,
        "verification_results": verification_results
    }

# Node 2: The Moderator
def run_moderator(state: GraphState):
    """
    Evaluates consensus and updates the state with the result.
    """
    print("--- Moderator: Evaluating Consensus ---")
    latest_analyses = state['specialist_analyses']
    
    formatted_analyses = "\n\n".join([f"**{agent}**:\n{report}" for agent, report in latest_analyses.items()])
    
    moderator_chain = create_agent_chain(prompts.moderator_prompt)
    decision = moderator_chain.invoke({"latest_analyses": formatted_analyses}).content.strip()
    
    print(f"Moderator Decision: {decision}")
    
    if "CONSENSUS" in decision:
        return {"consensus_reached": "CONSENSUS"}
    else:
        return {"consensus_reached": "CONFLICT"}

# Node 3: The Debate Round
def run_debate_round(state: GraphState):
    round_number = state['round_number'] + 1
    print(f"--- Starting Debate (Round {round_number}) ---")
    
    debate_history_str = json.dumps(state['debate_history'], indent=2)
    data = state['webpage_data']

    # Personas for the debate prompt
    personas = {
        "URL Analyst": "cybersecurity expert specializing in URL analysis",
        "HTML Analyst": "expert in web security and HTML structure",
        "Content Analyst": "cybersecurity-focused language expert",
        "Brand Analyst": "brand impersonation detection expert",
        "Visual Analyst": "visual forensics expert comparing webpage designs",
    }
    
    current_analyses = {}
    # Visual analyst does not debate, as its comparison is factual. We carry its report forward.
    current_analyses['Visual Analyst'] = state['specialist_analyses']['Visual Analyst']

    # Only text-based analysts participate in the debate
    for name in ["URL Analyst", "HTML Analyst", "Content Analyst", "Brand Analyst"]:
        debate_prompt = prompts.debate_specialist_prompt.format(
            agent_persona=personas[name],
            round_number=round_number,
            debate_history=debate_history_str,
            url=data['url'],
            html_content=data['html_content'],
            cleaned_text=data['cleaned_text']
        )
        result = llm.invoke(debate_prompt) # Using llm directly as prompt is already formatted
        current_analyses[name] = result.content
        print(f"--- {name} (Round {round_number}) ---")
        print(result.content)
        
    # Update state
    round_summary = {"round": round_number, "analyses": current_analyses}
    new_history = state['debate_history'] + [round_summary]
    
    return {
        "specialist_analyses": current_analyses,
        "debate_history": new_history,
        "round_number": round_number
    }

# Node 4: The Judge
def run_judge(state: GraphState):
    print("--- Judge: Making Final Verdict ---")
    history_str = json.dumps(state['debate_history'], indent=2)
    verification_str = json.dumps(state['verification_results'], indent=2)
    
    # Use the updated Judge prompt
    verdict_text = create_agent_chain(prompts.judge_prompt).invoke({
        "debate_history": history_str,
        "verification_results": verification_str
    }).content
    
    decision = "BENIGN"
    try:
        verdict_line = next(line for line in verdict_text.split('\n') if 'Final Verdict:' in line)
        if "PHISHING" in verdict_line.upper():
            decision = "PHISHING"
    except (StopIteration, IndexError):
        print("Warning: Could not parse final verdict from Judge. Defaulting to BENIGN.")
    
    print(f"--- Judge's Final Verdict: {decision} ---")
    return {"judge_verdict": decision, "judge_reasoning": verdict_text}

# Node 5: Intent Agent (No changes needed)
def run_intent_agent(state: GraphState):
    print("--- Running Intent Agent ---")
    final_analyses = state['debate_history'][-1]['analyses']
    analyses_str = json.dumps(final_analyses, indent=2)
    
    intention = create_agent_chain(prompts.intent_agent_prompt).invoke({
        "analyses": analyses_str
    })
    return {"malicious_intention": intention.content}

# --- Conditional Edges ---

def should_continue_debate(state: GraphState):
    """
    The routing logic for the debate loop.
    """
    if state['round_number'] >= MAX_DEBATE_ROUNDS:
        print("--- Max debate rounds reached. Proceeding to Judge. ---")
        return "end_debate"
    
    if state.get("consensus_reached") == "CONSENSUS":
        print("--- Consensus reached. Proceeding to Judge. ---")
        return "end_debate"
    else:
        print("--- Conflict detected. Continuing to next debate round. ---")
        return "continue_debate"

def should_run_intent_analysis(state: GraphState):
    return "run_intent_agent" if state["judge_verdict"] == "PHISHING" else END

# --- Build the Graph ---
workflow = StateGraph(GraphState)

workflow.add_node("initial_analysis", initial_analysis)
workflow.add_node("run_moderator", run_moderator)
workflow.add_node("run_debate_round", run_debate_round)
workflow.add_node("run_judge", run_judge)
workflow.add_node("run_intent_agent", run_intent_agent)

workflow.set_entry_point("initial_analysis")

workflow.add_edge("initial_analysis", "run_moderator")
workflow.add_edge("run_debate_round", "run_moderator")
workflow.add_edge("run_intent_agent", END) # Keep this line

# The conditional logic for the debate loop
workflow.add_conditional_edges(
    "run_moderator",
    # The router function is now separate from the node
    should_continue_debate,
    {
        "continue_debate": "run_debate_round",
        "end_debate": "run_judge"
    }
)

# The conditional logic for intent analysis
workflow.add_conditional_edges(
    "run_judge",  # <-- The source node is now the actual last step
    should_run_intent_analysis, # This function decides the next step
    {
        "run_intent_agent": "run_intent_agent",
        END: END
    }
)

app = workflow.compile()