import { fireEvent, render, screen } from '@testing-library/svelte'
import { describe, expect, it, vi } from 'vitest'
import SchedulePanel from './SchedulePanel.svelte'

const formatDate = (value?: string | null) => value ?? ''
const money = (value: number | string) => `$${Number(value).toFixed(2)}`

describe('SchedulePanel', () => {
  it('shows an empty state and offers to create a scheduled payment', async () => {
    const onOpenPaymentDialog = vi.fn()
    render(SchedulePanel, {
      props: {
        scheduledBills: [],
        onOpenPaymentDialog,
        onDeleteScheduledBill: vi.fn(),
        formatDate,
        money,
      },
    })

    expect(screen.getByText('No scheduled payments')).toBeTruthy()
    await fireEvent.click(screen.getByRole('button', { name: 'Create scheduled payment' }))
    expect(onOpenPaymentDialog).toHaveBeenCalledOnce()
  })

  it('renders scheduled payments and reports the selected payment for deletion', async () => {
    const onDeleteScheduledBill = vi.fn()
    render(SchedulePanel, {
      props: {
        scheduledBills: [
          { id: 7, description: 'Internet', amount: 65, due_date: '2026-11-05', frequency: 'monthly' },
        ],
        onOpenPaymentDialog: vi.fn(),
        onDeleteScheduledBill,
        formatDate,
        money,
      },
    })

    expect(screen.getByText('Internet')).toBeTruthy()
    expect(screen.getByText('$65.00')).toBeTruthy()
    expect(screen.getByText('1 SCHEDULED')).toBeTruthy()
    await fireEvent.click(screen.getByRole('button', { name: 'Delete Internet' }))

    expect(onDeleteScheduledBill).toHaveBeenCalledWith(7)
  })
})
