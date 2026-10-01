export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export type Inventory = {
  sku: string
  total_stock: number
  available_stock: number
  sold_out: boolean
  waitlist_count: number
}

export type User = {
  id: number
  username: string
}

export type Hold = {
  hold_id: number
  status: 'active' | 'expired' | 'paid'
  expires_at: string
}

export type PaymentResult = {
  outcome: 'processed' | 'duplicate' | 'late'
  event_id: string
  payment_id: string
  hold_id: number
  order_id: number | null
}

type ErrorPayload = {
  detail?: string
  hold?: Hold
}

export class ApiError extends Error {
  status: number
  data: ErrorPayload

  constructor(status: number, data: ErrorPayload) {
    super(data.detail ?? 'Something went wrong. Please try again.')
    this.status = status
    this.data = data
  }
}

function csrfToken() {
  const cookie = document.cookie
    .split('; ')
    .find((value) => value.startsWith('csrftoken='))

  return cookie ? decodeURIComponent(cookie.split('=')[1]) : ''
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const method = options.method ?? 'GET'
  const headers = new Headers(options.headers)

  if (options.body) {
    headers.set('Content-Type', 'application/json')
  }

  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    headers.set('X-CSRFToken', csrfToken())
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    method,
    headers,
    credentials: 'include',
  })

  const isJson = response.headers
    .get('content-type')
    ?.includes('application/json')
  const data = isJson ? await response.json() : null

  if (!response.ok) {
    throw new ApiError(response.status, (data ?? {}) as ErrorPayload)
  }

  return data as T
}

export function getInventory() {
  return request<Inventory>('/api/inventory/')
}

export async function getCurrentUser() {
  try {
    const response = await request<{ user: User }>('/api/auth/me/')
    return response.user
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      return null
    }
    throw error
  }
}

export function login(username: string, password: string) {
  return request<{ detail: string }>('/api/auth/csrf/')
    .then(() =>
      request<{ user: User }>('/api/auth/login/', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      }),
    )
    .then((response) => response.user)
}

export async function logout() {
  await request<null>('/api/auth/logout/', { method: 'POST' })
}

export function reservePair() {
  return request<{ outcome: 'held'; hold: Hold }>('/api/reservations/buy/', {
    method: 'POST',
  })
}

export function joinWaitlist() {
  return request<{
    outcome: 'waiting' | 'already_waiting'
    waitlist_entry_id: number
    position: number
  }>('/api/waitlist/join/', {
    method: 'POST',
  })
}

export function completePayment(holdId: number) {
  const eventId = `evt-${crypto.randomUUID()}`
  const paymentId = `pay-${crypto.randomUUID()}`

  return request<PaymentResult>('/api/payments/complete/', {
    method: 'POST',
    body: JSON.stringify({
      hold_id: holdId,
      event_id: eventId,
      payment_id: paymentId,
    }),
  })
}
