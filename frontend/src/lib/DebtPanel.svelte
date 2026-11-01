<script lang="ts">
  import type { ExpenseOverview } from './SplitService'

  type DebtPanelProps = {
    expenseOverview: ExpenseOverview
    initials: (name: string) => string
    money: (value: number | string) => string
  }

  let { expenseOverview, initials, money }: DebtPanelProps = $props()
</script>

<section class="page-heading">
  <div>
    <p class="eyebrow">SHARED EXPENSES, SETTLED CLEARLY</p>
    <h1>Debts<span class="heading-dot">.</span></h1>
  </div>
  <p class="heading-date">See what you owe and what others owe you.</p>
</section>

<section class="balance-strip" aria-label="Debt summary">
  <article class="balance-main">
    <div class="summary-label"><span class="summary-dot"></span> NET BALANCE</div>
    <strong class:negative={expenseOverview.summary.net_balance < 0}>
      {expenseOverview.summary.net_balance >= 0 ? '+' : '−'}{money(Math.abs(expenseOverview.summary.net_balance))}
    </strong>
    <p>{expenseOverview.summary.net_balance >= 0 ? 'You are owed more than you owe.' : 'You owe more than you are owed.'}</p>
    <div class="balance-decoration" aria-hidden="true">↗</div>
  </article>
  <article class="balance-small owe-card">
    <span class="summary-label">YOU OWE</span>
    <strong>{money(expenseOverview.summary.total_i_owe)}</strong>
    <p>Across {expenseOverview.my_debts.chart.length} {expenseOverview.my_debts.chart.length === 1 ? 'person' : 'people'}</p>
    <span class="metric-mark" aria-hidden="true">−</span>
  </article>
  <article class="balance-small owed-card">
    <span class="summary-label">OWED TO YOU</span>
    <strong>{money(expenseOverview.summary.total_owed_to_me)}</strong>
    <p>Across {expenseOverview.debts_to_me.chart.length} {expenseOverview.debts_to_me.chart.length === 1 ? 'person' : 'people'}</p>
    <span class="metric-mark" aria-hidden="true">+</span>
  </article>
</section>

<div class="overview-grid debt-grid">
  <section class="content-section">
    <div class="section-heading">
      <div><p class="eyebrow">YOUR SHARE OF THEIR PAYMENTS</p><h2>You owe</h2></div>
      <span class="section-count">{expenseOverview.my_debts.chart.length} {expenseOverview.my_debts.chart.length === 1 ? 'PERSON' : 'PEOPLE'}</span>
    </div>
    {#if expenseOverview.my_debts.chart.length}
      <div class="people-list">
        {#each expenseOverview.my_debts.chart as debt (debt.user_id)}
          <div class="person-row">
            <span class="avatar avatar-warm">{initials(debt.user_name)}</span>
            <div class="person-info"><strong>{debt.user_name}</strong><small>You owe them</small></div>
            <strong class="person-amount amount-negative">{money(debt.amount)}</strong>
          </div>
        {/each}
      </div>
    {:else}
      <div class="empty-state compact-empty"><span class="empty-icon">✓</span><strong>You’re all settled</strong><p>You don’t owe anyone right now.</p></div>
    {/if}
  </section>

  <section class="content-section">
    <div class="section-heading">
      <div><p class="eyebrow">YOUR SHARED BILLS</p><h2>Owed to you</h2></div>
      <span class="section-count">{expenseOverview.debts_to_me.chart.length} {expenseOverview.debts_to_me.chart.length === 1 ? 'PERSON' : 'PEOPLE'}</span>
    </div>
    {#if expenseOverview.debts_to_me.chart.length}
      <div class="people-list">
        {#each expenseOverview.debts_to_me.chart as debt (debt.user_id)}
          <div class="person-row">
            <span class="avatar">{initials(debt.user_name)}</span>
            <div class="person-info"><strong>{debt.user_name}</strong><small>They owe you</small></div>
            <strong class="person-amount amount-positive">{money(debt.amount)}</strong>
          </div>
        {/each}
      </div>
    {:else}
      <div class="empty-state compact-empty"><span class="empty-icon">＋</span><strong>No debts owed to you</strong><p>When others share your bills, they’ll show up here.</p></div>
    {/if}
  </section>
</div>
