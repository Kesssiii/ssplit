<script lang="ts">
  type User = { id: number; email: string; user_name?: string }

  type PaymentDialogProps = {
    open?: boolean
    users?: User[]
    currentUser?: User | null
    paymentType?: 'once' | 'recurring'
    description?: string
    amount?: string
    dueDate?: string
    frequency?: string
    splitBetween?: number[]
    paidBy?: number | ''
    errorMessage?: string
    busy?: boolean
    onClose?: () => void
    onSubmit?: (event: SubmitEvent) => void | Promise<void>
    onTypeChange?: (type: 'once' | 'recurring') => void
    onPayerChange?: (value: string) => void
  }

  let {
    open = $bindable(false),
    users = [],
    currentUser = null,
    paymentType = $bindable<'once' | 'recurring'>('once'),
    description = $bindable(''),
    amount = $bindable(''),
    dueDate = $bindable(''),
    frequency = $bindable('monthly'),
    splitBetween = $bindable<number[]>([]),
    paidBy = $bindable<number | ''>(''),
    errorMessage = $bindable(''),
    busy = false,
    onClose = () => {},
    onSubmit = () => {},
    onTypeChange = () => {},
    onPayerChange = () => {},
  }: PaymentDialogProps = $props()

  const displayName = (user: User) => user.user_name || user.email.split('@')[0]
  const initials = (name: string) => name.split(/[\s.@_-]+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join('').toUpperCase()
</script>

{#if open}
  <div class="dialog-backdrop" role="presentation" onclick={(event) => event.target === event.currentTarget && onClose()}>
    <div class="payment-dialog" role="dialog" aria-modal="true" aria-labelledby="payment-title" tabindex="-1">
      <header class="dialog-header">
        <div>
          <p class="eyebrow">ADD TO YOUR SPACE</p>
          <h2 id="payment-title">New payment</h2>
        </div>
        <button class="icon-button close-button" aria-label="Close dialog" onclick={onClose}>×</button>
      </header>

      <div class="payment-tabs" role="tablist" aria-label="Payment type">
        <button class:tab-active={paymentType === 'once'} role="tab" aria-selected={paymentType === 'once'} onclick={() => onTypeChange('once')}>One-time</button>
        <button class:tab-active={paymentType === 'recurring'} role="tab" aria-selected={paymentType === 'recurring'} onclick={() => onTypeChange('recurring')}>Recurring</button>
      </div>

      <form class="payment-form" onsubmit={onSubmit}>
        <label for="description">What was it for?</label>
        <input id="description" bind:value={description} placeholder="e.g. Friday dinner" maxlength="100" required />

        <div class="form-pair">
          <div>
            <label for="amount">Total amount</label>
            <div class="amount-input">
              <span>$</span>
              <input id="amount" type="number" min="0.01" step="0.01" bind:value={amount} placeholder="0.00" required />
            </div>
          </div>
          <div>
            <label for="due-date">{paymentType === 'once' ? 'Payment date' : 'Next due date'}</label>
            <input id="due-date" type="date" bind:value={dueDate} required />
          </div>
        </div>

        {#if paymentType === 'once'}
          <label for="paid-by">Who paid?</label>
          <select id="paid-by" value={paidBy} onchange={(event) => onPayerChange(event.currentTarget.value)} required>
            {#each users as user (user.id)}
              <option value={user.id}>{displayName(user)}{user.id === currentUser?.id ? ' (you)' : ''}</option>
            {/each}
          </select>

          <fieldset class="split-fieldset">
            <legend>Split this bill with</legend>
            <p class="field-hint">Choose everyone sharing the cost, including the person who paid.</p>
            <div class="split-options">
              {#each users as user (user.id)}
                <label class="split-option">
                  <input type="checkbox" value={user.id} bind:group={splitBetween} />
                  <span class="avatar mini-avatar">{initials(displayName(user))}</span>
                  <span>{displayName(user)}{user.id === currentUser?.id ? ' (you)' : ''}</span>
                </label>
              {/each}
            </div>
          </fieldset>
        {:else}
          <label for="frequency">Repeat</label>
          <select id="frequency" bind:value={frequency}>
            <option value="monthly">Every month</option>
            <option value="daily">Every day</option>
            <option value="yearly">Every year</option>
          </select>
          <p class="schedule-notice">Recurring payments are saved to your schedule. The current API does not attach split participants to scheduled bills.</p>
        {/if}

        {#if errorMessage}
          <p class="form-error" role="alert">{errorMessage}</p>
        {/if}

        <div class="dialog-actions">
          <button class="button button-quiet" type="button" onclick={onClose}>Cancel</button>
          <button class="button button-primary" type="submit" disabled={busy}>
            {busy ? 'Saving…' : paymentType === 'once' ? 'Save payment' : 'Schedule payment'} <span aria-hidden="true">↗</span>
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}
