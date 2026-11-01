import { fireEvent, render, screen } from '@testing-library/svelte'
import { describe, expect, it } from 'vitest'
import BillsPanel from './BillsPanel.svelte'
import type { Bill, User } from './SplitService'

const currentUser: User = { id: 1, email: 'alice@example.com', user_name: 'Alice' }
const bob: User = { id: 2, email: 'bob@example.com', user_name: 'Bob' }
const users = [currentUser, bob]
const money = (value: number | string) => `$${Number(value).toFixed(2)}`
const displayName = (user: User) => user.user_name ?? user.email
const formatDate = (value?: string | null) => value ?? 'No date'

function makeBill(id: number, description: string, splitBetween = '1,2'): Bill {
  return { id, description, amount: id * 10, paid_by: 2, split_between: splitBetween, due_date: `2026-10-${String(id).padStart(2, '0')}` }
}

const bills = [
  ...Array.from({ length: 11 }, (_, index) => makeBill(index + 1, `Shared bill ${index + 1}`)),
  { id: 12, description: 'Paid by Alice', amount: 25, paid_by: 1, split_between: '1', due_date: '2026-10-12' },
  { id: 13, description: 'Not Alice’s bill', amount: 50, paid_by: 2, split_between: '2', due_date: '2026-10-13' },
]

describe('BillsPanel', () => {
  it('lists bills involving the signed-in user and navigates between pages', async () => {
    render(BillsPanel, { props: { bills, users, currentUser, displayName, formatDate, money } })

    expect(screen.getByText('12 BILLS')).toBeTruthy()
    expect(screen.getByText('Shared bill 11')).toBeTruthy()
    expect(screen.queryByText('Not Alice’s bill')).toBeNull()
    expect(screen.getByText('Showing 1–10 of 12 bills')).toBeTruthy()

    await fireEvent.click(screen.getByRole('button', { name: 'Next page' }))

    expect(screen.getByText('Shared bill 2')).toBeTruthy()
    expect(screen.getByText('Showing 11–12 of 12 bills')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Page 2' }).getAttribute('aria-current')).toBe('page')
  })

  it('searches matching bills and resets pagination', async () => {
    render(BillsPanel, { props: { bills, users, currentUser, displayName, formatDate, money } })
    await fireEvent.click(screen.getByRole('button', { name: 'Next page' }))
    await fireEvent.input(screen.getByRole('searchbox', { name: 'Search bills' }), { target: { value: 'Shared bill 3' } })

    expect(screen.getByText('Shared bill 3')).toBeTruthy()
    expect(screen.getByText('Showing 1–1 of 1 bill')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Previous page' }).hasAttribute('disabled')).toBe(true)
  })
})
