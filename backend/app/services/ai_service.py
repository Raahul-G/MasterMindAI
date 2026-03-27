"""
AI service — all Claude/OpenAI calls go through here.

Architecture:
- LearningState: shared TypedDict that flows through the LangGraph graph
- One node per AI operation (eli5, passages, quiz, remediation)
- Each public function compiles its own minimal graph and invokes it
- LLM provider (Anthropic / OpenAI) is selected via LLM_PROVIDER in .env
"""

import json
from typing import TypedDict

from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

from app.core.llm import get_llm


# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------

class LearningState(TypedDict, total=False):
    topic: str
    level: str
    user_interests: list[str]
    eli5_text: str
    passages: list[dict]
    failed_concepts: list[str]
    quiz_questions: list[dict]
    remediations: list[dict]
    prerequisite_concepts: list[str]
    learned_concepts: list[str]
    recommended_concepts: list[dict]
    existing_topics: list[str]
    canonical_name: str
    domain: str
    module_recommendations: list[dict]
    topic_connections: list[dict]


# ---------------------------------------------------------------------------
# Graph nodes
# ---------------------------------------------------------------------------

async def _eli5_node(state: LearningState) -> dict:
    topic = state["topic"]
    level = state["level"]
    interests_str = ", ".join(state["user_interests"])

    prompt = f"""You are a brilliant teacher who is amazing at explaining complex things simply.

Your task is to explain the topic "{topic}" as if you are talking to a 5-year-old child.

This specific learner is personally interested in: {interests_str}

Rules:
- You MUST build your analogy using one or more of the learner's personal interests listed above — do not use a generic analogy
- Keep it to 3-5 sentences maximum
- Do NOT use jargon or technical terms of any kind
- Start directly with the analogy — do not say "imagine" or "think of it like" as your very first word, be more creative
- Do not mention the difficulty level "{level}" at all
- End with one sentence about why this topic is interesting or useful to know

Return only the ELI5 explanation. No headings, no bullet points, no extra commentary."""

    llm = get_llm(temperature=0.7, max_tokens=400)
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"eli5_text": response.content.strip()}


async def _passages_node(state: LearningState) -> dict:
    topic = state["topic"]
    level = state["level"]
    eli5_text = state["eli5_text"]
    prerequisite_concepts = state.get("prerequisite_concepts") or []

    level_descriptions = {
        "kid": "a curious 10-12 year old child with no prior knowledge of this subject",
        "intermediate": "a university undergraduate or curious adult who knows the basics",
        "expert": "a graduate-level student or professional in a related field",
    }
    audience = level_descriptions.get(level, level_descriptions["intermediate"])

    prerequisite_line = ""
    if prerequisite_concepts:
        joined = ", ".join(prerequisite_concepts)
        prerequisite_line = (
            f"\nImportant: The learner already understands these prerequisite concepts: {joined}. "
            "Do NOT re-explain them — assume that knowledge and build directly on top of it.\n"
        )

    prompt = f"""You are an expert educator writing clear, engaging learning content.

Topic: {topic}
Audience: {audience}
{prerequisite_line}
Context: The learner has just read this introductory analogy:
"{eli5_text}"

Your task is to write exactly 2 or 3 core concept passages about "{topic}" for this audience.

Rules:
- Each passage must cover one distinct, important concept within the topic
- Each passage must have a clear, specific title (the concept name)
- Each passage should be 100-200 words
- Write at the appropriate level for the audience — not too simple, not too advanced
- Build naturally from the ELI5 analogy above
- Do NOT repeat the ELI5 analogy
- Use active voice and engaging prose

Return your response as valid JSON only, with this exact structure:
[
  {{
    "concept_title": "Title of Concept 1",
    "content": "Full passage text for concept 1..."
  }},
  {{
    "concept_title": "Title of Concept 2",
    "content": "Full passage text for concept 2..."
  }}
]

Return ONLY the JSON array. No explanation, no markdown code blocks, no extra text."""

    llm = get_llm(temperature=0.5, max_tokens=1500)
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"passages": json.loads(response.content.strip())}


async def _quiz_node(state: LearningState) -> dict:
    topic = state["topic"]
    level = state["level"]
    passages_text = "\n\n".join([
        f"CONCEPT: {p['concept_title']}\n{p['content']}"
        for p in state["passages"]
    ])

    prompt = f"""You are an expert quiz writer creating assessment questions for a learning app.

Topic: {topic}
Level: {level}

The learner has read the following passages:

{passages_text}

Your task is to write between 5 and 10 quiz questions that test understanding of ONLY the content above.

Rules:
- Each question must be either true/false or multiple choice (your choice per question)
- For multiple choice: provide exactly 4 options (A, B, C, D)
- For true/false: options array should be ["True", "False"]
- The correct_answer must exactly match one of the options strings
- Each question must be tagged with the concept_title it tests (use the exact concept titles from above)
- Do not ask questions about information not covered in the passages
- Questions should test understanding, not just word-matching

Return your response as valid JSON only, with this exact structure:
[
  {{
    "concept_title": "Title of the concept this question tests",
    "question_text": "The question text here?",
    "question_type": "multiple_choice",
    "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
    "correct_answer": "Option A text"
  }},
  {{
    "concept_title": "Title of the concept this question tests",
    "question_text": "True or false: statement here.",
    "question_type": "true_false",
    "options": ["True", "False"],
    "correct_answer": "True"
  }}
]

Return ONLY the JSON array. No explanation, no markdown code blocks, no extra text."""

    llm = get_llm(temperature=0.4, max_tokens=2000)
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"quiz_questions": json.loads(response.content.strip())}


async def _remediation_node(state: LearningState) -> dict:
    topic = state["topic"]
    failed_concepts = state["failed_concepts"]
    passages = state["passages"]

    original_text = "\n\n".join([
        f"CONCEPT: {p['concept_title']}\nORIGINAL EXPLANATION: {p['content']}"
        for p in passages
        if p["concept_title"] in failed_concepts
    ])
    failed_list = "\n".join([f"- {c}" for c in failed_concepts])

    prompt = f"""You are a patient, creative tutor helping a student who did not understand a concept on their first try.

Topic: {topic}

The student struggled with these specific concepts:
{failed_list}

Here are the original explanations they already read (DO NOT repeat these — you must use completely different analogies):
{original_text}

Your task is to re-explain ONLY the failed concepts above using entirely fresh analogies and different wording.

Rules:
- Use a completely different analogy from the original explanation — do not recycle any of the same comparisons
- Be patient, warm, and encouraging in tone
- Each remediation passage should be 100-180 words
- Focus on clarity first — the student found this difficult, so be especially clear
- Do not say "as mentioned before" or reference the original explanation at all

Return your response as valid JSON only, with this exact structure:
[
  {{
    "concept_title": "Exact concept title matching the failed concept",
    "content": "Your new remediation explanation using fresh analogies..."
  }}
]

Return ONLY the JSON array. No explanation, no markdown code blocks, no extra text."""

    llm = get_llm(temperature=0.7, max_tokens=1500)
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"remediations": json.loads(response.content.strip())}


async def _normalize_topic_node(state: LearningState) -> dict:
    topic = state["topic"]
    existing_topics = state.get("existing_topics") or []
    existing_str = ", ".join(existing_topics) if existing_topics else "none"

    prompt = f"""Topic typed by user: "{topic}"
Existing canonical topics the user has studied: [{existing_str}]

1. If this topic matches an existing one (same concept, different phrasing), return that exact canonical name.
2. Otherwise return a clean canonical name (e.g. "REST API" not "Rest Api").
3. Assign a short domain label (e.g. "Web APIs", "AI / ML", "System Design").

Return JSON only: {{"canonical_name": "<str>", "domain": "<str>"}}
No explanation, no markdown fences."""

    llm = get_llm(temperature=0.3, max_tokens=150)
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return json.loads(response.content.strip())


async def _module_recommendations_node(state: LearningState) -> dict:
    canonical_name = state["canonical_name"]
    domain = state.get("domain", "")
    level = state.get("level", "intermediate")
    learned_concepts = state.get("learned_concepts") or []
    user_interests = state.get("user_interests") or []
    existing_topics = state.get("existing_topics") or []

    learned_str = ", ".join(learned_concepts) if learned_concepts else "none"
    interests_str = ", ".join(user_interests) if user_interests else "general learning"
    existing_str = ", ".join(existing_topics) if existing_topics else "none"

    prompt = f"""The user just mastered "{canonical_name}" (domain: {domain}) at {level} level.
Concepts they learned: {learned_str}
Their interests: {interests_str}
All topics they have studied so far: [{existing_str}]

Suggest 1-2 next MODULES to learn that directly build on "{canonical_name}".
Each module should have 2 concept hints (short strings, not sentences).
Do not suggest topics already in the existing_topics list.

Return JSON only:
[{{"topic": "<str>", "canonical_name": "<str>", "domain": "<str>", "concept_hints": ["<str>", "<str>"], "reason": "<one sentence>"}}]
No explanation, no markdown fences."""

    llm = get_llm(temperature=0.6, max_tokens=400)
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"module_recommendations": json.loads(response.content.strip())}


async def _topic_connections_node(state: LearningState) -> dict:
    canonical_name = state["canonical_name"]
    domain = state.get("domain", "")
    existing_topics = state.get("existing_topics") or []

    if not existing_topics:
        return {"topic_connections": []}

    existing_str = ", ".join(existing_topics)

    prompt = f"""New topic the user just learned: "{canonical_name}" (domain: {domain})
All other topics the user has studied: [{existing_str}]

Which existing topics are meaningfully connected to "{canonical_name}"?
Think like a knowledge graph — include prerequisite, extends, and related relationships.
Only include real, non-trivial connections.

Return JSON only (empty array if none):
[{{"source": "<canonical_name>", "target": "<canonical_name>", "relationship": "prerequisite"|"extends"|"related"}}]
where source and target are canonical topic names.
No explanation, no markdown fences."""

    llm = get_llm(temperature=0.3, max_tokens=300)
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"topic_connections": json.loads(response.content.strip())}


async def _recommendation_node(state: LearningState) -> dict:
    topic = state["topic"]
    level = state["level"]
    learned_concepts = state.get("learned_concepts") or []
    user_interests = state.get("user_interests") or []

    learned_list = ", ".join(learned_concepts)
    interests_str = ", ".join(user_interests) if user_interests else "general learning"

    prompt = f"""You are a learning path advisor helping a student decide what to study next.

The student just mastered these concepts within the topic "{topic}" at {level} level:
{learned_list}

Their personal interests are: {interests_str}

Your task: suggest exactly 2 next concepts within "{topic}" that:
1. Have the above learned concepts as direct prerequisites (they naturally build on them)
2. Are the logical next step in understanding "{topic}"
3. Are distinct from what was already learned

Return your response as valid JSON only, with this exact structure:
[
  {{
    "title": "Next Concept Name",
    "reason": "One sentence explaining why this is the next step and how it builds on what was learned."
  }},
  {{
    "title": "Second Next Concept Name",
    "reason": "One sentence explaining why this is the next step."
  }}
]

Return ONLY the JSON array. No explanation, no markdown code blocks, no extra text."""

    llm = get_llm(temperature=0.6, max_tokens=300)
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"recommended_concepts": json.loads(response.content.strip())}


# ---------------------------------------------------------------------------
# Compiled graphs (built once at import time)
# ---------------------------------------------------------------------------

def _build_eli5_graph():
    g = StateGraph(LearningState)
    g.add_node("eli5", _eli5_node)
    g.add_edge(START, "eli5")
    g.add_edge("eli5", END)
    return g.compile()


def _build_passages_graph():
    g = StateGraph(LearningState)
    g.add_node("passages", _passages_node)
    g.add_edge(START, "passages")
    g.add_edge("passages", END)
    return g.compile()


def _build_quiz_graph():
    g = StateGraph(LearningState)
    g.add_node("quiz", _quiz_node)
    g.add_edge(START, "quiz")
    g.add_edge("quiz", END)
    return g.compile()


def _build_remediation_graph():
    g = StateGraph(LearningState)
    g.add_node("remediation", _remediation_node)
    g.add_edge(START, "remediation")
    g.add_edge("remediation", END)
    return g.compile()


def _build_recommendation_graph():
    g = StateGraph(LearningState)
    g.add_node("recommendation", _recommendation_node)
    g.add_edge(START, "recommendation")
    g.add_edge("recommendation", END)
    return g.compile()


def _build_normalize_topic_graph():
    g = StateGraph(LearningState)
    g.add_node("normalize_topic", _normalize_topic_node)
    g.add_edge(START, "normalize_topic")
    g.add_edge("normalize_topic", END)
    return g.compile()


def _build_module_recommendations_graph():
    g = StateGraph(LearningState)
    g.add_node("module_recommendations", _module_recommendations_node)
    g.add_edge(START, "module_recommendations")
    g.add_edge("module_recommendations", END)
    return g.compile()


def _build_topic_connections_graph():
    g = StateGraph(LearningState)
    g.add_node("topic_connections", _topic_connections_node)
    g.add_edge(START, "topic_connections")
    g.add_edge("topic_connections", END)
    return g.compile()


_eli5_graph = _build_eli5_graph()
_passages_graph = _build_passages_graph()
_quiz_graph = _build_quiz_graph()
_remediation_graph = _build_remediation_graph()
_recommendation_graph = _build_recommendation_graph()
_normalize_topic_graph = _build_normalize_topic_graph()
_module_recommendations_graph = _build_module_recommendations_graph()
_topic_connections_graph = _build_topic_connections_graph()


# ---------------------------------------------------------------------------
# Public API (called by learning_service.py)
# ---------------------------------------------------------------------------

async def generate_eli5(topic: str, level: str, user_interests: list[str]) -> str:
    result = await _eli5_graph.ainvoke({
        "topic": topic,
        "level": level,
        "user_interests": user_interests,
    })
    return result["eli5_text"]


async def generate_passages(
    topic: str,
    level: str,
    eli5_text: str,
    prerequisite_concepts: list[str] | None = None,
) -> list[dict]:
    result = await _passages_graph.ainvoke({
        "topic": topic,
        "level": level,
        "eli5_text": eli5_text,
        "prerequisite_concepts": prerequisite_concepts or [],
    })
    return result["passages"]


async def generate_quiz(topic: str, passages_content: list[dict], level: str) -> list[dict]:
    result = await _quiz_graph.ainvoke({
        "topic": topic,
        "level": level,
        "passages": passages_content,
    })
    return result["quiz_questions"]


async def generate_remediation(
    topic: str,
    failed_concepts: list[str],
    original_passages: list[dict],
) -> list[dict]:
    result = await _remediation_graph.ainvoke({
        "topic": topic,
        "failed_concepts": failed_concepts,
        "passages": original_passages,
    })
    return result["remediations"]


async def generate_concept_recommendations(
    topic: str,
    level: str,
    learned_concepts: list[str],
    user_interests: list[str],
) -> list[dict]:
    result = await _recommendation_graph.ainvoke({
        "topic": topic,
        "level": level,
        "learned_concepts": learned_concepts,
        "user_interests": user_interests,
    })
    return result["recommended_concepts"]


async def normalize_topic(topic: str, existing_topics: list[str]) -> dict:
    result = await _normalize_topic_graph.ainvoke({
        "topic": topic,
        "existing_topics": existing_topics,
    })
    return {"canonical_name": result.get("canonical_name", topic), "domain": result.get("domain")}


async def generate_module_recommendations(
    canonical_name: str,
    domain: str | None,
    level: str,
    learned_concepts: list[str],
    user_interests: list[str],
    existing_topics: list[str],
) -> list[dict]:
    result = await _module_recommendations_graph.ainvoke({
        "canonical_name": canonical_name,
        "domain": domain or "",
        "level": level,
        "learned_concepts": learned_concepts,
        "user_interests": user_interests,
        "existing_topics": existing_topics,
    })
    return result.get("module_recommendations", [])


async def detect_topic_connections(
    canonical_name: str,
    domain: str | None,
    existing_topics: list[str],
) -> list[dict]:
    result = await _topic_connections_graph.ainvoke({
        "canonical_name": canonical_name,
        "domain": domain or "",
        "existing_topics": existing_topics,
    })
    return result.get("topic_connections", [])
