import pytest
from app.services.ai_service import (
    generate_eli5,
    generate_passages,
    generate_quiz,
    generate_remediation,
)


@pytest.mark.asyncio
async def test_generate_eli5_returns_string():
    result = await generate_eli5("Photosynthesis", "intermediate", ["football", "cooking"])
    assert isinstance(result, str)
    assert len(result) > 50
    print(f"\nELI5 output:\n{result}")


@pytest.mark.asyncio
async def test_generate_passages_returns_list_of_dicts():
    eli5 = await generate_eli5("Photosynthesis", "intermediate", ["football", "cooking"])
    passages = await generate_passages("Photosynthesis", "intermediate", eli5)
    assert isinstance(passages, list)
    assert len(passages) >= 2
    assert "concept_title" in passages[0]
    assert "content" in passages[0]
    print(f"\nPassages output:\n{passages}")


@pytest.mark.asyncio
async def test_generate_quiz_returns_valid_questions():
    eli5 = await generate_eli5("Photosynthesis", "intermediate", ["football"])
    passages = await generate_passages("Photosynthesis", "intermediate", eli5)
    questions = await generate_quiz("Photosynthesis", passages, "intermediate")
    assert isinstance(questions, list)
    assert len(questions) >= 5
    for q in questions:
        assert "question_text" in q
        assert "options" in q
        assert "correct_answer" in q
        assert q["correct_answer"] in q["options"]
    print(f"\nQuiz output:\n{questions}")


@pytest.mark.asyncio
async def test_generate_remediation_uses_different_content():
    eli5 = await generate_eli5("Photosynthesis", "intermediate", ["football"])
    passages = await generate_passages("Photosynthesis", "intermediate", eli5)
    failed = [passages[0]["concept_title"]]
    remediations = await generate_remediation("Photosynthesis", failed, passages)
    assert isinstance(remediations, list)
    assert len(remediations) >= 1
    assert remediations[0]["concept_title"] == failed[0]
    assert remediations[0]["content"] != passages[0]["content"]
    print(f"\nRemediation output:\n{remediations}")
