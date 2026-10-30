<script lang="ts">
  type User = { id: number; email: string; user_name?: string }
  type Bill = { id: number; description: string; amount: string | number; paid_by: string | number; due_date?: string | null; split_between?: string }

  type BalanceRow = { user: User; amount: number }

  type OverviewPanelProps = {
    balanceRows: BalanceRow[]
    recentBills: Bill[]
    billCount: number
    users: User[]
    currentUser: User | null
    netBalance: number
    owedToYou: number
    youOwe: number
    onAddPayment: () => void
    displayName: (user: User) => string
    initials: (name: string) => string
    formatDate: (value?: string | null) => string
    money: (value: number | string) => string
  }

  let {
    balanceRows,
    recentBills,
    billCount,
    users,
    currentUser,
    netBalance,
    owedToYou,
    youOwe,
    onAddPayment,
    displayName,
    initials,
    formatDate,
    money,
  }: OverviewPanelProps = $props()
</script>

<section class="page-heading">
  <div>
    <p class="eyebrow">YOUR HOUSEHOLD, AT A GLANCE</p>
    <h1>Overview<span class="heading-dot">.</span></h1>
  </div>
  <p class="heading-date">{new Intl.DateTimeFormat('en-US', { weekday: 'long', month: 'long', day: 'numeric' }).format(new Date())}</p>
</section>

<section class="balance-strip" aria-label="Balance summary">
  <article class="balance-main">
    <div class="summary-label"><span class="summary-dot"></span> NET BALANCE</div>
    <strong class:negative={netBalance < 0}>{netBalance >= 0 ? '+' : '−'}{money(Math.abs(netBalance))}</strong>
    <p>{netBalance >= 0 ? 'You are owed more than you owe.' : 'You owe more than you are owed.'}</p>
    <div class="balance-decoration" aria-hidden="true">↗</div>
  </article>
  <article class="balance-small owed-card">
    <span class="summary-label">OWED TO YOU</span>
    <strong>{money(owedToYou)}</strong>
    <p>Across {balanceRows.filter((row) => row.amount > 0).length} {balanceRows.filter((row) => row.amount > 0).length === 1 ? 'person' : 'people'}</p>
    <span class="metric-mark" aria-hidden="true">+</span>
  </article>
  <article class="balance-small owe-card">
    <span class="summary-label">YOU OWE</span>
    <strong>{money(youOwe)}</strong>
    <p>Across {balanceRows.filter((row) => row.amount < 0).length} {balanceRows.filter((row) => row.amount < 0).length === 1 ? 'person' : 'people'}</p>
    <span class="metric-mark" aria-hidden="true">−</span>
  </article>
</section>

<div class="overview-grid">
  <section class="content-section balances-section">
    <div class="section-heading">
      <div><p class="eyebrow">SETTLE UP, SIMPLY</p><h2>Balances with people</h2></div>
      <span class="section-count">{balanceRows.length} PEOPLE</span>
    </div>
    {#if balanceRows.length}
      <div class="people-list">
        {#each balanceRows as row (row.user.id)}
          <div class="person-row">
            <span class="avatar" class:avatar-warm={row.amount < 0}>{initials(displayName(row.user))}</span>
            <div class="person-info"><strong>{displayName(row.user)}</strong><small>{row.amount > 0 ? 'owes you' : 'you owe'}</small></div>
            <strong class="person-amount" class:amount-positive={row.amount > 0} class:amount-negative={row.amount < 0}>{row.amount > 0 ? '+' : '−'}{money(Math.abs(row.amount))}</strong>
          </div>
        {/each}
      </div>
    {:else}
      <div class="empty-state compact-empty"><span class="empty-icon">✓</span><strong>All square for now</strong><p>New shared bills will show up here.</p></div>
    {/if}
  </section>

  <section class="content-section activity-section">
    <div class="section-heading">
      <div><p class="eyebrow">THE LATEST</p><h2>Recent payments</h2></div>
      <span class="section-count">{billCount} TOTAL</span>
    </div>
    {#if recentBills.length}
      <div class="activity-list">
        {#each recentBills as bill (bill.id)}
          {@const payer = users.find((user) => user.id === Number(bill.paid_by))}
          <article class="activity-row">
            <span class="activity-icon">{bill.description.slice(0, 1).toUpperCase()}</span>
            <div class="activity-info">
              <strong>{bill.description}</strong>
              <small>Paid by {payer ? displayName(payer) : 'a member'} · {formatDate(bill.due_date)}</small>
            </div>
            <strong class="activity-amount">{money(bill.amount)}</strong>
          </article>
        {/each}
      </div>
    {:else}
      <div class="empty-state compact-empty"><span class="empty-icon">＋</span><strong>No payments yet</strong><p>Start by adding a shared bill.</p></div>
    {/if}
  </section>
</div>

<section class="bottom-note">
  <span class="note-spark">✳</span>
  <p><strong>Shared is a little easier.</strong> Add a payment to keep everyone on the same page.</p>
  <button class="text-button" onclick={onAddPayment}>Add a payment <span aria-hidden="true">↗</span></button>
</section>
