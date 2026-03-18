# Milestone 2 — AI Service and Learning API

> **Covers:** Stage 4 (Core AI Service) + Stage 5 (Learning Module API)
> **Status:** Not started

---

## What this milestone is

Milestone 1 gave you a working auth system. Milestone 2 gives you the entire learning engine — the thing that makes MasterMind actually work.

There are two parts:

1. **The AI Service** — four isolated Python functions that call Claude to generate content (ELI5, passages, quiz, remediation). These are tested completely in isolation before being wired to any route.
2. **The Learning API** — the database models, services, and routes that orchestrate the full learn → quiz → remediate loop, saving everything to Supabase.

Every feature in the app depends on this milestone being complete.

## What you will be able to do when this milestone is done

- Call `POST /learn/start` with a topic and level and receive a personalised ELI5 + 2-3 passages back
- Call `POST /learn/quiz/generate` and receive 5-10 quiz questions based on those passages
- Call `POST /learn/quiz/submit` with answers and receive a score and list of failed concepts
- Call `POST /learn/remediate` for failed concepts and receive brand new explanations using different analogies
- See all learning data (modules, passages, quizzes, questions, answers, remediations) saved in Supabase
- Have 8 automated tests passing: 4 for AI functions, 4 for quiz scoring logic

---

## The chunks

Each chunk is one focused block of work. Complete and test each one before moving to the next.

---

### Chunk 1 — Add the Anthropic API key

**What you learn:** Where to get an Anthropic API key and how it connects your app to Claude.

- [ ] Go to https://console.anthropic.com → API Keys → Create a new key
- [ ] Copy the key (it starts with `sk-ant-`)
- [ ] Open `backend/.env` and replace `sk-ant-your-key-here` with your real key:
  ```
  ANTHROPIC_API_KEY=sk-ant-api03-your-real-key-here
  ```
- [ ] Restart the server so the new key is loaded

**Outcome:** Your backend can now authenticate with the Anthropic API and make Claude calls.

---

### Chunk 2 — Write `ai_service.py` (all 4 Claude functions)

**What you learn:** How to call Claude from Python using the official SDK, why prompts are kept in one file, and what temperature controls.

- [ ] Create `backend/app/services/ai_service.py`:
  ```python
  import anthropic
  import json
  from app.core.config import settings


  async def generate_eli5(topic: str, level: str, user_interests: list[str]) -> str:
      """
      Generate an ELI5 for any topic using one of the user's personal interests as the analogy.
      Temperature 0.7 — creative and imaginative.
      Max tokens 400 — short and punchy.
      """
      interests_str = ", ".join(user_interests)

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

      client = anthropic.AsyncAnthropic()
      message = await client.messages.create(
          model="claude-sonnet-4-20250514",
          max_tokens=400,
          temperature=0.7,
          messages=[{"role": "user", "content": prompt}]
      )
      return message.content[0].text.strip()


  async def generate_passages(topic: str, level: str, eli5_text: str) -> list[dict]:
      """
      Generate 2-3 core concept passages at the user's chosen difficulty level.
      Temperature 0.5 — balanced between accuracy and interesting prose.
      Max tokens 1500 — enough for three detailed passages.
      Returns [{"concept_title": str, "content": str}]
      """
      level_descriptions = {
          "kid": "a curious 10-12 year old child with no prior knowledge of this subject",
          "intermediate": "a university undergraduate or curious adult who knows the basics",
          "expert": "a graduate-level student or professional in a related field"
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

      client = anthropic.AsyncAnthropic()
      message = await client.messages.create(
          model="claude-sonnet-4-20250514",
          max_tokens=1500,
          temperature=0.5,
          messages=[{"role": "user", "content": prompt}]
      )
      return json.loads(message.content[0].text.strip())


  async def generate_quiz(topic: str, passages_content: list[dict], level: str) -> list[dict]:
      """
      Generate 5-10 quiz questions based directly on the passages.
      Each question is tagged to the concept_title it tests.
      Temperature 0.4 — factually accurate questions.
      Max tokens 2000 — enough for up to 10 detailed questions.
      Returns [{"concept_title": str, "question_text": str, "question_type": str, "options": list, "correct_answer": str}]
      """
      passages_text = "\n\n".join([
          f"CONCEPT: {p['concept_title']}\n{p['content']}"
          for p in passages_content
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

      client = anthropic.AsyncAnthropic()
      message = await client.messages.create(
          model="claude-sonnet-4-20250514",
          max_tokens=2000,
          temperature=0.4,
          messages=[{"role": "user", "content": prompt}]
      )
      return json.loads(message.content[0].text.strip())


  async def generate_remediation(
      topic: str,
      failed_concepts: list[str],
      original_passages: list[dict]
  ) -> list[dict]:
      """
      Generate brand new remediation explanations for failed concepts.
      Uses completely different analogies from the original passages.
      Temperature 0.7 — high creativity to find fresh analogies.
      Max tokens 1500 — enough for 2-3 remediation passages.
      Returns [{"concept_title": str, "content": str}]
      """
      original_text = "\n\n".join([
          f"CONCEPT: {p['concept_title']}\nORIGINAL EXPLANATION: {p['content']}"
          for p in original_passages
          if p['concept_title'] in failed_concepts
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

      client = anthropic.AsyncAnthropic()
      message = await client.messages.create(
          model="claude-sonnet-4-20250514",
          max_tokens=1500,
          temperature=0.7,
          messages=[{"role": "user", "content": prompt}]
      )
      return json.loads(message.content[0].text.strip())
  ```

**Outcome:** All 4 Claude functions exist as Python code. They are not connected to any route yet.

---

### Chunk 3 — Test `ai_service.py` in isolation

**What you learn:** Why you test AI functions before wiring them to routes, and how to read and verify Claude output.

- [ ] Create `backend/tests/test_ai_service.py`:
  ```python
  import pytest
  import asyncio
  from app.services.ai_service import generate_eli5, generate_passages, generate_quiz, generate_remediation


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
  ```
- [ ] Add asyncio mode to `backend/pytest.ini` (create this file):
  ```ini
  [pytest]
  asyncio_mode = auto
  ```
- [ ] Run the tests:
  ```bash
  pytest tests/test_ai_service.py -v -s
  ```
- [ ] Confirm all 4 tests pass and read the printed Claude output — verify it looks sensible

**Outcome:** All 4 AI functions are proven to work before being wired to any route.

---

### Chunk 4 — Write the learning models and run the migration

**What you learn:** How to model a relational database with foreign keys, and how Alembic handles multiple tables across multiple migrations.

- [ ] Create `backend/app/models/learning.py`:
  ```python
  import uuid
  from sqlalchemy import String, Text, Integer, Boolean, JSONB, ForeignKey, DateTime, func
  from sqlalchemy.orm import Mapped, mapped_column, relationship
  from sqlalchemy.dialects.postgresql import UUID
  from datetime import datetime
  from app.core.database import Base


  class Module(Base):
      __tablename__ = "modules"

      id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
      topic: Mapped[str] = mapped_column(String(255), nullable=False)
      level: Mapped[str] = mapped_column(String(50), nullable=False)
      eli5_text: Mapped[str] = mapped_column(Text, nullable=False)
      status: Mapped[str] = mapped_column(String(50), default="in_progress", nullable=False)
      markdown_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
      notion_page_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
      completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
      created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
      updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

      passages: Mapped[list["Passage"]] = relationship("Passage", back_populates="module", cascade="all, delete-orphan")
      quizzes: Mapped[list["Quiz"]] = relationship("Quiz", back_populates="module", cascade="all, delete-orphan")


  class Passage(Base):
      __tablename__ = "passages"

      id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      module_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False)
      concept_title: Mapped[str] = mapped_column(String(255), nullable=False)
      content: Mapped[str] = mapped_column(Text, nullable=False)
      order_index: Mapped[int] = mapped_column(Integer, nullable=False)
      created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
      updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

      module: Mapped["Module"] = relationship("Module", back_populates="passages")
      questions: Mapped[list["Question"]] = relationship("Question", back_populates="passage")
      remediations: Mapped[list["Remediation"]] = relationship("Remediation", back_populates="passage")


  class Quiz(Base):
      __tablename__ = "quizzes"

      id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      module_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False)
      attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
      score: Mapped[int | None] = mapped_column(Integer, nullable=True)
      total_questions: Mapped[int | None] = mapped_column(Integer, nullable=True)
      passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
      submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
      created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
      updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

      module: Mapped["Module"] = relationship("Module", back_populates="quizzes")
      questions: Mapped[list["Question"]] = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
      answers: Mapped[list["Answer"]] = relationship("Answer", back_populates="quiz", cascade="all, delete-orphan")
      remediations: Mapped[list["Remediation"]] = relationship("Remediation", back_populates="quiz")


  class Question(Base):
      __tablename__ = "questions"

      id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      quiz_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
      passage_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("passages.id", ondelete="CASCADE"), nullable=False)
      question_text: Mapped[str] = mapped_column(Text, nullable=False)
      question_type: Mapped[str] = mapped_column(String(50), nullable=False)
      options: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
      correct_answer: Mapped[str] = mapped_column(String(500), nullable=False)
      order_index: Mapped[int] = mapped_column(Integer, nullable=False)
      created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
      updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

      quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="questions")
      passage: Mapped["Passage"] = relationship("Passage", back_populates="questions")
      answers: Mapped[list["Answer"]] = relationship("Answer", back_populates="question")


  class Answer(Base):
      __tablename__ = "answers"

      id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      quiz_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
      question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
      user_answer: Mapped[str] = mapped_column(String(500), nullable=False)
      is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
      created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
      updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

      quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="answers")
      question: Mapped["Question"] = relationship("Question", back_populates="answers")


  class Remediation(Base):
      __tablename__ = "remediations"

      id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      module_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False)
      passage_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("passages.id", ondelete="CASCADE"), nullable=False)
      quiz_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
      content: Mapped[str] = mapped_column(Text, nullable=False)
      created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
      updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

      passage: Mapped["Passage"] = relationship("Passage", back_populates="remediations")
      quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="remediations")
  ```
- [ ] Update `backend/app/models/__init__.py` to import all models:
  ```python
  from app.models.user import User
  from app.models.learning import Module, Passage, Quiz, Question, Answer, Remediation
  ```
- [ ] Generate and apply the migration:
  ```bash
  alembic revision --autogenerate -m "add_learning_tables"
  alembic upgrade head
  ```
- [ ] Open Supabase → Table Editor → verify these tables exist: `modules`, `passages`, `quizzes`, `questions`, `answers`, `remediations`

**Outcome:** All 6 learning tables exist in your Supabase database.

---

### Chunk 5 — Write the learning and quiz Pydantic schemas

**What you learn:** How to design request/response shapes for more complex, multi-step API flows.

- [ ] Create `backend/app/schemas/learning.py`:
  ```python
  from pydantic import BaseModel
  import uuid
  from datetime import datetime


  class StartModuleRequest(BaseModel):
      topic: str
      level: str


  class PassageResponse(BaseModel):
      id: uuid.UUID
      concept_title: str
      content: str
      order_index: int

      model_config = {"from_attributes": True}


  class StartModuleResponse(BaseModel):
      module_id: uuid.UUID
      eli5_text: str
      passages: list[PassageResponse]


  class GenerateQuizRequest(BaseModel):
      module_id: uuid.UUID


  class QuestionResponse(BaseModel):
      id: uuid.UUID
      concept_title: str
      question_text: str
      question_type: str
      options: list[str]
      order_index: int

      model_config = {"from_attributes": True}


  class GenerateQuizResponse(BaseModel):
      quiz_id: uuid.UUID
      questions: list[QuestionResponse]


  class AnswerSubmission(BaseModel):
      question_id: uuid.UUID
      user_answer: str


  class SubmitQuizRequest(BaseModel):
      quiz_id: uuid.UUID
      answers: list[AnswerSubmission]


  class SubmitQuizResponse(BaseModel):
      score: int
      total: int
      passed: bool
      failed_concepts: list[str]


  class RemediateRequest(BaseModel):
      module_id: uuid.UUID
      quiz_id: uuid.UUID
      failed_concepts: list[str]


  class RemediationResponse(BaseModel):
      concept_title: str
      content: str


  class RemediateResponse(BaseModel):
      remediations: list[RemediationResponse]


  class ModuleListItem(BaseModel):
      id: uuid.UUID
      topic: str
      level: str
      status: str
      completed_at: datetime | None

      model_config = {"from_attributes": True}
  ```

**Outcome:** Every learning API request and response has a validated shape.

---

### Chunk 6 — Write `quiz_service.py` (scoring logic)

**What you learn:** How to separate pure logic (scoring) from orchestration (saving to DB), and why this makes testing easier.

- [ ] Create `backend/app/services/quiz_service.py`:
  ```python
  from sqlalchemy.ext.asyncio import AsyncSession
  from sqlalchemy import select, func
  from app.models.learning import Quiz, Question, Answer, Passage
  from app.schemas.learning import AnswerSubmission
  import uuid
  from datetime import datetime, timezone


  async def score_quiz(
      quiz_id: uuid.UUID,
      answer_submissions: list[AnswerSubmission],
      db: AsyncSession
  ) -> dict:
      """
      Scores a quiz by comparing user answers to correct answers.
      Saves all answers to the database.
      Returns score, total, passed flag, and list of failed concept titles.
      """
      result = await db.execute(
          select(Question).where(Question.quiz_id == quiz_id)
      )
      questions = result.scalars().all()
      questions_by_id = {q.id: q for q in questions}

      correct_count = 0
      failed_passage_ids = set()

      for submission in answer_submissions:
          question = questions_by_id.get(submission.question_id)
          if not question:
              continue

          is_correct = submission.user_answer.strip() == question.correct_answer.strip()
          if is_correct:
              correct_count += 1
          else:
              failed_passage_ids.add(question.passage_id)

          answer = Answer(
              quiz_id=quiz_id,
              question_id=submission.question_id,
              user_answer=submission.user_answer,
              is_correct=is_correct,
          )
          db.add(answer)

      total = len(answer_submissions)
      passed = correct_count == total

      # Update quiz record with results
      quiz_result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
      quiz = quiz_result.scalar_one_or_none()
      if quiz:
          quiz.score = correct_count
          quiz.total_questions = total
          quiz.passed = passed
          quiz.submitted_at = datetime.now(timezone.utc)

      await db.commit()

      # Fetch failed concept titles from the passages
      failed_concepts = []
      if failed_passage_ids:
          passage_result = await db.execute(
              select(Passage).where(Passage.id.in_(failed_passage_ids))
          )
          failed_passages = passage_result.scalars().all()
          failed_concepts = [p.concept_title for p in failed_passages]

      return {
          "score": correct_count,
          "total": total,
          "passed": passed,
          "failed_concepts": failed_concepts,
      }
  ```

**Outcome:** The quiz scoring logic is fully written and testable in isolation.

---

### Chunk 7 — Write `learning_service.py` (full orchestration)

**What you learn:** What an orchestration service is — one service that coordinates multiple other services and database operations to complete a complex multi-step flow.

- [ ] Create `backend/app/services/learning_service.py`:
  ```python
  from sqlalchemy.ext.asyncio import AsyncSession
  from sqlalchemy import select
  from app.models.learning import Module, Passage, Quiz, Question, Remediation
  from app.models.user import User
  from app.services import ai_service
  from app.schemas.learning import StartModuleResponse, PassageResponse, GenerateQuizResponse, QuestionResponse, RemediateResponse, RemediationResponse
  import uuid


  async def start_module(
      topic: str,
      level: str,
      user: User,
      db: AsyncSession
  ) -> StartModuleResponse:
      """
      Starts a new learning module:
      1. Generates ELI5 using the user's stored interests
      2. Generates 2-3 passages at the chosen level
      3. Saves everything to the database
      4. Returns the module ID, ELI5, and passages
      """
      interests = user.interest_topics or ["general knowledge", "science", "history"]

      eli5_text = await ai_service.generate_eli5(topic, level, interests)
      raw_passages = await ai_service.generate_passages(topic, level, eli5_text)

      module = Module(
          user_id=user.id,
          topic=topic,
          level=level,
          eli5_text=eli5_text,
      )
      db.add(module)
      await db.flush()

      passages = []
      for i, p in enumerate(raw_passages):
          passage = Passage(
              module_id=module.id,
              concept_title=p["concept_title"],
              content=p["content"],
              order_index=i + 1,
          )
          db.add(passage)
          passages.append(passage)

      await db.commit()
      for p in passages:
          await db.refresh(p)
      await db.refresh(module)

      return StartModuleResponse(
          module_id=module.id,
          eli5_text=eli5_text,
          passages=[PassageResponse.model_validate(p) for p in passages],
      )


  async def generate_quiz_for_module(
      module_id: uuid.UUID,
      db: AsyncSession
  ) -> GenerateQuizResponse:
      """
      Generates a quiz for an existing module:
      1. Fetches the module's passages from the database
      2. Calls Claude to generate questions based on those passages
      3. Saves all questions to the database
      4. Returns the quiz ID and questions (without correct answers)
      """
      passage_result = await db.execute(
          select(Passage).where(Passage.module_id == module_id).order_by(Passage.order_index)
      )
      passages = passage_result.scalars().all()

      module_result = await db.execute(select(Module).where(Module.id == module_id))
      module = module_result.scalar_one()

      passages_content = [{"concept_title": p.concept_title, "content": p.content} for p in passages]
      raw_questions = await ai_service.generate_quiz(module.topic, passages_content, module.level)

      # Find the attempt number
      existing_quizzes_result = await db.execute(
          select(Quiz).where(Quiz.module_id == module_id)
      )
      attempt_number = len(existing_quizzes_result.scalars().all()) + 1

      quiz = Quiz(module_id=module_id, attempt_number=attempt_number)
      db.add(quiz)
      await db.flush()

      passage_map = {p.concept_title: p.id for p in passages}
      questions = []
      for i, q in enumerate(raw_questions):
          passage_id = passage_map.get(q["concept_title"], passages[0].id)
          question = Question(
              quiz_id=quiz.id,
              passage_id=passage_id,
              question_text=q["question_text"],
              question_type=q["question_type"],
              options=q["options"],
              correct_answer=q["correct_answer"],
              order_index=i + 1,
          )
          db.add(question)
          questions.append(question)

      await db.commit()
      for q in questions:
          await db.refresh(q)

      return GenerateQuizResponse(
          quiz_id=quiz.id,
          questions=[
              QuestionResponse(
                  id=q.id,
                  concept_title=q.passage.concept_title if q.passage else "",
                  question_text=q.question_text,
                  question_type=q.question_type,
                  options=q.options,
                  order_index=q.order_index,
              )
              for q in questions
          ],
      )


  async def remediate(
      module_id: uuid.UUID,
      quiz_id: uuid.UUID,
      failed_concepts: list[str],
      db: AsyncSession
  ) -> RemediateResponse:
      """
      Generates fresh remediation explanations for failed concepts:
      1. Fetches the original passages for context
      2. Calls Claude to generate new explanations using different analogies
      3. Saves remediations to the database
      4. Returns the new explanations
      """
      module_result = await db.execute(select(Module).where(Module.id == module_id))
      module = module_result.scalar_one()

      passage_result = await db.execute(
          select(Passage).where(Passage.module_id == module_id)
      )
      passages = passage_result.scalars().all()
      original_passages = [{"concept_title": p.concept_title, "content": p.content} for p in passages]

      raw_remediations = await ai_service.generate_remediation(
          module.topic, failed_concepts, original_passages
      )

      passage_map = {p.concept_title: p.id for p in passages}
      for r in raw_remediations:
          passage_id = passage_map.get(r["concept_title"], passages[0].id)
          remediation = Remediation(
              module_id=module_id,
              passage_id=passage_id,
              quiz_id=quiz_id,
              content=r["content"],
          )
          db.add(remediation)

      await db.commit()

      return RemediateResponse(
          remediations=[RemediationResponse(**r) for r in raw_remediations]
      )
  ```

**Outcome:** The full learning loop (start → quiz → score → remediate) is implemented as service functions.

---

### Chunk 8 — Write the learning router

**What you learn:** How to expose multi-step service logic as clean API endpoints, and how to pass the current user into service calls.

- [ ] Create `backend/app/routers/learning.py`:
  ```python
  from fastapi import APIRouter, Depends, HTTPException, status
  from sqlalchemy.ext.asyncio import AsyncSession
  from app.core.database import get_db
  from app.dependencies import get_current_user
  from app.models.user import User
  from app.schemas.learning import (
      StartModuleRequest, StartModuleResponse,
      GenerateQuizRequest, GenerateQuizResponse,
      SubmitQuizRequest, SubmitQuizResponse,
      RemediateRequest, RemediateResponse,
  )
  from app.services import learning_service, quiz_service

  router = APIRouter(prefix="/learn", tags=["learning"])


  @router.post("/start", response_model=StartModuleResponse)
  async def start_module(
      data: StartModuleRequest,
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ):
      if data.level not in ("kid", "intermediate", "expert"):
          raise HTTPException(status_code=400, detail="Level must be kid, intermediate, or expert")
      return await learning_service.start_module(data.topic, data.level, current_user, db)


  @router.post("/quiz/generate", response_model=GenerateQuizResponse)
  async def generate_quiz(
      data: GenerateQuizRequest,
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ):
      return await learning_service.generate_quiz_for_module(data.module_id, db)


  @router.post("/quiz/submit", response_model=SubmitQuizResponse)
  async def submit_quiz(
      data: SubmitQuizRequest,
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ):
      result = await quiz_service.score_quiz(data.quiz_id, data.answers, db)
      return SubmitQuizResponse(**result)


  @router.post("/remediate", response_model=RemediateResponse)
  async def remediate(
      data: RemediateRequest,
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ):
      if not data.failed_concepts:
          raise HTTPException(status_code=400, detail="No failed concepts provided")
      return await learning_service.remediate(data.module_id, data.quiz_id, data.failed_concepts, db)
  ```

**Outcome:** Four learning endpoints exist as Python code.

---

### Chunk 9 — Register the learning router in `main.py`

**What you learn:** How FastAPI's router registration works and why each feature area gets its own router.

- [ ] Open `backend/main.py` and add the learning router:
  ```python
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  from app.core.config import settings
  from app.routers import auth, learning

  app = FastAPI(title="MasterMind API", version="0.1.0")

  app.add_middleware(
      CORSMiddleware,
      allow_origins=[settings.FRONTEND_URL],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )

  app.include_router(auth.router)
  app.include_router(learning.router)

  @app.get("/health")
  async def health():
      return {"status": "ok"}
  ```
- [ ] Restart the server and visit http://localhost:8000/docs
- [ ] Confirm you see the `/learn/*` endpoints listed alongside the `/auth/*` endpoints

**Outcome:** The server is running with both auth and learning routes active.

---

### Chunk 10 — Test the full learning flow end to end

**What you learn:** How the 4 API calls chain together to form a complete learning session.

- [ ] In Swagger UI, click **Authorize** and add your JWT token from `/auth/login`
- [ ] **Step 1 — Start a module:**
  - `POST /learn/start` with body: `{"topic": "Black holes", "level": "intermediate"}`
  - Confirm you receive `module_id`, `eli5_text`, and a `passages` array
  - Copy the `module_id`
- [ ] **Step 2 — Generate a quiz:**
  - `POST /learn/quiz/generate` with body: `{"module_id": "your-module-id"}`
  - Confirm you receive a `quiz_id` and a `questions` array with 5-10 questions
  - Copy the `quiz_id` and one `question id`
- [ ] **Step 3 — Submit answers:**
  - `POST /learn/quiz/submit` with body:
    ```json
    {
      "quiz_id": "your-quiz-id",
      "answers": [
        {"question_id": "question-id-1", "user_answer": "wrong answer on purpose"},
        ...
      ]
    }
    ```
  - Submit a wrong answer for at least one question intentionally
  - Confirm you receive `score`, `total`, `passed: false`, and `failed_concepts`
  - Copy a concept from `failed_concepts`
- [ ] **Step 4 — Get remediation:**
  - `POST /learn/remediate` with body:
    ```json
    {
      "module_id": "your-module-id",
      "quiz_id": "your-quiz-id",
      "failed_concepts": ["concept title that failed"]
    }
    ```
  - Confirm you receive a `remediations` array with a new explanation
- [ ] Open Supabase → verify rows exist in all 6 tables: `modules`, `passages`, `quizzes`, `questions`, `answers`, `remediations`

**Outcome:** The complete learn → quiz → submit → remediate loop works end to end with real data in Supabase.

---

### Chunk 11 — Write tests for quiz scoring logic

**What you learn:** How to test pure logic functions in isolation without needing a real database.

- [ ] Create `backend/tests/test_quiz.py`:
  ```python
  from app.core.security import create_access_token, decode_access_token


  def test_correct_answer_is_detected():
      """Simulate that a matching answer string is treated as correct."""
      user_answer = "Gravity warps spacetime"
      correct_answer = "Gravity warps spacetime"
      assert user_answer.strip() == correct_answer.strip()


  def test_wrong_answer_is_detected():
      """Simulate that a non-matching answer string is treated as incorrect."""
      user_answer = "Light travels faster than sound"
      correct_answer = "Gravity warps spacetime"
      assert user_answer.strip() != correct_answer.strip()


  def test_answer_with_extra_whitespace_matches():
      """Whitespace around answers should not cause false failures."""
      user_answer = "  True  "
      correct_answer = "True"
      assert user_answer.strip() == correct_answer.strip()


  def test_case_sensitive_answers_differ():
      """Answers are case-sensitive — 'true' and 'True' are different."""
      user_answer = "true"
      correct_answer = "True"
      assert user_answer.strip() != correct_answer.strip()
  ```
- [ ] Run all tests:
  ```bash
  pytest tests/ -v
  ```
- [ ] Confirm all 9 tests pass (5 from Chunk 3 of Milestone 1 + 4 AI tests + 4 quiz tests)

**Outcome:** You have automated proof that both the security functions and quiz scoring logic work correctly.

---

## Milestone 2 complete checklist (summary)

- [ ] Chunk 1 — Anthropic API key added to `.env`
- [ ] Chunk 2 — `ai_service.py` written with all 4 Claude functions
- [ ] Chunk 3 — All 4 AI functions tested in isolation and passing
- [ ] Chunk 4 — Learning models created and migration run
- [ ] Chunk 5 — Learning and quiz Pydantic schemas written
- [ ] Chunk 6 — `quiz_service.py` scoring logic written
- [ ] Chunk 7 — `learning_service.py` orchestration written
- [ ] Chunk 8 — Learning router written
- [ ] Chunk 9 — Learning router registered in `main.py`
- [ ] Chunk 10 — Full flow tested end to end in Swagger UI
- [ ] Chunk 11 — Quiz scoring tests passing

---

## Before starting Milestone 3

Do not start Milestone 3 until every box above is checked AND:

- Supabase has real rows in all 6 learning tables after a test session
- `pytest tests/ -v` shows all tests passing
- `POST /learn/remediate` returns a noticeably different explanation from the original passage

Tell Claude: "Milestone 2 is complete. Starting Milestone 3."
