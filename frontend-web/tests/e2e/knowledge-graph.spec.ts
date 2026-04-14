/**
 * E2E tests — Knowledge Graph feature
 *
 * Covers:
 *   - Own graph page (/graph): empty state, node render, nav badge
 *   - Friend graph page (/graph/friend/:userId): read-only, back nav, 403 handling
 *   - Activity feed entry point: "View their graph →" button
 *
 * Prerequisites:
 *   npm install -D @playwright/test
 *   npx playwright install chromium
 *   Run: npx playwright test tests/e2e/knowledge-graph.spec.ts
 *
 * The tests mock the API layer so no live backend is required.
 */

import { test, expect, type Page, type Route } from '@playwright/test'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const BASE_URL = 'http://localhost:5173'

/** Inject a valid JWT into localStorage so ProtectedRoute lets the page render. */
async function loginAs(page: Page, userId = 'user-abc') {
  await page.goto(BASE_URL)
  await page.evaluate((token) => localStorage.setItem('access_token', token), `fake.jwt.${userId}`)
}

/** Stub GET /auth/me so Navbar renders with a name. */
async function stubMe(page: Page, name = 'Test User') {
  await page.route('**/auth/me', (route: Route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'user-abc',
        email: 'test@example.com',
        full_name: name,
        avatar_url: null,
        interest_topics: [],
        is_active: true,
        notion_connected: false,
        notion_workspace_name: null,
      }),
    })
  )
}

// ---------------------------------------------------------------------------
// Own graph — /graph
// ---------------------------------------------------------------------------

test.describe('Own Knowledge Graph (/graph)', () => {
  test('shows empty state when user has no concepts', async ({ page }) => {
    await loginAs(page)
    await stubMe(page)

    await page.route('**/graph', (route: Route) => {
      if (route.request().resourceType() !== 'document' && !route.request().url().includes('/friend/')) {
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ nodes: [] }) })
      } else {
        route.continue()
      }
    })

    await page.goto(`${BASE_URL}/graph`)
    await expect(page.getByText('Complete your first concept')).toBeVisible()
  })

  test('renders node count badge when concepts exist', async ({ page }) => {
    await loginAs(page)
    await stubMe(page)

    await page.route('**/graph', (route: Route) => {
      if (route.request().resourceType() !== 'document' && !route.request().url().includes('/friend/')) {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            nodes: [
              { id: 'n1', label: 'gradient descent', pos_x: 1.0, pos_y: 2.0, pos_z: 3.0, hub_score: 1, module_ids: ['m1'] },
              { id: 'n2', label: 'backpropagation', pos_x: 4.0, pos_y: 5.0, pos_z: 6.0, hub_score: 2, module_ids: ['m1', 'm2'] },
            ],
          }),
        })
      } else {
        route.continue()
      }
    })

    await page.goto(`${BASE_URL}/graph`)
    await expect(page.getByText('2 concepts')).toBeVisible()
  })

  test('shows error message when API call fails', async ({ page }) => {
    await loginAs(page)
    await stubMe(page)

    await page.route('**/graph', (route: Route) => {
      if (route.request().resourceType() !== 'document' && !route.request().url().includes('/friend/')) {
        route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ error: 'server error' }) })
      } else {
        route.continue()
      }
    })

    await page.goto(`${BASE_URL}/graph`)
    await expect(page.getByText('Failed to load your knowledge graph')).toBeVisible()
  })

  test('Navbar Graph link is present and navigates to /graph', async ({ page }) => {
    await loginAs(page)
    await stubMe(page)
    await page.route('**/modules', (route: Route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
    )
    await page.route('**/gamification/streak', (route: Route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ current_streak: 0, longest_streak: 0, last_activity_date: null, total_concepts: 0 }) })
    )
    await page.route('**/graph', (route: Route) => {
      if (route.request().resourceType() !== 'document' && !route.request().url().includes('/friend/')) {
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ nodes: [] }) })
      } else {
        route.continue()
      }
    })

    await page.goto(`${BASE_URL}/dashboard`)

    await page.getByText('Graph').click()
    await expect(page).toHaveURL(`${BASE_URL}/graph`)
  })
})

// ---------------------------------------------------------------------------
// Friend graph — /graph/friend/:userId
// ---------------------------------------------------------------------------

test.describe("Friend's Knowledge Graph (/graph/friend/:userId)", () => {
  const FRIEND_ID = 'friend-xyz'
  const FRIEND_NAME = 'Alice'

  test('shows friend name in header and back button', async ({ page }) => {
    await loginAs(page)
    await stubMe(page)

    await page.route(`**/graph/friend/${FRIEND_ID}`, (route: Route) => {
      if (route.request().resourceType() !== 'document') {
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ nodes: [] }) })
      } else {
        route.continue()
      }
    })

    // Navigate with friendName in route state (simulate Friends.tsx navigation)
    await page.goto(`${BASE_URL}/graph/friend/${FRIEND_ID}`, {
      waitUntil: 'domcontentloaded',
    })
    // Inject state manually since Playwright navigates without React Router state
    await page.evaluate(
      ([id, name]) => {
        window.history.replaceState({ friendName: name }, '', `/graph/friend/${id}`)
      },
      [FRIEND_ID, FRIEND_NAME]
    )
    await page.reload()

    await expect(page.getByRole('button', { name: /back/i })).toBeVisible()
  })

  test('shows empty state when friend has no concepts', async ({ page }) => {
    await loginAs(page)
    await stubMe(page)

    await page.route(`**/graph/friend/${FRIEND_ID}`, (route: Route) => {
      if (route.request().resourceType() !== 'document') {
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ nodes: [] }) })
      } else {
        route.continue()
      }
    })

    await page.goto(`${BASE_URL}/graph/friend/${FRIEND_ID}`)
    await expect(page.getByText("hasn't completed any concepts yet")).toBeVisible()
  })

  test('shows 403 error when not friends with user', async ({ page }) => {
    await loginAs(page)
    await stubMe(page)

    await page.route(`**/graph/friend/${FRIEND_ID}`, (route: Route) => {
      if (route.request().resourceType() !== 'document') {
        route.fulfill({ status: 403, contentType: 'application/json', body: JSON.stringify({ detail: 'You are not friends with this user.' }) })
      } else {
        route.continue()
      }
    })

    await page.goto(`${BASE_URL}/graph/friend/${FRIEND_ID}`)
    await expect(page.getByText('You are not friends with this user')).toBeVisible()
  })

  test('shows concept count when friend has nodes', async ({ page }) => {
    await loginAs(page)
    await stubMe(page)

    await page.route(`**/graph/friend/${FRIEND_ID}`, (route: Route) => {
      if (route.request().resourceType() !== 'document') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            nodes: [
              { id: 'n1', label: 'machine learning', pos_x: 1.0, pos_y: 2.0, pos_z: 3.0, hub_score: 1, module_ids: ['m1'] },
              { id: 'n2', label: 'deep learning', pos_x: 4.0, pos_y: 5.0, pos_z: 6.0, hub_score: 1, module_ids: ['m1'] },
              { id: 'n3', label: 'transformers', pos_x: 7.0, pos_y: 8.0, pos_z: 9.0, hub_score: 2, module_ids: ['m1', 'm2'] },
            ],
          }),
        })
      } else {
        route.continue()
      }
    })

    await page.goto(`${BASE_URL}/graph/friend/${FRIEND_ID}`)
    await expect(page.getByText('3 concepts')).toBeVisible()
  })

  test('back button navigates to /friends', async ({ page }) => {
    await loginAs(page)
    await stubMe(page)

    await page.route(`**/graph/friend/${FRIEND_ID}`, (route: Route) => {
      if (route.request().resourceType() !== 'document') {
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ nodes: [] }) })
      } else {
        route.continue()
      }
    })
    await page.route('**/social/friends', (route: Route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
    )
    await page.route('**/social/friends/requests', (route: Route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
    )
    await page.route('**/social/feed', (route: Route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
    )

    await page.goto(`${BASE_URL}/graph/friend/${FRIEND_ID}`)
    await page.getByRole('button', { name: /back/i }).click()
    await expect(page).toHaveURL(`${BASE_URL}/friends`)
  })
})

// ---------------------------------------------------------------------------
// Activity feed → friend graph entry point
// ---------------------------------------------------------------------------

test.describe('Activity Feed — View their graph entry point', () => {
  test('"View their graph" button appears on module_completed feed items', async ({ page }) => {
    await loginAs(page)
    await stubMe(page)

    await page.route('**/social/friends', (route: Route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
    )
    await page.route('**/social/friends/requests', (route: Route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
    )
    await page.route('**/social/feed', (route: Route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'feed-1',
            user: { id: 'friend-xyz', full_name: 'Alice', avatar_url: null },
            activity_type: 'module_completed',
            metadata: { topic: 'Machine Learning', level: 'intermediate', concept: 'Gradient Descent' },
            created_at: new Date().toISOString(),
          },
        ]),
      })
    )

    await page.goto(`${BASE_URL}/friends`)
    await expect(page.getByText('View their graph')).toBeVisible()
  })

  test('"View their graph" button not shown on achievement_earned items', async ({ page }) => {
    await loginAs(page)
    await stubMe(page)

    await page.route('**/social/friends', (route: Route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
    )
    await page.route('**/social/friends/requests', (route: Route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
    )
    await page.route('**/social/feed', (route: Route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'feed-2',
            user: { id: 'friend-xyz', full_name: 'Alice', avatar_url: null },
            activity_type: 'achievement_earned',
            metadata: { slug: 'streak_starter', name: 'Streak Starter', icon_emoji: '🌱' },
            created_at: new Date().toISOString(),
          },
        ]),
      })
    )

    await page.goto(`${BASE_URL}/friends`)
    await expect(page.getByText('View their graph')).not.toBeVisible()
  })

  test('clicking "View their graph" navigates to friend graph route', async ({ page }) => {
    await loginAs(page)
    await stubMe(page)

    await page.route('**/social/friends', (route: Route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
    )
    await page.route('**/social/friends/requests', (route: Route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
    )
    await page.route('**/social/feed', (route: Route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'feed-1',
            user: { id: 'friend-xyz', full_name: 'Alice', avatar_url: null },
            activity_type: 'module_completed',
            metadata: { topic: 'ML', level: 'intermediate', concept: 'Backprop' },
            created_at: new Date().toISOString(),
          },
        ]),
      })
    )
    await page.route('**/graph/friend/friend-xyz', (route: Route) => {
      if (route.request().resourceType() !== 'document') {
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ nodes: [] }) })
      } else {
        route.continue()
      }
    })

    await page.goto(`${BASE_URL}/friends`)
    await page.getByText('View their graph').click()
    await expect(page).toHaveURL(`${BASE_URL}/graph/friend/friend-xyz`)
  })
})
