<script lang="ts">
  type LoginPageProps = {
    busy: boolean
    errorMessage: string
    onSubmit: (event: SubmitEvent) => void | Promise<void>
  }

  let { busy = false, errorMessage = '', onSubmit }: LoginPageProps = $props()
</script>

<main class="login-page">
  <div class="login-ornament" aria-hidden="true"><span>01</span><span>02</span><span>03</span></div>
  <section class="login-panel">
    <a class="brand" href="/" aria-label="Split home"><span class="brand-mark">s/</span><span>SSPlit</span></a>
    <div class="login-copy">
      <p class="eyebrow">A little more together</p>
      <h1>Good company.<br /><em>Clear accounts.</em></h1>
      <p class="login-subtitle">Shared costs, without the awkward follow-up.</p>
    </div>

    <form class="login-form" onsubmit={onSubmit}>
      <label for="email">Email address</label>
      <input id="email" name="email" type="email" autocomplete="username" placeholder="you@example.com" required />
      <label for="password">Password</label>
      <input id="password" name="password" type="password" autocomplete="current-password" placeholder="Your password" required />
      {#if errorMessage}
        <p class="form-error" role="alert">{errorMessage}</p>
      {/if}
      <button class="button button-primary login-submit" type="submit" disabled={busy}>
        {busy ? 'Signing in…' : 'Sign in'} <span aria-hidden="true">↗</span>
      </button>
    </form>

    <p class="login-footnote">Your shared-expense space, all in one place.</p>
  </section>

  <aside class="login-aside">
    <div class="aside-note"><span class="aside-rule"></span><p>KEEP THE GOOD<br />PARTS SHARED.</p></div>
    <div class="aside-number">S<br /><span>2026</span></div>
  </aside>
</main>
