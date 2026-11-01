export type User = { id: number; email: string; user_name?: string }
export type Bill = { id: number; description: string; amount: string | number; paid_by: string | number; due_date?: string | null; split_between?: string }
export type ScheduledBill = { id: number; description: string; amount: string | number; due_date: string; frequency: string }
export type DebtPerson = { user_id: number; user_name: string; amount: number }
export type DebtBreakdown = { total: number; by_person: Record<string, number>; chart: DebtPerson[] }
export type ExpenseOverview = {
  summary: {
    total_paid_by_me: number
    total_i_owe: number
    total_owed_to_me: number
    net_balance: number
  }
  my_debts: DebtBreakdown
  debts_to_me: DebtBreakdown
}

export type DashboardData = {
  users: User[]
  bills: Bill[]
  scheduledBills: ScheduledBill[]
  expenseOverview: ExpenseOverview
}

export class SplitService {
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

  async getDashboard(): Promise<DashboardData> {
    const [users, bills, scheduledBills, expenseOverview] = await Promise.all([
      this.request<User[]>('/users'),
      this.request<Bill[]>('/bills'),
      this.request<ScheduledBill[]>('/scheduled-bills'),
      this.request<ExpenseOverview>('/expenses/overview'),
    ])

    return { users, bills, scheduledBills, expenseOverview }
  }

  async createBill(payload: {
    description: string
    amount: string
    paid_by: number | ''
    split_between: string
    due_date: string
  }): Promise<void> {
    await this.request('/bills', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  }

  async createScheduledBill(payload: {
    description: string
    amount: string
    due_date: string
    frequency: string
  }): Promise<void> {
    await this.request('/scheduled-bills', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  }

  async deleteScheduledBill(billId: number): Promise<void> {
    await this.request(`/scheduled-bills/${billId}`, { method: 'DELETE' })
  }
}
