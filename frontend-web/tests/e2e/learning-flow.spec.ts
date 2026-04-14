/**
 * E2E tests — Core learning flow
 * Covers: TopicSelection → Learning reading phase → quiz → pass/fail → remediation
 */

import { test, expect, type Page, type Route } from '@playwright/test'

const BASE_URL = 'http://localhost:5173'

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

async function loginAs(page: Page) {
  await page.goto(BASE_URL)
  await page.evaluate(() => localStorage.setItem('access_token', 'fake.jwt.user'))
}

async function stubMe(page: Page) {
  await page.route('**/auth/me', (r: Route) =>
    r.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({
        id: 'user-abc', email: 'test@example.com', full_name: 'Test User',
        avatar_url: null, interest_topics: ['cooking'], is_active: true,
        notion_connected: false, notion_workspace_name: null,
      }),
    })
  )
}

const PASSAGE = {
  id: 'p-001',
  concept_title: 'Gradient Descent',
  summary: 'A method to minimise loss.',
  content: 'Gradient descent iteratively adjusts parameters to reduce the loss function.',
  use_cases: 'Used in training neural networks.',
  order_index: 1,
  status: 'in_progress',
}

const QUESTIONS = [
  {
    id: 'q-001', concept_title: 'Gradient Descent',
    question_text: 'What does gradient descent minimise?',
    question_type: 'multiple_choice' as const,
    options: ['Loss function', 'Activation function', 'Learning rate', 'Batch size'],
    order_index: 1,
  },
  {
    id: 'q-002', concept_title: 'Gradient Descent',
    question_text: 'Gradient descent moves in the direction of the gradient.',
    question_type: 'true_false' as const,
    options: ['True', 'False'],
    order_index: 2,
  },
]

const START_MODULE_RESPONSE = {
  module_id: 'mod-001',
  eli5_text: 'Imagine rolling a ball down a hill to find the lowest point.',
  current_passage: PASSAGE,
  quiz_id: 'quiz-001',
  questions: QUESTIONS,
  concepts_learned: 0,
}

// Seeds the learning store by posting to /learn/start
async function stubStartModule(page: Page) {
  await page.route('**/learn/start', (r: Route) => {
    if (r.request().method() === 'POST') {
      r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(START_MODULE_RESPONSE) })
    } else {
      r.continue()
    }
  })
}

// Navigate to topic selection and kick off a module
async function startLearning(page: Page) {
  await loginAs(page)
  await stubMe(page)
  await stubStartModule(page)

  await page.goto(`${BASE_URL}/learn/start`)
  await page.getByLabel('Topic').fill('Machine Learning')
  await page.getByRole('button', { name: 'Start Learning' }).click()

  // Wait for navigation to /learn
  await page.waitForURL(`${BASE_URL}/learn`)
}

// ---------------------------------------------------------------------------
// TopicSelection
// ---------------------------------------------------------------------------

test.describe('TopicSelection', () => {
  test('renders topic input and three level buttons', async ({ page }) => {
    await loginAs(page)
    await stubMe(page)

    await page.goto(`${BASE_URL}/learn/start`)
    await expect(page.getByLabel('Topic')).toBeVisible()
    await expect(page.getByRole('button', { name: /Kid/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /Intermediate/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /Expert/i })).toBeVisible()
  })

  test('clicking a level button changes active selection', async ({ page }) => {
    await loginAs(page)
    await stubMe(page)

    await page.goto(`${BASE_URL}/learn/start`)
    await page.getByRole('button', { name: /Kid/i }).click()
    // Kid button should have the active border
    await expect(page.getByRole('button', { name: /Kid/i })).toHaveClass(/border-green-500/)
  })

  test('submitting without topic does nothing (required field)', async ({ page }) => {
    await loginAs(page)
    await stubMe(page)

    await page.goto(`${BASE_URL}/learn/start`)
    // Do not fill the topic
    const submitBtn = page.getByRole('button', { name: 'Start Learning' })
    await submitBtn.click()
    // Should still be on topic selection (required HTML validation prevents submit)
    await expect(page).toHaveURL(`${BASE_URL}/learn/start`)
  })

  test('successful submit navigates to /learn', async ({ page }) => {
    await loginAs(page)
    await stubMe(page)
    await stubStartModule(page)

    await page.goto(`${BASE_URL}/learn/start`)
    await page.getByLabel('Topic').fill('Machine Learning')
    await page.getByRole('button', { name: 'Start Learning' }).click()

    await expect(page).toHaveURL(`${BASE_URL}/learn`)
  })

  test('shows error when startModule API fails', async ({ page }) => {
    await loginAs(page)
    await stubMe(page)
    await page.route('**/learn/start', (r: Route) => {
      if (r.request().method() === 'POST') {
        r.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ error: 'server error' }) })
      } else {
        r.continue()
      }
    })

    await page.goto(`${BASE_URL}/learn/start`)
    await page.getByLabel('Topic').fill('Quantum Physics')
    await page.getByRole('button', { name: 'Start Learning' }).click()

    await expect(page.getByText('Failed to start module')).toBeVisible()
  })
})

// ---------------------------------------------------------------------------
// Learning — reading phase
// ---------------------------------------------------------------------------

test.describe('Learning — reading phase', () => {
  test('shows concept title in header', async ({ page }) => {
    await startLearning(page)
    await expect(page.getByRole('heading', { name: 'Gradient Descent', level: 1 })).toBeVisible()
  })

  test('shows Big Idea (ELI5) on first concept', async ({ page }) => {
    await startLearning(page)
    await expect(page.getByText('Big Idea')).toBeVisible()
    await expect(page.getByText('Imagine rolling a ball')).toBeVisible()
  })

  test('shows passage content', async ({ page }) => {
    await startLearning(page)
    await expect(page.getByText('Gradient descent iteratively')).toBeVisible()
  })

  test('shows "Where it\'s used" section when use_cases exist', async ({ page }) => {
    await startLearning(page)
    await expect(page.getByText("Where it's used")).toBeVisible()
    await expect(page.getByText('Used in training neural networks.')).toBeVisible()
  })

  test('"Test my understanding" button is visible', async ({ page }) => {
    await startLearning(page)
    await expect(page.getByRole('button', { name: /Test my understanding/i })).toBeVisible()
  })

  test('clicking "Test my understanding" transitions to quiz phase', async ({ page }) => {
    await startLearning(page)
    await page.getByRole('button', { name: /Test my understanding/i }).click()
    await expect(page.getByText('Question 1 of 2')).toBeVisible()
  })
})

// ---------------------------------------------------------------------------
// Learning — quiz phase
// ---------------------------------------------------------------------------

test.describe('Learning — quiz phase', () => {
  async function goToQuizPhase(page: Page) {
    await startLearning(page)
    await page.getByRole('button', { name: /Test my understanding/i }).click()
  }

  test('renders all questions', async ({ page }) => {
    await goToQuizPhase(page)
    await expect(page.getByText('What does gradient descent minimise?')).toBeVisible()
    await expect(page.getByText('Gradient descent moves in the direction of the gradient.')).toBeVisible()
  })

  test('Submit button is disabled until all questions answered', async ({ page }) => {
    await goToQuizPhase(page)
    await expect(page.getByRole('button', { name: 'Submit' })).toBeDisabled()
  })

  test('Submit button enabled after all questions answered', async ({ page }) => {
    await goToQuizPhase(page)
    // Answer question 1
    await page.getByText('Loss function').click()
    // Answer question 2
    await page.getByText('False').click()
    await expect(page.getByRole('button', { name: 'Submit' })).toBeEnabled()
  })
})

// ---------------------------------------------------------------------------
// Learning — passing a concept
// ---------------------------------------------------------------------------

test.describe('Learning — passing a concept', () => {
  async function submitAndPass(page: Page, responseBody: object) {
    await startLearning(page)
    await page.getByRole('button', { name: /Test my understanding/i }).click()

    await page.route('**/learn/quiz/submit', (r: Route) =>
      r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(responseBody) })
    )
    // Answer both questions
    await page.getByText('Loss function').click()
    await page.getByText('False').click()
    await page.getByRole('button', { name: 'Submit' }).click()
  }

  test('concept_passed phase shows score and "Next concept" button', async ({ page }) => {
    await submitAndPass(page, {
      score: 2, total: 2, passed: true, failed_concepts: [],
      next_passage: {
        id: 'p-002', concept_title: 'Learning Rate',
        summary: null, content: 'Controls step size.', use_cases: null,
        order_index: 2, status: 'in_progress',
      },
      next_quiz_id: 'quiz-002',
      next_questions: [
        { id: 'q-003', concept_title: 'Learning Rate', question_text: 'What does the learning rate control?',
          question_type: 'multiple_choice', options: ['Step size', 'Batch size', 'Layer count', 'Epoch count'], order_index: 1 },
      ],
      needs_new_pair: false,
      concepts_learned: 1,
    })

    await expect(page.getByText('Concept mastered!')).toBeVisible()
    await expect(page.getByText('2/2')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Next concept' })).toBeVisible()
  })

  test('needs_pair phase shows "Continue learning" button', async ({ page }) => {
    await submitAndPass(page, {
      score: 2, total: 2, passed: true, failed_concepts: [],
      next_passage: null, next_quiz_id: null, next_questions: [],
      needs_new_pair: true, concepts_learned: 2,
    })

    await expect(page.getByRole('button', { name: 'Continue learning' })).toBeVisible()
  })

  test('passed phase shows "Back to Dashboard" when no next pair', async ({ page }) => {
    await submitAndPass(page, {
      score: 2, total: 2, passed: true, failed_concepts: [],
      next_passage: null, next_quiz_id: null, next_questions: [],
      needs_new_pair: false, concepts_learned: 2,
    })

    await expect(page.getByRole('button', { name: 'Back to Dashboard' })).toBeVisible()
  })
})

// ---------------------------------------------------------------------------
// Learning — failing a concept and remediating
// ---------------------------------------------------------------------------

test.describe('Learning — failed concept and remediation', () => {
  async function submitAndFail(page: Page) {
    await startLearning(page)
    await page.getByRole('button', { name: /Test my understanding/i }).click()

    await page.route('**/learn/quiz/submit', (r: Route) =>
      r.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({
          score: 0, total: 2, passed: false,
          failed_concepts: ['Gradient Descent'],
          next_passage: null, next_quiz_id: null, next_questions: [],
          needs_new_pair: false, concepts_learned: 0,
        }),
      })
    )
    await page.getByText('Loss function').click()
    await page.getByText('True').click()
    await page.getByRole('button', { name: 'Submit' }).click()
  }

  test('failed phase shows score and failed concept name', async ({ page }) => {
    await submitAndFail(page)
    await expect(page.getByText('0/2')).toBeVisible()
    await expect(page.getByText('Gradient Descent').first()).toBeVisible()
  })

  test('"See new explanation" button is visible on failure', async ({ page }) => {
    await submitAndFail(page)
    await expect(page.getByRole('button', { name: /See new explanation/i })).toBeVisible()
  })

  test('clicking "See new explanation" loads remediation', async ({ page }) => {
    await submitAndFail(page)

    await page.route('**/learn/remediate', (r: Route) =>
      r.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({
          remediations: [{
            concept_title: 'Gradient Descent',
            content: 'Think of it like water flowing downhill to the lowest point.',
          }],
        }),
      })
    )
    await page.getByRole('button', { name: /See new explanation/i }).click()

    await expect(page.getByText("Let's try again")).toBeVisible()
    await expect(page.getByText('Think of it like water flowing downhill')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Try again' })).toBeVisible()
  })
})
