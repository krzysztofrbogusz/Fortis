<script>
  // Read-only table view of a simple (unquoted) CSV, e.g. letters.csv.
  let { content = "" } = $props();

  const rows = $derived(
    content.trim() ? content.trim().split(/\r?\n/).map((line) => line.split(",")) : [],
  );
  const header = $derived(rows[0] ?? []);
  const body = $derived(rows.slice(1));
</script>

<div class="csv-wrap">
  {#if header.length}
    <table class="csv">
      <thead>
        <tr>
          {#each header as h}<th>{h}</th>{/each}
        </tr>
      </thead>
      <tbody>
        {#each body as row}
          <tr>
            {#each header as _, i}
              <td class:sym={i === 0}>{row[i] ?? ""}</td>
            {/each}
          </tr>
        {/each}
      </tbody>
    </table>
  {:else}
    <p class="empty">Empty file.</p>
  {/if}
</div>

<style>
  .csv-wrap {
    flex: 1;
    overflow: auto;
    margin: 0 16px 16px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--code-bg);
  }
  table.csv {
    border-collapse: collapse;
    font-family: var(--mono);
    font-size: 12px;
  }
  .csv th,
  .csv td {
    border: 1px solid var(--border);
    padding: 2px 7px;
    text-align: center;
    white-space: nowrap;
  }
  /* Sticky header row and sticky first (symbol) column. */
  .csv thead th {
    position: sticky;
    top: 0;
    z-index: 2;
    background: var(--panel);
    color: var(--text-h);
    font-weight: 600;
    font-family: var(--sans);
  }
  .csv td.sym,
  .csv th:first-child {
    position: sticky;
    left: 0;
    z-index: 1;
    background: var(--panel);
  }
  .csv thead th:first-child {
    z-index: 3;
  }
  .csv td.sym {
    font-family: var(--ipa);
    font-size: 15px;
    font-weight: 600;
    color: var(--text-h);
  }
  .empty {
    color: var(--muted);
    padding: 14px;
  }
</style>
