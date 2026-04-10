from datetime import date, datetime
import uuid

from pydantic import BaseModel


class StartModuleRequest(BaseModel):
    topic: str
    level: str
    prerequisite_concepts: list[str] = []


class PassageResponse(BaseModel):
    id: uuid.UUID
    concept_title: str
    summary: str | None = None
    content: str
    use_cases: str | None = None
    order_index: int
    status: str = "in_progress"

    model_config = {"from_attributes": True}


class QuestionResponse(BaseModel):
    id: uuid.UUID
    concept_title: str
    question_text: str
    question_type: str
    options: list[str]
    order_index: int

    model_config = {"from_attributes": True}


class StartModuleResponse(BaseModel):
    module_id: uuid.UUID
    eli5_text: str
    current_passage: PassageResponse
    quiz_id: uuid.UUID
    questions: list[QuestionResponse]
    concepts_learned: int = 0


class GenerateQuizRequest(BaseModel):
    passage_id: uuid.UUID


class GenerateQuizResponse(BaseModel):
    quiz_id: uuid.UUID
    questions: list[QuestionResponse]


class AnswerSubmission(BaseModel):
    question_id: uuid.UUID
    user_answer: str


class SubmitQuizRequest(BaseModel):
    quiz_id: uuid.UUID
    answers: list[AnswerSubmission]
    local_date: date | None = None


class SubmitQuizResponse(BaseModel):
    score: int
    total: int
    passed: bool
    failed_concepts: list[str]
    next_passage: PassageResponse | None = None
    next_quiz_id: uuid.UUID | None = None
    next_questions: list[QuestionResponse] = []
    needs_new_pair: bool = False
    concepts_learned: int = 0


class NextPairRequest(BaseModel):
    module_id: uuid.UUID
    covered_concepts: list[str] = []


class NextPairResponse(BaseModel):
    current_passage: PassageResponse
    quiz_id: uuid.UUID
    questions: list[QuestionResponse]
    concepts_learned: int


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
    concepts_learned: int = 0
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ModuleDetail(BaseModel):
    id: uuid.UUID
    topic: str
    level: str
    eli5_text: str
    status: str
    markdown_url: str | None
    notion_page_id: str | None
    concepts_learned: int = 0
    completed_at: datetime | None
    created_at: datetime
    passages: list[PassageResponse]

    model_config = {"from_attributes": True}


class ExportDownloadResponse(BaseModel):
    download_url: str


class ExportNotionResponse(BaseModel):
    notion_page_url: str


class ReviewQuestionResponse(BaseModel):
    question_text: str
    concept_title: str
    options: list[str]
    correct_answer: str
    user_answer: str | None
    is_correct: bool | None


class ModuleReviewResponse(BaseModel):
    id: uuid.UUID
    topic: str
    level: str
    eli5_text: str
    status: str
    completed_at: datetime | None
    passages: list[PassageResponse]
    quiz_score: int | None
    quiz_total: int | None
    quiz_attempts: int | None
    questions: list[ReviewQuestionResponse]


class GraphNode(BaseModel):
    id: uuid.UUID
    label: str
    pos_x: float | None = None
    pos_y: float | None = None
    pos_z: float | None = None
    hub_score: int = 1
    module_ids: list[uuid.UUID] = []

    model_config = {"from_attributes": True}


class GraphResponse(BaseModel):
    nodes: list[GraphNode] = []


class PopulateGraphResponse(BaseModel):
    populated: int
