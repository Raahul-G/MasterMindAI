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

    level_descriptions = {
        "kid": "a curious 10-12 year old child with no prior knowledge of this subject",
        "intermediate": "a university undergraduate or curious adult who knows the basics",
        "expert": "a graduate-level student or professional in a related field",
    }
    audience = level_descriptions.get(level, level_descriptions["intermediate"])

    prompt = f"""You are an expert educator writing clear, engaging learning content.

Topic: {topic}
Audience: {audience}

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


_eli5_graph = _build_eli5_graph()
_passages_graph = _build_passages_graph()
_quiz_graph = _build_quiz_graph()
_remediation_graph = _build_remediation_graph()


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


async def generate_passages(topic: str, level: str, eli5_text: str) -> list[dict]:
    result = await _passages_graph.ainvoke({
        "topic": topic,
        "level": level,
        "eli5_text": eli5_text,
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
