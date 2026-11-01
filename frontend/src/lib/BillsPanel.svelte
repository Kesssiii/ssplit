<script lang="ts">
  import type { Bill, User } from './SplitService'

  const pageSize = 10

  type BillsPanelProps = {
    bills: Bill[]
    users: User[]
    currentUser: User
    displayName: (user: User) => string
    formatDate: (value?: string | null) => string
    money: (value: number | string) => string
  }

  let { bills, users, currentUser, displayName, formatDate, money }: BillsPanelProps = $props()
  let searchTerm = $state('')
  let currentPage = $state(1)

  function participantsFor(bill: Bill) {
    return [...new Set(String(bill.split_between ?? '')
      .split(',')
      .filter((value) => value.trim() !== '')
      .map((value) => Number(value.trim()))
      .filter((id) => Number.isInteger(id)))]
  }

  function nameFor(userId: number) {
    const user = users.find((candidate) => candidate.id === userId)
    return user ? displayName(user) : 'Unknown user'
  }

  let userBills = $derived(
    bills
      .filter((bill) => Number(bill.paid_by) === currentUser.id || participantsFor(bill).includes(currentUser.id))
      .sort((left, right) => (right.due_date ?? '').localeCompare(left.due_date ?? '') || right.id - left.id),
  )

  let matchingBills = $derived.by(() => {
    const query = searchTerm.trim().toLocaleLowerCase()
    if (!query) return userBills

    return userBills.filter((bill) => {
      const payerName = nameFor(Number(bill.paid_by))
      const participantNames = participantsFor(bill).map(nameFor).join(' ')
      return [
        bill.description,
        bill.amount,
        bill.due_date ?? '',
        payerName,
        participantNames,
      ].some((value) => String(value).toLocaleLowerCase().includes(query))
    })
  })

  let pageCount = $derived(Math.max(1, Math.ceil(matchingBills.length / pageSize)))
  let pageBills = $derived(matchingBills.slice((currentPage - 1) * pageSize, currentPage * pageSize))
  let firstVisibleBill = $derived(matchingBills.length ? (currentPage - 1) * pageSize + 1 : 0)
  let lastVisibleBill = $derived(Math.min(currentPage * pageSize, matchingBills.length))
  let visiblePages = $derived.by(() => {
    const firstPage = Math.max(1, Math.min(currentPage - 2, pageCount - 4))
    return Array.from({ length: Math.min(pageCount, 5) }, (_, index) => firstPage + index)
  })
</script>

<section class="page-heading bills-heading">
  <div>
    <p class="eyebrow">YOUR SHARED EXPENSES</p>
    <h1>Bills<span class="heading-dot">.</span></h1>
  </div>
  <p class="heading-date">All bills you paid or were included in.</p>
</section>

<section class="bills-section" aria-label="Your bills">
  <div class="bills-toolbar">
    <label class="bill-search">
      <span aria-hidden="true">⌕</span>
      <input
        aria-label="Search bills"
        type="search"
        placeholder="Search bills, people, or amounts"
        bind:value={searchTerm}
        oninput={() => (currentPage = 1)}
      />
    </label>
    <span class="section-count">{userBills.length} {userBills.length === 1 ? 'BILL' : 'BILLS'}</span>
  </div>

  {#if pageBills.length}
    <div class="bills-table-wrap">
      <table class="bills-table">
        <thead>
          <tr>
            <th scope="col">Bill</th>
            <th scope="col">Paid by</th>
            <th scope="col">Split between</th>
            <th scope="col">Due date</th>
            <th scope="col" class="bill-amount-cell">Amount</th>
          </tr>
        </thead>
        <tbody>
          {#each pageBills as bill (bill.id)}
            {@const payerId = Number(bill.paid_by)}
            <tr>
              <th scope="row">{bill.description || 'Untitled bill'}</th>
              <td>{nameFor(payerId)}{payerId === currentUser.id ? ' (you)' : ''}</td>
              <td>{participantsFor(bill).map(nameFor).join(', ') || 'No participants'}</td>
              <td>{formatDate(bill.due_date)}</td>
              <td class="bill-amount-cell">{money(bill.amount)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {:else if searchTerm.trim()}
    <div class="empty-state compact-empty"><span class="empty-icon">⌕</span><strong>No matching bills</strong><p>Try a different search term.</p></div>
  {:else}
    <div class="empty-state compact-empty"><span class="empty-icon">＋</span><strong>No bills yet</strong><p>Bills you pay or are included in will appear here.</p></div>
  {/if}

  <div class="bills-pagination">
    <p>Showing {firstVisibleBill}–{lastVisibleBill} of {matchingBills.length} {matchingBills.length === 1 ? 'bill' : 'bills'}</p>
    <nav aria-label="Bills pages">
      <button class="page-button" aria-label="Previous page" disabled={currentPage === 1} onclick={() => (currentPage -= 1)}>Previous</button>
      {#each visiblePages as page (page)}
        <button
          class="page-button page-number"
          aria-label={`Page ${page}`}
          aria-current={currentPage === page ? 'page' : undefined}
          class:active={currentPage === page}
          onclick={() => (currentPage = page)}
        >{page}</button>
      {/each}
      <button class="page-button" aria-label="Next page" disabled={currentPage === pageCount} onclick={() => (currentPage += 1)}>Next</button>
    </nav>
  </div>
</section>
