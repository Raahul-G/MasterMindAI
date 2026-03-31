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
    covered_concepts: list[str]
    learned_concepts: list[str]
    recommended_concepts: list[dict]


# ---------------------------------------------------------------------------
# Graph nodes
# ---------------------------------------------------------------------------

async def _eli5_node(state: LearningState) -> dict:
    topic = state.get("topic", "")
    level = state.get("level", "")
    interests_str = ", ".join(state.get("user_interests") or [])

    prompt = f"""You are an enthusiastic teacher who makes complex ideas feel instantly simple and exciting.

Your job is to write the "Big Idea" for the topic "{topic}" — a short, memorable explanation that gives the learner an instant gut-feeling of what this topic is about.

This learner personally loves: {interests_str}

Rules:
- BUILD your analogy directly around ONE of the learner's specific interests above — make it feel personal
- Write 2–4 sentences maximum
- No jargon, no technical words of any kind — a 10-year-old should understand every word
- Do NOT start your first sentence with "Imagine" — be more creative and direct
- Do not mention the difficulty level "{level}"
- End with one punchy sentence on why this topic is useful or cool in real life
- Friendly, energetic tone — make the learner think "oh, that actually makes sense!"

Return only the Big Idea explanation. No headings, no bullet points, no extra text."""

    llm = get_llm(temperature=0.7, max_tokens=400)
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"eli5_text": response.content.strip()}


async def _passages_node(state: LearningState) -> dict:
    topic = state.get("topic", "")
    level = state.get("level", "")
    eli5_text = state.get("eli5_text", "")
    prerequisite_concepts = state.get("prerequisite_concepts") or []
    covered_concepts = state.get("covered_concepts") or []

    level_descriptions = {
        "kid": "a curious 10-12 year old child with no prior knowledge of this subject",
        "intermediate": "a university undergraduate or curious adult who knows the basics",
        "expert": "a graduate-level student or professional in a related field",
    }
    audience = level_descriptions.get(level, level_descriptions["intermediate"])

    context_line = ""
    all_known = list(dict.fromkeys(prerequisite_concepts + covered_concepts))
    if all_known:
        joined = ", ".join(all_known)
        context_line = (
            f"\nImportant: The learner already understands these concepts: {joined}. "
            "Do NOT re-explain them. Build on them and introduce the next 2 logical concepts.\n"
        )

    prompt = f"""You are an expert educator writing structured learning content for a learning app.

Topic: {topic}
Audience: {audience}
{context_line}
The learner has just read this Big Idea introduction:
"{eli5_text}"

Write exactly 2 concept cards about "{topic}" for this audience. These should be the next 2 logical concepts to learn, distinct from any already-covered concepts listed above.

Each concept card has THREE parts:

1. summary — ONE sentence using a simple, concrete analogy that captures the whole concept like a flashcard. No jargon. Think of this as the sticky sentence a learner will remember.

2. content — 2 to 4 sentences that explain what the concept actually is, written simply and directly for the audience. Build on the summary. Do NOT repeat the Big Idea analogy above.

3. use_cases — 2 to 3 sentences that connect the analogy to a real-world example of where and why this concept is used in practice. Make it feel tangible and useful.

Return your response as valid JSON only, with this exact structure:
[
  {{
    "concept_title": "Name of Concept 1",
    "summary": "One sentence analogy that captures the concept.",
    "content": "2-4 sentences explaining what the concept is...",
    "use_cases": "2-3 sentences on where and why it is used in real life..."
  }},
  {{
    "concept_title": "Name of Concept 2",
    "summary": "One sentence analogy that captures the concept.",
    "content": "2-4 sentences explaining what the concept is...",
    "use_cases": "2-3 sentences on where and why it is used in real life..."
  }}
]

Return ONLY the JSON array. No explanation, no markdown code blocks, no extra text."""

    llm = get_llm(temperature=0.5, max_tokens=2000)
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"passages": json.loads(response.content.strip())}


async def _quiz_node(state: LearningState) -> dict:
    topic = state.get("topic", "")
    level = state.get("level", "")
    passages = state.get("passages") or []
    passages_text = "\n\n".join([
        f"CONCEPT: {p['concept_title']}\nSUMMARY: {p.get('summary', '')}\nEXPLANATION: {p.get('content', '')}\nUSE CASES: {p.get('use_cases', '')}"
        for p in passages
    ])
    concept_list = ", ".join([f'"{p["concept_title"]}"' for p in passages])

    prompt = f"""You are an expert quiz writer for a learning app.

Topic: {topic}
Level: {level}

The learner has studied these concept cards:

{passages_text}

Concepts to cover: {concept_list}

Your task: write EXACTLY 2 questions for EACH concept above.
- Mix question types freely: true/false or multiple choice — your choice per question
- For multiple choice: exactly 4 options
- For true/false: options must be ["True", "False"]
- correct_answer must exactly match one of the options strings
- Tag each question with the exact concept_title it tests
- Test genuine understanding — not just word recall
- Do not ask about anything not covered in the concept cards above

Return your response as valid JSON only, with this exact structure:
[
  {{
    "concept_title": "Exact concept title from above",
    "question_text": "Your question here?",
    "question_type": "multiple_choice",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option A"
  }},
  {{
    "concept_title": "Exact concept title from above",
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
    topic = state.get("topic", "")
    failed_concepts = state.get("failed_concepts") or []
    passages = state.get("passages") or []

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


_eli5_graph = _build_eli5_graph()
_passages_graph = _build_passages_graph()
_quiz_graph = _build_quiz_graph()
_remediation_graph = _build_remediation_graph()
_recommendation_graph = _build_recommendation_graph()


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
    covered_concepts: list[str] | None = None,
) -> list[dict]:
    result = await _passages_graph.ainvoke({
        "topic": topic,
        "level": level,
        "eli5_text": eli5_text,
        "prerequisite_concepts": prerequisite_concepts or [],
        "covered_concepts": covered_concepts or [],
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


