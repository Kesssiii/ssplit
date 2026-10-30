import { fireEvent, render, screen } from '@testing-library/svelte'
import { describe, expect, it, vi } from 'vitest'
import PaymentDialog from './PaymentDialog.svelte'

const users = [
  { id: 1, email: 'alice@example.com', user_name: 'Alice' },
  { id: 2, email: 'bob@example.com', user_name: 'Bob' },
]

describe('PaymentDialog', () => {
  it('does not render when closed', () => {
    render(PaymentDialog, { props: { open: false } })

    expect(screen.queryByRole('dialog')).toBeNull()
  })

  it('renders a one-time payment form and reports its actions', async () => {
    const onSubmit = vi.fn((event: SubmitEvent) => event.preventDefault())
    const onClose = vi.fn()
    const onTypeChange = vi.fn()
    const onPayerChange = vi.fn()
    render(PaymentDialog, {
      props: {
        open: true,
        users,
        currentUser: users[0],
        onSubmit,
        onClose,
        onTypeChange,
        onPayerChange,
      },
    })

    expect(screen.getByRole('dialog', { name: 'New payment' })).toBeTruthy()
    expect(screen.getByLabelText('Payment date')).toBeTruthy()
    expect(screen.getByLabelText('Who paid?')).toBeTruthy()
    expect(screen.getByRole('option', { name: 'Alice (you)' })).toBeTruthy()
    await fireEvent.click(screen.getByRole('tab', { name: 'Recurring' }))
    await fireEvent.change(screen.getByLabelText('Who paid?'), { target: { value: '2' } })
    await fireEvent.submit(screen.getByRole('dialog').querySelector('form')!)
    await fireEvent.click(screen.getByRole('button', { name: 'Close dialog' }))

    expect(onTypeChange).toHaveBeenCalledWith('recurring')
    expect(onPayerChange).toHaveBeenCalledWith('2')
    expect(onSubmit).toHaveBeenCalledOnce()
    expect(onClose).toHaveBeenCalledOnce()
  })

  it('shows recurring payment fields and validation errors', () => {
    render(PaymentDialog, {
      props: {
        open: true,
        paymentType: 'recurring',
        errorMessage: 'Enter a valid amount',
      },
    })

    expect(screen.getByLabelText('Next due date')).toBeTruthy()
    expect(screen.getByLabelText('Repeat')).toBeTruthy()
    expect(screen.getByRole('alert').textContent).toBe('Enter a valid amount')
    expect(screen.queryByLabelText('Who paid?')).toBeNull()
  })
})
