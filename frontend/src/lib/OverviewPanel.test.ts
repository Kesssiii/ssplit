import { fireEvent, render, screen } from '@testing-library/svelte'
import { describe, expect, it, vi } from 'vitest'
import OverviewPanel from './OverviewPanel.svelte'

type User = { id: number; email: string; user_name?: string }

const currentUser: User = { id: 1, email: 'alice@example.com', user_name: 'Alice' }
const bob: User = { id: 2, email: 'bob@example.com', user_name: 'Bob' }
const money = (value: number | string) => `$${Number(value).toFixed(2)}`

const commonProps = {
  balanceRows: [
    { user: bob, amount: 15 },
    { user: { id: 3, email: 'carol@example.com', user_name: 'Carol' }, amount: -5 },
  ],
  recentBills: [
    { id: 12, description: 'Groceries', amount: 40, paid_by: 2, due_date: '2026-10-24' },
  ],
  billCount: 4,
  users: [currentUser, bob],
  currentUser,
  netBalance: 10,
  owedToYou: 15,
  youOwe: 5,
  onAddPayment: vi.fn(),
  displayName: (user: User) => user.user_name ?? user.email,
  initials: (name: string) => name.slice(0, 1).toUpperCase(),
  formatDate: (value?: string | null) => value ?? '',
  money,
}

describe('OverviewPanel', () => {
  it('shows balance summaries, people, and recent activity', () => {
    render(OverviewPanel, { props: commonProps })

    expect(screen.getByRole('region', { name: 'Balance summary' })).toBeTruthy()
    expect(screen.getByText('+$10.00')).toBeTruthy()
    expect(screen.getAllByText('Across 1 person')).toHaveLength(2)
    expect(screen.getByText('Bob')).toBeTruthy()
    expect(screen.getByText('Paid by Bob · 2026-10-24')).toBeTruthy()
    expect(screen.getByText('4 TOTAL')).toBeTruthy()
  })

  it('offers an action to add a payment', async () => {
    const onAddPayment = vi.fn()
    render(OverviewPanel, { props: { ...commonProps, onAddPayment } })

    await fireEvent.click(screen.getByRole('button', { name: /add a payment/i }))

    expect(onAddPayment).toHaveBeenCalledOnce()
  })

  it('shows empty states when there are no balances or payments', () => {
    render(OverviewPanel, {
      props: {
        ...commonProps,
        balanceRows: [],
        recentBills: [],
        billCount: 0,
      },
    })

    expect(screen.getByText('All square for now')).toBeTruthy()
    expect(screen.getByText('No payments yet')).toBeTruthy()
  })
})
