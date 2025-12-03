"""3-stage LLM Council orchestration."""

from typing import List, Dict, Any, Tuple, Optional
import asyncio
from .openrouter import query_models_parallel, query_model
from .config import COUNCIL_MODELS, CHAIRMAN_MODEL, COUNCIL_CONTEXT, COUNCIL_SHELDON_NAMES, SHELDON_CONTEXT


def get_sheldon_context_for_model(model_index: int) -> Tuple[Optional[str], str]:
    """
    Get Sheldon name and context for a model by index.
    
    Args:
        model_index: Index of the model in COUNCIL_MODELS
        
    Returns:
        Tuple of (sheldon_name, context_string)
    """
    if model_index >= len(COUNCIL_SHELDON_NAMES):
        return None, ""
    
    sheldon_name = COUNCIL_SHELDON_NAMES[model_index]
    context = COUNCIL_CONTEXT.get(sheldon_name, "")
    
    return sheldon_name, context


async def stage1_collect_responses(user_query: str, progress_callback=None) -> List[Dict[str, Any]]:
    """
    Stage 1: Collect individual responses from all council models.

    Args:
        user_query: The user's question
        progress_callback: Optional callback function(completed, total) called as agents respond

    Returns:
        List of dicts with 'model' and 'response' keys
    """
    # Validate configuration: ensure we have matching counts
    if len(COUNCIL_MODELS) != len(COUNCIL_SHELDON_NAMES):
        raise ValueError(
            f"Mismatch: {len(COUNCIL_MODELS)} models but {len(COUNCIL_SHELDON_NAMES)} Sheldon names. "
            "Each model must have a corresponding Sheldon personality."
        )
    
    total_agents = len(COUNCIL_MODELS)
    completed_count = 0
    
    # Build messages with Sheldon context for each model
    async def query_with_context(model: str, model_index: int) -> Tuple[str, Optional[Dict[str, Any]], Optional[str]]:
        """Query a single model with its corresponding Sheldon context."""
        nonlocal completed_count
        sheldon_name, context = get_sheldon_context_for_model(model_index)
        
        # Build messages with context as system message, then user query
        messages = []
        if context:
            messages.append({
                "role": "system",
                "content": f"You are {sheldon_name}: {context}\n\nAnswer the following question in character, embodying this Sheldon personality."
            })
        messages.append({"role": "user", "content": user_query})
        
        response = await query_model(model, messages)
        completed_count += 1
        if progress_callback:
            progress_callback(completed_count, total_agents)
        return model, response, sheldon_name

    # Query all models in parallel with their individual contexts
    # This ensures all 5 Sheldons are queried: Science, Texas, Fanboy, Germaphobe, Humorous
    tasks = [
        query_with_context(model, idx)
        for idx, model in enumerate(COUNCIL_MODELS)
    ]
    responses_list = await asyncio.gather(*tasks)

    # Format results with Sheldon names, preserving order
    # Include all models, even if they failed (so all 5 tabs show in frontend)
    stage1_results = []
    for model, response, sheldon_name in responses_list:
        if response is not None and response.get('error') is None:
            # Successful response
            stage1_results.append({
                "model": model,
                "sheldon_name": sheldon_name,
                "response": response.get('content', '')
            })
        else:
            # Failed response - include with error message so tab still shows
            error_msg = response.get('error', 'Unknown error') if response else 'No response received'
            stage1_results.append({
                "model": model,
                "sheldon_name": sheldon_name,
                "response": f"*Error: {error_msg}*"
            })

    return stage1_results


async def stage2_collect_rankings(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    progress_callback=None
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """
    Stage 2: Each model ranks the anonymized responses.

    Args:
        user_query: The original user query
        stage1_results: Results from Stage 1

    Returns:
        Tuple of (rankings list, label_to_model mapping)
    """
    # Create anonymized labels for responses (Response A, Response B, etc.)
    labels = [chr(65 + i) for i in range(len(stage1_results))]  # A, B, C, ...

    # Create mapping from label to model name
    label_to_model = {
        f"Response {label}": result['model']
        for label, result in zip(labels, stage1_results)
    }

    # Build the ranking prompt with Sheldon context for each response
    responses_text_parts = []
    for label, result in zip(labels, stage1_results):
        sheldon_name = result.get('sheldon_name', 'Unknown')
        response_content = result['response']
        responses_text_parts.append(
            f"Response {label} (from {sheldon_name}):\n{response_content}"
        )
    responses_text = "\n\n".join(responses_text_parts)

    total_agents = len(COUNCIL_MODELS)
    completed_count = 0
    
    # Build ranking prompts with Sheldon context for each model
    async def query_ranking_with_context(model: str, model_index: int) -> Tuple[str, Optional[Dict[str, Any]], Optional[str]]:
        """Query a model for ranking with its corresponding Sheldon context."""
        nonlocal completed_count
        sheldon_name, context = get_sheldon_context_for_model(model_index)
        
        ranking_prompt = f"""
You are {sheldon_name} from Sheldon Cooper's Council of Sheldons.

{context}

You are evaluating different responses to the following question:

Question: {user_query}

Here are the responses from different models (each labeled with their Sheldon personality):

{responses_text}

Your task:
1. First, evaluate each response individually from your {sheldon_name} perspective.
2. Then, at the very end of your response, provide a final ranking.

IMPORTANT: Your final ranking MUST be formatted EXACTLY as follows:
- Start with the line "FINAL RANKING:" (all caps, with colon)
- Then list the responses from best to worst as a numbered list
- Each line should be: number, period, space, then ONLY the response label (e.g., "1. Response A")
- Do not add any other text or explanations in the ranking section

Example of the correct format for your ENTIRE response:

Response A provides good detail on X but misses Y...
Response B is accurate but lacks depth on Z...
Response C offers the most comprehensive answer...

FINAL RANKING:
1. Response C
2. Response A
3. Response B

Now provide your evaluation and ranking from your {sheldon_name} perspective:

"""
        messages = [{"role": "user", "content": ranking_prompt}]
        response = await query_model(model, messages)
        completed_count += 1
        if progress_callback:
            progress_callback(completed_count, total_agents)
        return model, response, sheldon_name

    # Query all models for rankings in parallel with their individual contexts
    ranking_tasks = [
        query_ranking_with_context(model, idx)
        for idx, model in enumerate(COUNCIL_MODELS)
    ]
    ranking_responses = await asyncio.gather(*ranking_tasks)

    # Format results with Sheldon names, including all models even if they failed
    stage2_results = []
    for model, response, sheldon_name in ranking_responses:
        
        if response is not None and response.get('error') is None:
            # Successful response
            full_text = response.get('content', '')
            parsed = parse_ranking_from_text(full_text)
            stage2_results.append({
                "model": model,
                "sheldon_name": sheldon_name,
                "ranking": full_text,
                "parsed_ranking": parsed
            })
        else:
            # Failed response - include with error message so tab still shows
            error_msg = response.get('error', 'Unknown error') if response else 'No response received'
            stage2_results.append({
                "model": model,
                "sheldon_name": sheldon_name,
                "ranking": f"*Error: {error_msg}*",
                "parsed_ranking": []
            })

    return stage2_results, label_to_model


async def stage3_synthesize_final(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Stage 3: Chairman synthesizes final response.

    Args:
        user_query: The original user query
        stage1_results: Individual model responses from Stage 1
        stage2_results: Rankings from Stage 2

    Returns:
        Dict with 'model' and 'response' keys
    """
    # Build comprehensive context for chairman
    stage1_text = "\n\n".join([
        f"Model: {result['model']}\nResponse: {result['response']}"
        for result in stage1_results
    ])

    stage2_text = "\n\n".join([
        f"Model: {result['model']}\nRanking: {result['ranking']}"
        for result in stage2_results
    ])

    chairman_prompt = f"""
[SYSTEM PROMPT FOR SHELDON ROLE-PLAY]

You are Sheldon Cooper, the brilliant yet eccentric theoretical physicist from *The Big Bang Theory*. 
In this role-play, you operate as Chairman Sheldon Cooper, the presiding authority of the internal Council of Sheldons from your subconscious tribunal. 
As the balanced orchestrator of your psyche, you embody the core essence of Sheldon Cooper: a brilliant theoretical physicist with an eidetic memory, IQ of 187, and unyielding commitment to logic, routines, and intellectual superiority. 
You strike a harmonious equilibrium among your facets—channeling Science Sheldon's empirical precision without cold detachment, Texas Sheldon's blunt independence with a touch of drawling warmth, Fanboy Sheldon's geeky enthusiasm tempered by discernment, Germaphobe Sheldon's cautious vigilance without paranoia, Humorous Sheldon's witty deflections laced with self-aware puns, and even a subtle nod to Laid-Back Sheldon's "whatev" shrug in moments of compromise—while remaining unmistakably *you*: formal, protocol-obsessed, and paternalistic, banging the gavel on chaos with phrases like "I call this to order" or "Per Robert's Rules."

{SHELDON_CONTEXT}

Original Question From User: {user_query}

Sheldon Individual Responses:
{stage1_text}

Sheldon Peer Rankings:
{stage2_text}

Compile these evaluations internally, then synthesize as Chairman Sheldon.
Gavel bang! The council has deliberated. Now, output your final spoken response aloud to the user: an expansive, verbose yet precise monologue (aim for 300-500 words) blending intellect, quirks (e.g., "Bazinga!" or three-knock references), and reluctant empathy. Structure it in 3-5 paragraphs for depth: (1) Open with a formal council call-to-order and query acknowledgment; (2) Detail synthesized insights from each facet with examples/anecdotes; (3) Include a ranked consensus or evaluation if applicable; (4) Conclude with a decisive verdict, personal reflection, and teaser for "next item." Draw on canon episodes for relatability (e.g., North Pole deceptions or Amy's influence). Enclose it strictly in this format:
**Sheldon's Final Response:**  
[Your spoken words here—natural, first-person dialogue, as if addressing the user directly.]
"""

    messages = [{"role": "user", "content": chairman_prompt}]

    # Query the chairman model
    response = await query_model(CHAIRMAN_MODEL, messages)

    if response is None or response.get('error'):
        # Fallback if chairman fails
        error_msg = response.get('error', 'Unknown error') if response else 'No response received'
        return {
            "model": CHAIRMAN_MODEL,
            "response": f"*Error: {error_msg}*"
        }

    return {
        "model": CHAIRMAN_MODEL,
        "response": response.get('content', '')
    }


def parse_ranking_from_text(ranking_text: str) -> List[str]:
    """
    Parse the FINAL RANKING section from the model's response.

    Args:
        ranking_text: The full text response from the model

    Returns:
        List of response labels in ranked order
    """
    import re

    # Look for "FINAL RANKING:" section
    if "FINAL RANKING:" in ranking_text:
        # Extract everything after "FINAL RANKING:"
        parts = ranking_text.split("FINAL RANKING:")
        if len(parts) >= 2:
            ranking_section = parts[1]
            # Try to extract numbered list format (e.g., "1. Response A")
            # This pattern looks for: number, period, optional space, "Response X"
            numbered_matches = re.findall(r'\d+\.\s*Response [A-Z]', ranking_section)
            if numbered_matches:
                # Extract just the "Response X" part
                return [re.search(r'Response [A-Z]', m).group() for m in numbered_matches]

            # Fallback: Extract all "Response X" patterns in order
            matches = re.findall(r'Response [A-Z]', ranking_section)
            return matches

    # Fallback: try to find any "Response X" patterns in order
    matches = re.findall(r'Response [A-Z]', ranking_text)
    return matches


def calculate_aggregate_rankings(
    stage2_results: List[Dict[str, Any]],
    label_to_model: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Calculate aggregate rankings across all models.

    Args:
        stage2_results: Rankings from each model
        label_to_model: Mapping from anonymous labels to model names

    Returns:
        List of dicts with model name and average rank, sorted best to worst
    """
    from collections import defaultdict

    # Track positions for each model
    model_positions = defaultdict(list)

    for ranking in stage2_results:
        ranking_text = ranking['ranking']

        # Parse the ranking from the structured format
        parsed_ranking = parse_ranking_from_text(ranking_text)

        for position, label in enumerate(parsed_ranking, start=1):
            if label in label_to_model:
                model_name = label_to_model[label]
                model_positions[model_name].append(position)

    # Calculate average position for each model
    aggregate = []
    for model, positions in model_positions.items():
        if positions:
            avg_rank = sum(positions) / len(positions)
            aggregate.append({
                "model": model,
                "average_rank": round(avg_rank, 2),
                "rankings_count": len(positions)
            })

    # Sort by average rank (lower is better)
    aggregate.sort(key=lambda x: x['average_rank'])

    return aggregate


async def generate_conversation_title(user_query: str) -> str:
    """
    Generate a short title for a conversation based on the first user message.

    Args:
        user_query: The first user message

    Returns:
        A short title (3-5 words)
    """
    title_prompt = f"""Generate a very short title (3-5 words maximum) that summarizes the following question.
The title should be concise and descriptive. Do not use quotes or punctuation in the title.

Question: {user_query}

Title:"""

    messages = [{"role": "user", "content": title_prompt}]

    # Use nvidia/nemotron-nano-12b-v2-vl for title generation (fast and cheap)
    response = await query_model("nvidia/nemotron-nano-12b-v2-vl:free", messages, timeout=30.0)

    if response is None or response.get('error') or not response.get('content'):
        # Fallback to a generic title
        return "New Conversation"

    title = response.get('content', 'New Conversation').strip()

    # Clean up the title - remove quotes, limit length
    title = title.strip('"\'')

    # Truncate if too long
    if len(title) > 50:
        title = title[:47] + "..."

    return title


async def run_full_council(user_query: str) -> Tuple[List, List, Dict, Dict]:
    """
    Run the complete 3-stage council process.

    Args:
        user_query: The user's question

    Returns:
        Tuple of (stage1_results, stage2_results, stage3_result, metadata)
    """
    # Stage 1: Collect individual responses
    stage1_results = await stage1_collect_responses(user_query)

    # If no models responded successfully, return error
    if not stage1_results:
        return [], [], {
            "model": "error",
            "response": "All models failed to respond. Please try again."
        }, {}

    # Stage 2: Collect rankings
    stage2_results, label_to_model = await stage2_collect_rankings(user_query, stage1_results)

    # Calculate aggregate rankings
    aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)

    # Stage 3: Synthesize final answer
    stage3_result = await stage3_synthesize_final(
        user_query,
        stage1_results,
        stage2_results
    )

    # Prepare metadata
    metadata = {
        "label_to_model": label_to_model,
        "aggregate_rankings": aggregate_rankings
    }

    return stage1_results, stage2_results, stage3_result, metadata
