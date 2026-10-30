import { fireEvent, render, screen } from '@testing-library/svelte'
import { describe, expect, it, vi } from 'vitest'
import Sidebar from './Sidebar.svelte'

const user = { id: 1, email: 'alice@example.com', user_name: 'Alice Example' }

describe('Sidebar', () => {
  it('shows the current user, scheduled count, and active view', () => {
    render(Sidebar, {
      props: {
        currentUser: user,
        currentView: 'overview',
        scheduledBillsCount: 3,
        displayName: (currentUser) => currentUser.user_name ?? currentUser.email,
        initials: (name) => name.slice(0, 2).toUpperCase(),
        onViewChange: vi.fn(),
        onSignOut: vi.fn(),
      },
    })

    expect(screen.getByText('Alice Example')).toBeTruthy()
    expect(screen.getByText('alice@example.com')).toBeTruthy()
    expect(screen.getByText('3')).toBeTruthy()
    expect(screen.getByRole('button', { name: /overview/i }).classList.contains('active')).toBe(true)
  })

  it('notifies when the user changes views or signs out', async () => {
    const onViewChange = vi.fn()
    const onSignOut = vi.fn()
    render(Sidebar, {
      props: {
        currentUser: user,
        currentView: 'overview',
        scheduledBillsCount: 0,
        displayName: (currentUser) => currentUser.user_name ?? currentUser.email,
        initials: (name) => name.slice(0, 2).toUpperCase(),
        onViewChange,
        onSignOut,
      },
    })

    await fireEvent.click(screen.getByRole('button', { name: /scheduled/i }))
    await fireEvent.click(screen.getByRole('button', { name: /sign out/i }))

    expect(onViewChange).toHaveBeenCalledWith('schedule')
    expect(onSignOut).toHaveBeenCalledOnce()
  })
})
