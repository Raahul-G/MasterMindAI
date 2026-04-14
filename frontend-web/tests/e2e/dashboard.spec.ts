/**
 * E2E tests — Dashboard
 * Covers: empty state, module list, streak counter, Continue / Review / Start New Module
 */

import { test, expect, type Page, type Route } from '@playwright/test'

const BASE_URL = 'http://localhost:5173'

async function loginAs(page: Page) {
  await page.goto(BASE_URL)
  await page.evaluate(() => localStorage.setItem('access_token', 'fake.jwt.user'))
}

async function stubMe(page: Page, name = 'Test User') {
  await page.route('**/auth/me', (r: Route) =>
    r.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({
        id: 'user-abc', email: 'test@example.com', full_name: name,
        avatar_url: null, interest_topics: [], is_active: true,
        notion_connected: false, notion_workspace_name: null,
      }),
    })
  )
}

async function stubStreak(page: Page, current = 3) {
  await page.route('**/gamification/streak', (r: Route) =>
    r.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({
        current_streak: current, longest_streak: 7,
        last_activity_date: '2026-04-13', total_concepts: 12,
      }),
    })
  )
}

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------

test.describe('Dashboard — empty state', () => {
  test('shows "No modules yet" when user has no modules', async ({ page }) => {
    await loginAs(page)
    await stubMe(page)
    await stubStreak(page, 0)
    await page.route('**/modules', (r: Route) =>
      r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
    )

    await page.goto(`${BASE_URL}/dashboard`)
    await expect(page.getByText('No modules yet')).toBeVisible()
  })

  test('"Start New Module" button is visible in empty state', async ({ page }) => {
    await loginAs(page)
    await stubMe(page)
    await stubStreak(page, 0)
    await page.route('**/modules', (r: Route) =>
      r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
    )

    await page.goto(`${BASE_URL}/dashboard`)
    await expect(page.getByRole('button', { name: /Start New Module/i })).toBeVisible()
  })

  test('"Start New Module" navigates to /learn/start', async ({ page }) => {
    await loginAs(page)
    await stubMe(page)
    await stubStreak(page, 0)
    await page.route('**/modules', (r: Route) =>
      r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
    )

    await page.goto(`${BASE_URL}/dashboard`)
    await page.getByRole('button', { name: /Start New Module/i }).click()
    await expect(page).toHaveURL(`${BASE_URL}/learn/start`)
  })
})

// ---------------------------------------------------------------------------
// Module list
// ---------------------------------------------------------------------------

const MODULE = {
  id: 'mod-001',
  topic: 'Machine Learning',
  level: 'intermediate',
  status: 'in_progress',
  concepts_learned: 5,
  eli5_text: null,
  completed_at: null,
  created_at: '2026-04-10T10:00:00Z',
}

test.describe('Dashboard — module list', () => {
  async function goToDashboardWithModule(page: Page) {
    await loginAs(page)
    await stubMe(page)
    await stubStreak(page)
    await page.route('**/modules', (r: Route) =>
      r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([MODULE]) })
    )
    await page.goto(`${BASE_URL}/dashboard`)
  }

  test('shows module topic name', async ({ page }) => {
    await goToDashboardWithModule(page)
    await expect(page.getByText('Machine Learning')).toBeVisible()
  })

  test('shows concepts learned count', async ({ page }) => {
    await goToDashboardWithModule(page)
    await expect(page.getByText('5 concepts learned')).toBeVisible()
  })

  test('shows level badge', async ({ page }) => {
    await goToDashboardWithModule(page)
    await expect(page.getByText('Intermediate')).toBeVisible()
  })

  test('"Review" button navigates to module review page', async ({ page }) => {
    await goToDashboardWithModule(page)
    await page.route('**/modules/mod-001/review', (r: Route) =>
      r.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({
          id: 'mod-001', topic: 'Machine Learning', level: 'intermediate',
          eli5_text: 'ML is like teaching a dog tricks.', status: 'in_progress',
          completed_at: null, passages: [], quiz_score: null,
          quiz_total: null, quiz_attempts: null, questions: [],
        }),
      })
    )
    await page.getByRole('button', { name: 'Review' }).click()
    await expect(page).toHaveURL(`${BASE_URL}/modules/mod-001/review`)
  })

  test('"Continue" calls resume API and navigates to /learn', async ({ page }) => {
    await goToDashboardWithModule(page)
    await page.route('**/learn/resume/mod-001', (r: Route) =>
      r.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({
          module_id: 'mod-001',
          eli5_text: 'ML is cool.',
          current_passage: {
            id: 'p-001', concept_title: 'Gradient Descent',
            summary: null, content: 'Gradient descent minimises a loss function.',
            use_cases: null, order_index: 1, status: 'in_progress',
          },
          quiz_id: 'q-001',
          questions: [],
          concepts_learned: 5,
        }),
      })
    )
    await page.getByRole('button', { name: 'Continue' }).click()
    await expect(page).toHaveURL(`${BASE_URL}/learn`)
  })

  test('shows error message when Continue fails', async ({ page }) => {
    await goToDashboardWithModule(page)
    await page.route('**/learn/resume/mod-001', (r: Route) =>
      r.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ error: 'server error' }) })
    )
    await page.getByRole('button', { name: 'Continue' }).click()
    await expect(page.getByText("Couldn't resume")).toBeVisible()
  })
})

// ---------------------------------------------------------------------------
// Streak counter
// ---------------------------------------------------------------------------

test.describe('Dashboard — streak counter', () => {
  test('shows current streak when streak is active', async ({ page }) => {
    await loginAs(page)
    await stubMe(page)
    await stubStreak(page, 5)
    await page.route('**/modules', (r: Route) =>
      r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
    )

    await page.goto(`${BASE_URL}/dashboard`)
    // StreakCounter shows the day count somewhere in the widget
    await expect(page.getByText('5')).toBeVisible()
  })
})
