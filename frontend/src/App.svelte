<script lang="ts">
  import { onMount } from 'svelte'
  import LoginPage from './lib/LoginPage.svelte'
  import PaymentDialog from './lib/PaymentDialog.svelte'
  import OverviewPanel from './lib/OverviewPanel.svelte'
  import SchedulePanel from './lib/SchedulePanel.svelte'
  import Sidebar from './lib/Sidebar.svelte'
  import { AuthService } from './lib/AuthService'
  import { SplitService, type Bill, type ScheduledBill, type User } from './lib/SplitService'
  import {
    createPaymentPayload,
    displayName,
    formatDate,
    getBalanceRows,
    getRecentBills,
    initials,
    money,
    resetPaymentForm,
    validatePayment,
  } from './lib/split-logic'

  const authService = new AuthService()
  const splitService = new SplitService()

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

  const displayNameFn = displayName
  const moneyFn = money
  const initialsFn = initials
  const formatDateFn = formatDate

  async function loadDashboard() {
    const dashboard = await splitService.getDashboard()
    users = dashboard.users
    bills = dashboard.bills
    scheduledBills = dashboard.scheduledBills
    if (currentUser && paidBy === '') paidBy = currentUser.id
    if (currentUser && splitBetween.length === 0) splitBetween = [currentUser.id]
  }

  async function authenticate(event: SubmitEvent) {
    event.preventDefault()
    const formData = new FormData(event.currentTarget as HTMLFormElement)
    errorMessage = ''
    busy = true
    try {
      const session = await authService.login(
        String(formData.get('email') || ''),
        String(formData.get('password') || ''),
      )
      token = session.token
      authService.setToken(token)
      splitService.setToken(token)
      currentUser = session.user
      localStorage.setItem('ssplit-token', token)
      paidBy = currentUser.id
      splitBetween = [currentUser.id]
      await loadDashboard()
    } catch (error) {
      token = ''
      authService.clearToken()
      splitService.clearToken()
      currentUser = null
      errorMessage = error instanceof Error ? error.message : 'Unable to sign in.'
    } finally {
      busy = false
    }
  }

  async function signOut() {
    try { await authService.logout() } catch { /* The server session may already have expired. */ }
    token = ''
    authService.clearToken()
    splitService.clearToken()
    currentUser = null
    localStorage.removeItem('ssplit-token')
    users = []
    bills = []
    scheduledBills = []
    currentView = 'overview'
  }

  function openPaymentDialog() {
    errorMessage = ''
    const nextPayment = resetPaymentForm(currentUser)
    paymentType = nextPayment.paymentType
    description = nextPayment.description
    amount = nextPayment.amount
    dueDate = nextPayment.dueDate
    frequency = nextPayment.frequency
    paidBy = nextPayment.paidBy
    splitBetween = nextPayment.splitBetween
    paymentDialogOpen = true
  }

  function updatePayer(value: string) {
    paidBy = value ? Number(value) : ''
    if (paidBy !== '' && !splitBetween.includes(paidBy)) splitBetween = [...splitBetween, paidBy]
  }

  async function createPayment(event: SubmitEvent) {
    event.preventDefault()
    const validationMessage = validatePayment({ description, amount, dueDate, paymentType, paidBy, splitBetween })
    if (validationMessage) {
      errorMessage = validationMessage
      return
    }
    errorMessage = ''
    busy = true
    try {
      if (paymentType === 'once') {
        await splitService.createBill(createPaymentPayload({ description, amount, dueDate, paymentType, paidBy, splitBetween, frequency }))
      } else {
        await splitService.createScheduledBill(createPaymentPayload({ description, amount, dueDate, paymentType, paidBy, splitBetween, frequency }))
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
      await splitService.deleteScheduledBill(billId)
      scheduledBills = scheduledBills.filter((bill) => bill.id !== billId)
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : 'Could not delete this scheduled bill.'
    }
  }

  let balanceRows = $derived(getBalanceRows(users, bills, currentUser))
  let owedToYou = $derived(balanceRows.reduce((total, row) => total + Math.max(row.amount, 0), 0))
  let youOwe = $derived(balanceRows.reduce((total, row) => total + Math.max(-row.amount, 0), 0))
  let netBalance = $derived(owedToYou - youOwe)
  let recentBills = $derived(getRecentBills(bills))

  onMount(async () => {
    token = localStorage.getItem('ssplit-token') || ''
    authService.setToken(token)
    splitService.setToken(token)
    if (token) {
      try {
        const response = await authService.getMe()
        currentUser = response.user
        await loadDashboard()
      } catch {
        token = ''
        authService.clearToken()
        splitService.clearToken()
        localStorage.removeItem('ssplit-token')
      }
    }
    checkingSession = false
  })
</script>

{#if checkingSession}
  <main class="session-check" aria-label="Loading session"><span class="brand-mark">s/</span></main>
{:else if !token || !currentUser}
  <LoginPage {busy} errorMessage={errorMessage} onSubmit={authenticate} />
{:else}
  <div class="app-shell">
    <Sidebar
      currentUser={currentUser}
      currentView={currentView}
      scheduledBillsCount={scheduledBills.length}
      displayName={displayNameFn}
      initials={initialsFn}
      onViewChange={(view) => (currentView = view)}
      onSignOut={signOut}
    />
    <main class="workspace">
      <header class="topbar">
        <div class="breadcrumb"><span>Workspace</span><span class="crumb-divider">/</span><strong>{currentView === 'overview' ? 'Overview' : 'Scheduled payments'}</strong></div>
        <button class="button button-primary top-add" onclick={openPaymentDialog}><span aria-hidden="true">+</span> New payment</button>
      </header>
      {#if errorMessage && !paymentDialogOpen}<p class="page-error" role="alert">{errorMessage}</p>{/if}
      {#if currentView === 'overview'}
        <OverviewPanel
          balanceRows={balanceRows}
          recentBills={recentBills}
          billCount={bills.length}
          users={users}
          currentUser={currentUser}
          netBalance={netBalance}
          owedToYou={owedToYou}
          youOwe={youOwe}
          onAddPayment={openPaymentDialog}
          displayName={displayNameFn}
          initials={initialsFn}
          formatDate={formatDateFn}
          money={moneyFn}
        />
      {:else}
        <SchedulePanel
          scheduledBills={scheduledBills}
          onOpenPaymentDialog={openPaymentDialog}
          onDeleteScheduledBill={removeScheduledBill}
          formatDate={formatDateFn}
          money={moneyFn}
        />
      {/if}
      <footer class="workspace-footer"><span>SPLIT · SHARED EXPENSES</span><span>Made for the people you live, travel, and laugh with.</span></footer>
    </main>
  </div>
{/if}

<PaymentDialog
  bind:open={paymentDialogOpen}
  bind:paymentType={paymentType}
  bind:description={description}
  bind:amount={amount}
  bind:dueDate={dueDate}
  bind:frequency={frequency}
  bind:splitBetween={splitBetween}
  bind:paidBy={paidBy}
  bind:errorMessage={errorMessage}
  {users}
  {currentUser}
  {busy}
  onClose={() => (paymentDialogOpen = false)}
  onSubmit={createPayment}
  onTypeChange={(type) => {
    paymentType = type
    errorMessage = ''
  }}
  onPayerChange={(value) => updatePayer(value)}
/>
