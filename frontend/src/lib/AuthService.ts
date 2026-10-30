export type User = { id: number; email: string; user_name?: string }

export class AuthService {
  private token = ''

  constructor(token = '') {
    this.token = token
  }

  setToken(token: string) {
    this.token = token
  }

  clearToken() {
    this.token = ''
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers = new Headers(options.headers)
    if (this.token) headers.set('Authorization', `Bearer ${this.token}`)
    if (options.body) headers.set('Content-Type', 'application/json')

    const response = await fetch(`/api${path}`, { ...options, headers })
    const result = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(result.error || `Request failed (${response.status})`)
    return result as T
  }

  async getMe(): Promise<{ user: User }> {
    return this.request<{ user: User }>('/auth/me')
  }

  async login(email: string, password: string): Promise<{ token: string; user: User }> {
    return this.request<{ token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  }

  async logout(): Promise<void> {
    await this.request('/auth/logout', { method: 'POST' })
  }
}
