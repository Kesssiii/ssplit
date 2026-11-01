import { render, screen } from '@testing-library/svelte'
import { describe, expect, it } from 'vitest'
import DebtPanel from './DebtPanel.svelte'
import type { ExpenseOverview } from './SplitService'

const money = (value: number | string) => `$${Number(value).toFixed(2)}`
const initials = (name: string) => name.slice(0, 1).toUpperCase()

const expenseOverview: ExpenseOverview = {
  summary: {
    total_paid_by_me: 120,
    total_i_owe: 30,
    total_owed_to_me: 45,
    net_balance: 15,
  },
  my_debts: {
    total: 30,
    by_person: { '2': 30 },
    chart: [{ user_id: 2, user_name: 'Bob', amount: 30 }],
  },
  debts_to_me: {
    total: 45,
    by_person: { '3': 45 },
    chart: [{ user_id: 3, user_name: 'Carol', amount: 45 }],
  },
}

describe('DebtPanel', () => {
  it('shows totals and debts grouped by person', () => {
    render(DebtPanel, { props: { expenseOverview, money, initials } })

    expect(screen.getByRole('region', { name: 'Debt summary' })).toBeTruthy()
    expect(screen.getByText('+$15.00')).toBeTruthy()
    expect(screen.getByText('Bob')).toBeTruthy()
    expect(screen.getAllByText('$30.00')).toHaveLength(2)
    expect(screen.getByText('Carol')).toBeTruthy()
    expect(screen.getAllByText('$45.00')).toHaveLength(2)
  })

  it('shows independent empty states when no debts are outstanding', () => {
    const noDebts: ExpenseOverview = {
      ...expenseOverview,
      summary: { ...expenseOverview.summary, total_i_owe: 0, total_owed_to_me: 0, net_balance: 0 },
      my_debts: { total: 0, by_person: {}, chart: [] },
      debts_to_me: { total: 0, by_person: {}, chart: [] },
    }

    render(DebtPanel, { props: { expenseOverview: noDebts, money, initials } })

    expect(screen.getByText('You’re all settled')).toBeTruthy()
    expect(screen.getByText('No debts owed to you')).toBeTruthy()
  })
})
