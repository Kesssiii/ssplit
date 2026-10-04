<script lang="ts">
  import { onMount } from 'svelte'

  type User = { id: number; email: string; user_name?: string }
  type Bill = { id: number; description: string; amount: string | number; paid_by: string | number; due_date?: string | null; split_between?: string }
  type ScheduledBill = { id: number; description: string; amount: string | number; due_date: string; frequency: string }

  let token = $state('')
  let currentUser = $state<User | null>(null)
  let users = $state<User[]>([])
  let bills = $state<Bill[]>([])
  let scheduledBills = $state<ScheduledBill[]>([])
  let checkingSession = $state(true)
  let busy = $state(false)
  let errorMessage = $state('')
  let currentView = $state<'overview' | 'schedule'>('overview')
  let paymentDialogOpen = $state(false)
  let paymentType = $state<'once' | 'recurring'>('once')
  let description = $state('')
  let amount = $state('')
  let paidBy = $state<number | ''>('')
  let splitBetween = $state<number[]>([])
  let dueDate = $state(new Date().toISOString().slice(0, 10))
  let frequency = $state('monthly')

  const displayName = (user: User) => user.user_name || user.email.split('@')[0]
  const money = (value: number | string) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(value) || 0)
  const initials = (name: string) => name.split(/[\s.@_-]+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join('').toUpperCase()
  const formatDate = (value?: string | null) => {
    if (!value) return 'No date'
    const date = new Date(`${value.slice(0, 10)}T00:00:00`)
    return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(date)
  }

  async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers = new Headers(options.headers)
    if (token) headers.set('Authorization', `Bearer ${token}`)
    if (options.body) headers.set('Content-Type', 'application/json')
    const response = await fetch(`/api${path}`, { ...options, headers })
    const result = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(result.error || `Request failed (${response.status})`)
    return result as T
  }

  async function loadDashboard() {
    const [userList, billList, scheduledList] = await Promise.all([
      apiRequest<User[]>('/users'), apiRequest<Bill[]>('/bills'), apiRequest<ScheduledBill[]>('/scheduled-bills'),
    ])
    users = userList
    bills = billList
    scheduledBills = scheduledList
    if (currentUser && paidBy === '') paidBy = currentUser.id
    if (currentUser && splitBetween.length === 0) splitBetween = [currentUser.id]
  }

  async function authenticate(event: SubmitEvent) {
    event.preventDefault()
    const formData = new FormData(event.currentTarget as HTMLFormElement)
    errorMessage = ''
    busy = true
    try {
      const session = await apiRequest<{ token: string; user: User }>('/auth/login', {
        method: 'POST', body: JSON.stringify({ email: String(formData.get('email') || ''), password: String(formData.get('password') || '') }),
      })
      token = session.token
      currentUser = session.user
      localStorage.setItem('ssplit-token', token)
      paidBy = currentUser.id
      splitBetween = [currentUser.id]
      await loadDashboard()
    } catch (error) {
      token = ''
      currentUser = null
      errorMessage = error instanceof Error ? error.message : 'Unable to sign in.'
    } finally {
      busy = false
    }
  }

  async function signOut() {
    try { await apiRequest('/auth/logout', { method: 'POST' }) } catch { /* The server session may already have expired. */ }
    token = ''
    currentUser = null
    localStorage.removeItem('ssplit-token')
    users = []
    bills = []
    scheduledBills = []
    currentView = 'overview'
  }

  function openPaymentDialog() {
    errorMessage = ''
    paymentType = 'once'
    description = ''
    amount = ''
    dueDate = new Date().toISOString().slice(0, 10)
    frequency = 'monthly'
    paidBy = currentUser?.id ?? ''
    splitBetween = currentUser ? [currentUser.id] : []
    paymentDialogOpen = true
  }

  function updatePayer(value: string) {
    paidBy = value ? Number(value) : ''
    if (paidBy !== '' && !splitBetween.includes(paidBy)) splitBetween = [...splitBetween, paidBy]
  }

  async function createPayment(event: SubmitEvent) {
    event.preventDefault()
    if (!description.trim() || Number(amount) <= 0 || !dueDate) {
      errorMessage = 'Add a description, a positive amount, and a date.'
      return
    }
    if (paymentType === 'once' && (paidBy === '' || splitBetween.length === 0)) {
      errorMessage = 'Choose who paid and at least one person to split the bill with.'
      return
    }
    errorMessage = ''
    busy = true
    try {
      if (paymentType === 'once') {
        await apiRequest('/bills', { method: 'POST', body: JSON.stringify({
          description: description.trim(), amount: Number(amount).toFixed(2), paid_by: paidBy,
          split_between: [...new Set(splitBetween)].join(','), due_date: dueDate,
        }) })
      } else {
        await apiRequest('/scheduled-bills', { method: 'POST', body: JSON.stringify({
          description: description.trim(), amount: Number(amount).toFixed(2), due_date: dueDate, frequency,
        }) })
      }
      await loadDashboard()
      paymentDialogOpen = false
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : 'Could not save this payment.'
    } finally {
      busy = false
    }
  }

  async function removeScheduledBill(billId: number) {
    errorMessage = ''
    try {
      await apiRequest(`/scheduled-bills/${billId}`, { method: 'DELETE' })
      scheduledBills = scheduledBills.filter((bill) => bill.id !== billId)
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : 'Could not delete this scheduled bill.'
    }
  }

  let balanceRows = $derived.by(() => {
    const activeUser = currentUser
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
    return users.filter((user) => user.id !== activeUser.id && Math.abs(balances.get(user.id) || 0) > 0.004)
      .map((user) => ({ user, amount: balances.get(user.id) || 0 }))
      .sort((left, right) => Math.abs(right.amount) - Math.abs(left.amount))
  })
  let owedToYou = $derived(balanceRows.reduce((total, row) => total + Math.max(row.amount, 0), 0))
  let youOwe = $derived(balanceRows.reduce((total, row) => total + Math.max(-row.amount, 0), 0))
  let netBalance = $derived(owedToYou - youOwe)
  let recentBills = $derived([...bills].slice(-5).reverse())

  onMount(async () => {
    token = localStorage.getItem('ssplit-token') || ''
    if (token) {
      try {
        const response = await apiRequest<{ user: User }>('/auth/me')
        currentUser = response.user
        await loadDashboard()
      } catch {
        token = ''
        localStorage.removeItem('ssplit-token')
      }
    }
    checkingSession = false
  })
</script>

{#if checkingSession}
  <main class="session-check" aria-label="Loading session"><span class="brand-mark">s/</span></main>
{:else if !token || !currentUser}
  <main class="login-page">
    <div class="login-ornament" aria-hidden="true"><span>01</span><span>02</span><span>03</span></div>
    <section class="login-panel">
      <a class="brand" href="/" aria-label="Split home"><span class="brand-mark">s/</span><span>SSPlit</span></a>
      <div class="login-copy"><p class="eyebrow">A little more together</p><h1>Good company.<br /><em>Clear accounts.</em></h1><p class="login-subtitle">Shared costs, without the awkward follow-up.</p></div>
      <form class="login-form" onsubmit={authenticate}>
        <label for="email">Email address</label><input id="email" name="email" type="email" autocomplete="username" placeholder="you@example.com" required />
        <label for="password">Password</label><input id="password" name="password" type="password" autocomplete="current-password" placeholder="Your password" required />
        {#if errorMessage}<p class="form-error" role="alert">{errorMessage}</p>{/if}
        <button class="button button-primary login-submit" type="submit" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'} <span aria-hidden="true">↗</span></button>
      </form>
      <p class="login-footnote">Your shared-expense space, all in one place.</p>
    </section>
    <aside class="login-aside"><div class="aside-note"><span class="aside-rule"></span><p>KEEP THE GOOD<br />PARTS SHARED.</p></div><div class="aside-number">S<br /><span>2026</span></div></aside>
  </main>
{:else}
  <div class="app-shell">
    <aside class="sidebar">
      <a class="brand sidebar-brand" href="/" aria-label="Split home"><span class="brand-mark">s/</span><span>split</span></a>
      <p class="nav-caption">YOUR SPACE</p>
      <nav class="side-nav" aria-label="Main navigation">
        <button class:active={currentView === 'overview'} onclick={() => currentView = 'overview'}><span class="nav-symbol">⌂</span> Overview</button>
        <button class:active={currentView === 'schedule'} onclick={() => currentView = 'schedule'}><span class="nav-symbol">◷</span> Scheduled <span class="nav-count">{scheduledBills.length}</span></button>
      </nav>
      <div class="sidebar-bottom"><div class="profile"><span class="avatar avatar-current">{initials(displayName(currentUser))}</span><span class="profile-copy"><strong>{displayName(currentUser)}</strong><small>{currentUser.email}</small></span></div><button class="sign-out" onclick={signOut}><span aria-hidden="true">↪</span> Sign out</button></div>
    </aside>
    <main class="workspace">
      <header class="topbar"><div class="breadcrumb"><span>Workspace</span><span class="crumb-divider">/</span><strong>{currentView === 'overview' ? 'Overview' : 'Scheduled payments'}</strong></div><button class="button button-primary top-add" onclick={openPaymentDialog}><span aria-hidden="true">+</span> New payment</button></header>
      {#if errorMessage && !paymentDialogOpen}<p class="page-error" role="alert">{errorMessage}</p>{/if}
      {#if currentView === 'overview'}
        <section class="page-heading"><div><p class="eyebrow">YOUR HOUSEHOLD, AT A GLANCE</p><h1>Overview<span class="heading-dot">.</span></h1></div><p class="heading-date">{new Intl.DateTimeFormat('en-US', { weekday: 'long', month: 'long', day: 'numeric' }).format(new Date())}</p></section>
        <section class="balance-strip" aria-label="Balance summary">
          <article class="balance-main"><div class="summary-label"><span class="summary-dot"></span> NET BALANCE</div><strong class:negative={netBalance < 0}>{netBalance >= 0 ? '+' : '−'}{money(Math.abs(netBalance))}</strong><p>{netBalance >= 0 ? 'You are owed more than you owe.' : 'You owe more than you are owed.'}</p><div class="balance-decoration" aria-hidden="true">↗</div></article>
          <article class="balance-small owed-card"><span class="summary-label">OWED TO YOU</span><strong>{money(owedToYou)}</strong><p>Across {balanceRows.filter((row) => row.amount > 0).length} {balanceRows.filter((row) => row.amount > 0).length === 1 ? 'person' : 'people'}</p><span class="metric-mark" aria-hidden="true">+</span></article>
          <article class="balance-small owe-card"><span class="summary-label">YOU OWE</span><strong>{money(youOwe)}</strong><p>Across {balanceRows.filter((row) => row.amount < 0).length} {balanceRows.filter((row) => row.amount < 0).length === 1 ? 'person' : 'people'}</p><span class="metric-mark" aria-hidden="true">−</span></article>
        </section>
        <div class="overview-grid">
          <section class="content-section balances-section"><div class="section-heading"><div><p class="eyebrow">SETTLE UP, SIMPLY</p><h2>Balances with people</h2></div><span class="section-count">{balanceRows.length} PEOPLE</span></div>
            {#if balanceRows.length}<div class="people-list">{#each balanceRows as row (row.user.id)}<div class="person-row"><span class="avatar" class:avatar-warm={row.amount < 0}>{initials(displayName(row.user))}</span><div class="person-info"><strong>{displayName(row.user)}</strong><small>{row.amount > 0 ? 'owes you' : 'you owe'}</small></div><strong class="person-amount" class:amount-positive={row.amount > 0} class:amount-negative={row.amount < 0}>{row.amount > 0 ? '+' : '−'}{money(Math.abs(row.amount))}</strong></div>{/each}</div>
            {:else}<div class="empty-state compact-empty"><span class="empty-icon">✓</span><strong>All square for now</strong><p>New shared bills will show up here.</p></div>{/if}
          </section>
          <section class="content-section activity-section"><div class="section-heading"><div><p class="eyebrow">THE LATEST</p><h2>Recent payments</h2></div><span class="section-count">{bills.length} TOTAL</span></div>
            {#if recentBills.length}<div class="activity-list">{#each recentBills as bill (bill.id)}{@const payer = users.find((user) => user.id === Number(bill.paid_by))}<article class="activity-row"><span class="activity-icon">{bill.description.slice(0, 1).toUpperCase()}</span><div class="activity-info"><strong>{bill.description}</strong><small>Paid by {payer ? displayName(payer) : 'a member'} · {formatDate(bill.due_date)}</small></div><strong class="activity-amount">{money(bill.amount)}</strong></article>{/each}</div>
            {:else}<div class="empty-state compact-empty"><span class="empty-icon">＋</span><strong>No payments yet</strong><p>Start by adding a shared bill.</p></div>{/if}
          </section>
        </div>
        <section class="bottom-note"><span class="note-spark">✳</span><p><strong>Shared is a little easier.</strong> Add a payment to keep everyone on the same page.</p><button class="text-button" onclick={openPaymentDialog}>Add a payment <span aria-hidden="true">↗</span></button></section>
      {:else}
        <section class="page-heading schedule-heading"><div><p class="eyebrow">REPEATING HOUSEHOLD COSTS</p><h1>Scheduled<span class="heading-dot">.</span></h1></div><p class="heading-date">A clear view of what comes around again.</p></section>
        <section class="content-section schedule-section"><div class="section-heading"><div><p class="eyebrow">UPCOMING</p><h2>Recurring payments</h2></div><span class="section-count">{scheduledBills.length} SCHEDULED</span></div>
          {#if scheduledBills.length}<div class="schedule-list">{#each scheduledBills as bill (bill.id)}<article class="schedule-row"><span class="schedule-calendar"><small>{formatDate(bill.due_date).split(' ')[0]}</small><strong>{bill.due_date.slice(8, 10)}</strong></span><div class="schedule-info"><strong>{bill.description}</strong><small>{bill.frequency} · Next date {formatDate(bill.due_date)}</small></div><strong class="schedule-amount">{money(bill.amount)}</strong><button class="icon-button delete-button" aria-label={`Delete ${bill.description}`} title="Delete scheduled payment" onclick={() => removeScheduledBill(bill.id)}>×</button></article>{/each}</div>
          {:else}<div class="empty-state"><span class="empty-icon">◷</span><strong>No scheduled payments</strong><p>Create a recurring bill to keep regular costs in view.</p><button class="button button-secondary" onclick={openPaymentDialog}>Create scheduled payment</button></div>{/if}
        </section>
      {/if}
      <footer class="workspace-footer"><span>SPLIT · SHARED EXPENSES</span><span>Made for the people you live, travel, and laugh with.</span></footer>
    </main>
  </div>
{/if}

{#if paymentDialogOpen}
  <div class="dialog-backdrop" role="presentation" onclick={(event) => event.target === event.currentTarget && (paymentDialogOpen = false)}>
    <div class="payment-dialog" role="dialog" aria-modal="true" aria-labelledby="payment-title" tabindex="-1">
      <header class="dialog-header"><div><p class="eyebrow">ADD TO YOUR SPACE</p><h2 id="payment-title">New payment</h2></div><button class="icon-button close-button" aria-label="Close dialog" onclick={() => paymentDialogOpen = false}>×</button></header>
      <div class="payment-tabs" role="tablist" aria-label="Payment type"><button class:tab-active={paymentType === 'once'} role="tab" aria-selected={paymentType === 'once'} onclick={() => { paymentType = 'once'; errorMessage = '' }}>One-time</button><button class:tab-active={paymentType === 'recurring'} role="tab" aria-selected={paymentType === 'recurring'} onclick={() => { paymentType = 'recurring'; errorMessage = '' }}>Recurring</button></div>
      <form class="payment-form" onsubmit={createPayment}>
        <label for="description">What was it for?</label><input id="description" bind:value={description} placeholder="e.g. Friday dinner" maxlength="100" required />
        <div class="form-pair"><div><label for="amount">Total amount</label><div class="amount-input"><span>$</span><input id="amount" type="number" min="0.01" step="0.01" bind:value={amount} placeholder="0.00" required /></div></div><div><label for="due-date">{paymentType === 'once' ? 'Payment date' : 'Next due date'}</label><input id="due-date" type="date" bind:value={dueDate} required /></div></div>
        {#if paymentType === 'once'}
          <label for="paid-by">Who paid?</label><select id="paid-by" value={paidBy} onchange={(event) => updatePayer(event.currentTarget.value)} required>{#each users as user (user.id)}<option value={user.id}>{displayName(user)}{user.id === currentUser?.id ? ' (you)' : ''}</option>{/each}</select>
          <fieldset class="split-fieldset"><legend>Split this bill with</legend><p class="field-hint">Choose everyone sharing the cost, including the person who paid.</p><div class="split-options">{#each users as user (user.id)}<label class="split-option"><input type="checkbox" value={user.id} bind:group={splitBetween} /><span class="avatar mini-avatar">{initials(displayName(user))}</span><span>{displayName(user)}{user.id === currentUser?.id ? ' (you)' : ''}</span></label>{/each}</div></fieldset>
        {:else}
          <label for="frequency">Repeat</label><select id="frequency" bind:value={frequency}><option value="monthly">Every month</option><option value="daily">Every day</option><option value="yearly">Every year</option></select><p class="schedule-notice">Recurring payments are saved to your schedule. The current API does not attach split participants to scheduled bills.</p>
        {/if}
        {#if errorMessage}<p class="form-error" role="alert">{errorMessage}</p>{/if}
        <div class="dialog-actions"><button class="button button-quiet" type="button" onclick={() => paymentDialogOpen = false}>Cancel</button><button class="button button-primary" type="submit" disabled={busy}>{busy ? 'Saving…' : paymentType === 'once' ? 'Save payment' : 'Schedule payment'} <span aria-hidden="true">↗</span></button></div>
      </form>
    </div>
  </div>
{/if}
