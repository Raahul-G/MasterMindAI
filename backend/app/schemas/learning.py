from datetime import date, datetime
import uuid

from pydantic import BaseModel


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
    local_date: date | None = None


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
