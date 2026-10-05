<script lang="ts">
  type User = { id: number; email: string; user_name?: string }

  type SidebarProps = {
    currentUser: User | null
    currentView: 'overview' | 'schedule'
    scheduledBillsCount: number
    displayName: (user: User) => string
    initials: (name: string) => string
    onViewChange: (view: 'overview' | 'schedule') => void
    onSignOut: () => void
  }

  let {
    currentUser,
    currentView,
    scheduledBillsCount,
    displayName,
    initials,
    onViewChange,
    onSignOut,
  }: SidebarProps = $props()
</script>

<aside class="sidebar">
  <a class="brand sidebar-brand" href="/" aria-label="Split home"><span class="brand-mark">s/</span><span>split</span></a>
  <p class="nav-caption">YOUR SPACE</p>
  <nav class="side-nav" aria-label="Main navigation">
    <button class:active={currentView === 'overview'} onclick={() => onViewChange('overview')}><span class="nav-symbol">⌂</span> Overview</button>
    <button class:active={currentView === 'schedule'} onclick={() => onViewChange('schedule')}><span class="nav-symbol">◷</span> Scheduled <span class="nav-count">{scheduledBillsCount}</span></button>
  </nav>
  <div class="sidebar-bottom">
    <div class="profile">
      <span class="avatar avatar-current">{currentUser ? initials(displayName(currentUser)) : ''}</span>
      <span class="profile-copy">
        <strong>{currentUser ? displayName(currentUser) : ''}</strong>
        <small>{currentUser?.email ?? ''}</small>
      </span>
    </div>
    <button class="sign-out" onclick={onSignOut}><span aria-hidden="true">↪</span> Sign out</button>
  </div>
</aside>
