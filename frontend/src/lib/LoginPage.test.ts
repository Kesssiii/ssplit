import { fireEvent, render, screen } from '@testing-library/svelte'
import { describe, expect, it, vi } from 'vitest'
import LoginPage from './LoginPage.svelte'

describe('LoginPage', () => {
  it('renders required email and password fields', () => {
    render(LoginPage, { props: { onSubmit: vi.fn(), busy: false, errorMessage: '' } })

    expect(screen.getByRole('heading', { name: /good company/i })).toBeTruthy()
    expect(screen.getByLabelText('Email address').getAttribute('type')).toBe('email')
    expect(screen.getByLabelText('Password').getAttribute('type')).toBe('password')
  })

  it('shows login errors and disables submission while busy', () => {
    render(LoginPage, {
      props: { onSubmit: vi.fn(), busy: true, errorMessage: 'Invalid credentials' },
    })

    expect(screen.getByRole('alert').textContent).toBe('Invalid credentials')
    expect(screen.getByRole('button', { name: /signing in/i }).hasAttribute('disabled')).toBe(true)
  })

  it('forwards form submission', async () => {
    const onSubmit = vi.fn()
    render(LoginPage, { props: { onSubmit, busy: false, errorMessage: '' } })

    await fireEvent.submit(screen.getByRole('button', { name: /sign in/i }).closest('form')!)

    expect(onSubmit).toHaveBeenCalledOnce()
  })
})
