<script lang="ts">
  type ScheduledBill = { id: number; description: string; amount: string | number; due_date: string; frequency: string }

  type SchedulePanelProps = {
    scheduledBills: ScheduledBill[]
    onOpenPaymentDialog: () => void
    onDeleteScheduledBill: (billId: number) => void
    formatDate: (value?: string | null) => string
    money: (value: number | string) => string
  }

  let {
    scheduledBills,
    onOpenPaymentDialog,
    onDeleteScheduledBill,
    formatDate,
    money,
  }: SchedulePanelProps = $props()
</script>

<section class="page-heading schedule-heading">
  <div>
    <p class="eyebrow">REPEATING HOUSEHOLD COSTS</p>
    <h1>Scheduled<span class="heading-dot">.</span></h1>
  </div>
  <p class="heading-date">A clear view of what comes around again.</p>
</section>

<section class="content-section schedule-section">
  <div class="section-heading">
    <div><p class="eyebrow">UPCOMING</p><h2>Recurring payments</h2></div>
    <span class="section-count">{scheduledBills.length} SCHEDULED</span>
  </div>

  {#if scheduledBills.length}
    <div class="schedule-list">
      {#each scheduledBills as bill (bill.id)}
        <article class="schedule-row">
          <span class="schedule-calendar"><small>{formatDate(bill.due_date).split(' ')[0]}</small><strong>{bill.due_date.slice(8, 10)}</strong></span>
          <div class="schedule-info"><strong>{bill.description}</strong><small>{bill.frequency} · Next date {formatDate(bill.due_date)}</small></div>
          <strong class="schedule-amount">{money(bill.amount)}</strong>
          <button class="icon-button delete-button" aria-label={`Delete ${bill.description}`} title="Delete scheduled payment" onclick={() => onDeleteScheduledBill(bill.id)}>×</button>
        </article>
      {/each}
    </div>
  {:else}
    <div class="empty-state">
      <span class="empty-icon">◷</span>
      <strong>No scheduled payments</strong>
      <p>Create a recurring bill to keep regular costs in view.</p>
      <button class="button button-secondary" onclick={onOpenPaymentDialog}>Create scheduled payment</button>
    </div>
  {/if}
</section>
