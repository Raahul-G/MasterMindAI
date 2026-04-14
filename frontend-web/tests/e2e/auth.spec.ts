/**
 * E2E tests — Authentication flow
 * Covers: Login, Register, ProtectedRoute redirect
 */

import { test, expect, type Page, type Route } from '@playwright/test'

const BASE_URL = 'http://localhost:5173'

const ME_RESPONSE = {
  id: 'user-123',
  email: 'test@example.com',
  full_name: 'Test User',
  avatar_url: null,
  interest_topics: [],
  is_active: true,
  notion_connected: false,
  notion_workspace_name: null,
}

async function stubDashboard(page: Page) {
  await page.route('**/modules', (r: Route) =>
    r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
  )
  await page.route('**/gamification/streak', (r: Route) =>
    r.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ current_streak: 0, longest_streak: 0, last_activity_date: null, total_concepts: 0 }),
    })
  )
}

// ---------------------------------------------------------------------------
// Login
// ---------------------------------------------------------------------------

test.describe('Login', () => {
  test('renders email, password fields and Log In button', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`)
    await expect(page.getByLabel('Email')).toBeVisible()
    await expect(page.getByLabel('Password')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Log In' })).toBeVisible()
  })

  test('shows Register link', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`)
    await expect(page.getByRole('link', { name: 'Register' })).toBeVisible()
  })

  test('successful login redirects to dashboard', async ({ page }) => {
    await page.route('**/auth/login', (r: Route) =>
      r.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ access_token: 'tok.abc', refresh_token: 'ref.abc', token_type: 'bearer' }),
      })
    )
    await page.route('**/auth/me', (r: Route) =>
      r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(ME_RESPONSE) })
    )
    await stubDashboard(page)

    await page.goto(`${BASE_URL}/login`)
    await page.getByLabel('Email').fill('test@example.com')
    await page.getByLabel('Password').fill('password123')
    await page.getByRole('button', { name: 'Log In' }).click()

    await expect(page).toHaveURL(`${BASE_URL}/dashboard`)
  })

  test('shows error message on invalid credentials', async ({ page }) => {
    await page.route('**/auth/login', (r: Route) =>
      r.fulfill({
        status: 401, contentType: 'application/json',
        body: JSON.stringify({ detail: 'Invalid email or password.' }),
      })
    )

    await page.goto(`${BASE_URL}/login`)
    await page.getByLabel('Email').fill('wrong@example.com')
    await page.getByLabel('Password').fill('wrongpass')
    await page.getByRole('button', { name: 'Log In' }).click()

    await expect(page.getByText('Invalid email or password.')).toBeVisible()
  })

  test('submit button is disabled while loading', async ({ page }) => {
    await page.route('**/auth/login', async (r: Route) => {
      await new Promise((res) => setTimeout(res, 500))
      r.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ access_token: 'tok', refresh_token: 'ref', token_type: 'bearer' }),
      })
    })
    await page.route('**/auth/me', (r: Route) =>
      r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(ME_RESPONSE) })
    )

    await page.goto(`${BASE_URL}/login`)
    await page.getByLabel('Email').fill('test@example.com')
    await page.getByLabel('Password').fill('password123')
    await page.getByRole('button', { name: 'Log In' }).click()

    await expect(page.getByRole('button', { name: 'Logging in...' })).toBeDisabled()
  })
})

// ---------------------------------------------------------------------------
// Register
// ---------------------------------------------------------------------------

test.describe('Register', () => {
  test('renders full name, email, password fields and Create Account button', async ({ page }) => {
    await page.goto(`${BASE_URL}/register`)
    await expect(page.getByLabel('Full name')).toBeVisible()
    await expect(page.getByLabel('Email')).toBeVisible()
    await expect(page.getByLabel('Password')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Create Account' })).toBeVisible()
  })

  test('shows Log In link for existing accounts', async ({ page }) => {
    await page.goto(`${BASE_URL}/register`)
    await expect(page.getByRole('link', { name: 'Log In' })).toBeVisible()
  })

  test('successful registration redirects to dashboard', async ({ page }) => {
    await page.route('**/auth/register', (r: Route) =>
      r.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ access_token: 'tok.new', refresh_token: 'ref.new', token_type: 'bearer' }),
      })
    )
    await page.route('**/auth/me', (r: Route) =>
      r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(ME_RESPONSE) })
    )
    await stubDashboard(page)

    await page.goto(`${BASE_URL}/register`)
    await page.getByLabel('Full name').fill('Alice Johnson')
    await page.getByLabel('Email').fill('alice@example.com')
    await page.getByLabel('Password').fill('securepass123')
    await page.getByRole('button', { name: 'Create Account' }).click()

    await expect(page).toHaveURL(`${BASE_URL}/dashboard`)
  })

  test('shows error when email is already registered', async ({ page }) => {
    await page.route('**/auth/register', (r: Route) =>
      r.fulfill({
        status: 400, contentType: 'application/json',
        body: JSON.stringify({ detail: 'Email already registered.' }),
      })
    )

    await page.goto(`${BASE_URL}/register`)
    await page.getByLabel('Full name').fill('Alice Johnson')
    await page.getByLabel('Email').fill('existing@example.com')
    await page.getByLabel('Password').fill('securepass123')
    await page.getByRole('button', { name: 'Create Account' }).click()

    await expect(page.getByText('Email already registered.')).toBeVisible()
  })
})

// ---------------------------------------------------------------------------
// ProtectedRoute — unauthenticated redirect
// ---------------------------------------------------------------------------

test.describe('ProtectedRoute', () => {
  test('unauthenticated user is redirected from /dashboard to /login', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`)
    await expect(page).toHaveURL(`${BASE_URL}/login`)
  })

  test('unauthenticated user is redirected from /learn to /login', async ({ page }) => {
    await page.goto(`${BASE_URL}/learn`)
    await expect(page).toHaveURL(`${BASE_URL}/login`)
  })

  test('unauthenticated user is redirected from /profile to /login', async ({ page }) => {
    await page.goto(`${BASE_URL}/profile`)
    await expect(page).toHaveURL(`${BASE_URL}/login`)
  })
})
