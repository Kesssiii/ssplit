export type User = { id: number; email: string; user_name?: string }
export type Bill = { id: number; description: string; amount: string | number; paid_by: string | number; due_date?: string | null; split_between?: string }
export type ScheduledBill = { id: number; description: string; amount: string | number; due_date: string; frequency: string }

export type BalanceRow = { user: User; amount: number }

export function displayName(user: User) {
  return user.user_name || user.email.split('@')[0]
}

export function money(value: number | string) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(value) || 0)
}

export function initials(name: string) {
  return name.split(/[\s.@_-]+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join('').toUpperCase()
}

export function formatDate(value?: string | null) {
  if (!value) return 'No date'
  const date = new Date(`${value.slice(0, 10)}T00:00:00`)
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(date)
}

export function getBalanceRows(users: User[], bills: Bill[], activeUser: User | null): BalanceRow[] {
  if (!activeUser) return []

  const balances = new Map<number, number>()

  for (const bill of bills) {
    const payerId = Number(bill.paid_by)
    const participants = [...new Set(String(bill.split_between || '').split(',').map((id) => Number(id.trim())).filter(Number.isFinite))]
    if (!participants.length || !Number.isFinite(payerId)) continue

    const share = (Number(bill.amount) || 0) / participants.length
    for (const participantId of participants) {
      if (participantId === payerId) continue
      if (payerId === activeUser.id) balances.set(participantId, (balances.get(participantId) || 0) + share)
      else if (participantId === activeUser.id) balances.set(payerId, (balances.get(payerId) || 0) - share)
    }
  }

  return users
    .filter((user) => user.id !== activeUser.id && Math.abs(balances.get(user.id) || 0) > 0.004)
    .map((user) => ({ user, amount: balances.get(user.id) || 0 }))
    .sort((left, right) => Math.abs(right.amount) - Math.abs(left.amount))
}

export function getRecentBills(bills: Bill[]) {
  return [...bills].slice(-5).reverse()
}

export function resetPaymentForm(currentUser: User | null) {
  return {
    paymentType: 'once' as const,
    description: '',
    amount: '',
    dueDate: new Date().toISOString().slice(0, 10),
    frequency: 'monthly',
    paidBy: currentUser?.id ?? '',
    splitBetween: currentUser ? [currentUser.id] : [],
  }
}

export function validatePayment(args: {
  description: string
  amount: string
  dueDate: string
  paymentType: 'once' | 'recurring'
  paidBy: number | ''
  splitBetween: number[]
}) {
  const { description, amount, dueDate, paymentType, paidBy, splitBetween } = args

  if (!description.trim() || Number(amount) <= 0 || !dueDate) {
    return 'Add a description, a positive amount, and a date.'
  }

  if (paymentType === 'once' && (paidBy === '' || splitBetween.length === 0)) {
    return 'Choose who paid and at least one person to split the bill with.'
  }

  return ''
}

export function createPaymentPayload(args: {
  description: string
  amount: string
  dueDate: string
  paymentType: 'once' | 'recurring'
  paidBy: number | ''
  splitBetween: number[]
  frequency: string
}) {
  const { description, amount, dueDate, paymentType, paidBy, splitBetween, frequency } = args

  if (paymentType === 'once') {
    return {
      description: description.trim(),
      amount: Number(amount).toFixed(2),
      paid_by: paidBy,
      split_between: [...new Set(splitBetween)].join(','),
      due_date: dueDate,
    }
  }

  return {
    description: description.trim(),
    amount: Number(amount).toFixed(2),
    due_date: dueDate,
    frequency,
  }
}
