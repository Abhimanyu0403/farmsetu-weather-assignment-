/* ── helpers ─────────────────────────────────────────────── */

function getCsrf() {
  return document.cookie.split("; ")
    .find(r => r.startsWith("csrftoken="))
    ?.split("=")[1] ?? "";
}

async function apiFetch(url, options = {}) {
  const res = await fetch(url, options);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error ?? `HTTP ${res.status}`);
  return data;
}

/* ── state ───────────────────────────────────────────────── */

const DATE_PERIODS   = ["ann","jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec","win","spr","sum","aut"];
const RANKED_PERIODS = ["ann","jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec","win","spr","sum","aut"];

let chartInstance = null;
let activeDataset = null;
let activePeriod  = "ann";

/* ── DOM refs ────────────────────────────────────────────── */

const selRegion    = document.getElementById("sel-region");
const selParameter = document.getElementById("sel-parameter");
const selOrder     = document.getElementById("sel-order");
const btnLoad      = document.getElementById("btn-load");
const loadStatus   = document.getElementById("load-status");
const datasetsWrap = document.getElementById("datasets-wrapper");
const viewer       = document.getElementById("viewer");
const viewerTitle  = document.getElementById("viewer-title");
const periodSel    = document.getElementById("period-selector");
const chartCanvas  = document.getElementById("chart");
const tableWrap    = document.getElementById("data-table-wrapper");

/* ── bootstrap ───────────────────────────────────────────── */

async function init() {
  const [options] = await Promise.all([
    apiFetch("/api/options/"),
  ]);

  populate(selRegion,    options.regions,     "code", "name");
  populate(selParameter, options.parameters,  "code", "name");
  populate(selOrder,     options.order_types, "code", "name");

  await refreshDatasets();
}

function populate(select, items, valueKey, labelKey) {
  select.innerHTML = items
    .map(i => `<option value="${i[valueKey]}">${i[labelKey]}</option>`)
    .join("");
}

/* ── dataset list ────────────────────────────────────────── */

async function refreshDatasets() {
  const datasets = await apiFetch("/api/datasets/");

  if (!datasets.length) {
    datasetsWrap.innerHTML = `<p class="empty">No datasets imported yet.</p>`;
    return;
  }

  datasetsWrap.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Region</th>
          <th>Parameter</th>
          <th>Order</th>
          <th>Start year</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        ${datasets.map(ds => `
          <tr>
            <td>${ds.region_name}</td>
            <td>${ds.parameter_name}</td>
            <td>${ds.order_type}</td>
            <td>${ds.series_start_year ?? "—"}</td>
            <td>
              <button class="btn-view" data-id="${ds.id}" data-order="${ds.order_type}"
                      data-title="${ds.region_name} · ${ds.parameter_name} (${ds.order_type})">
                View
              </button>
            </td>
          </tr>`).join("")}
      </tbody>
    </table>`;

  datasetsWrap.querySelectorAll(".btn-view").forEach(btn => {
    btn.addEventListener("click", () => openViewer(
      Number(btn.dataset.id),
      btn.dataset.order,
      btn.dataset.title,
    ));
  });
}

/* ── import ──────────────────────────────────────────────── */

btnLoad.addEventListener("click", async () => {
  setStatus("", "");
  btnLoad.disabled = true;
  btnLoad.textContent = "Loading…";

  const regionOption    = selRegion.options[selRegion.selectedIndex];
  const parameterOption = selParameter.options[selParameter.selectedIndex];
  const orderOption     = selOrder.options[selOrder.selectedIndex];

  try {
    await apiFetch("/api/datasets/load/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrf(),
      },
      body: JSON.stringify({
        region_code:    selRegion.value,
        region_name:    regionOption.text,
        parameter_code: selParameter.value,
        parameter_name: parameterOption.text,
        order_type:     selOrder.value,
      }),
    });

    setStatus("Dataset imported successfully.", "success");
    await refreshDatasets();
  } catch (err) {
    setStatus(err.message, "error");
  } finally {
    btnLoad.disabled = false;
    btnLoad.textContent = "Load Dataset";
  }
});

function setStatus(msg, type) {
  loadStatus.textContent = msg;
  loadStatus.className = type;
}

/* ── viewer ──────────────────────────────────────────────── */

async function openViewer(datasetId, orderType, title) {
  activeDataset = { id: datasetId, orderType };
  activePeriod  = "ann";
  viewerTitle.textContent = title;
  viewer.style.display = "block";
  viewer.scrollIntoView({ behavior: "smooth" });

  buildPeriodButtons(orderType === "date" ? DATE_PERIODS : RANKED_PERIODS);
  await renderViewer();
}

function buildPeriodButtons(periods) {
  periodSel.innerHTML = periods.map(p =>
    `<button class="period-btn${p === activePeriod ? " active" : ""}" data-period="${p}">
      ${p.toUpperCase()}
    </button>`
  ).join("");

  periodSel.querySelectorAll(".period-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      activePeriod = btn.dataset.period;
      periodSel.querySelectorAll(".period-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      await renderViewer();
    });
  });
}

async function renderViewer() {
  if (!activeDataset) return;

  if (activeDataset.orderType === "date") {
    const rows = await apiFetch(`/api/observations/?dataset_id=${activeDataset.id}`);
    renderDateChart(rows, activePeriod);
    renderDateTable(rows, activePeriod);
  } else {
    const rows = await apiFetch(
      `/api/rankings/?dataset_id=${activeDataset.id}&period_code=${activePeriod}&limit=20`
    );
    renderRankedChart(rows);
    renderRankedTable(rows);
  }
}

/* ── charts ──────────────────────────────────────────────── */

function destroyChart() {
  if (chartInstance) { chartInstance.destroy(); chartInstance = null; }
}

function renderDateChart(rows, period) {
  destroyChart();
  const labels = rows.map(r => r.year);
  const values = rows.map(r => r[period]);

  chartInstance = new Chart(chartCanvas, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: period.toUpperCase(),
        data: values,
        borderColor: "#2563eb",
        backgroundColor: "rgba(37,99,235,.08)",
        borderWidth: 2,
        pointRadius: 0,
        tension: 0.3,
        fill: true,
        spanGaps: true,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { maxTicksLimit: 12 } },
        y: { ticks: { maxTicksLimit: 6 } },
      },
    },
  });
}

function renderRankedChart(rows) {
  destroyChart();
  const labels = rows.map(r => `#${r.rank} (${r.year})`);
  const values = rows.map(r => r.value);

  chartInstance = new Chart(chartCanvas, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "Value",
        data: values,
        backgroundColor: "rgba(37,99,235,.7)",
        borderRadius: 4,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { maxRotation: 45 } },
        y: { ticks: { maxTicksLimit: 6 } },
      },
    },
  });
}

/* ── tables ──────────────────────────────────────────────── */

function renderDateTable(rows, period) {
  if (!rows.length) { tableWrap.innerHTML = `<p class="empty">No data.</p>`; return; }

  tableWrap.innerHTML = `
    <table>
      <thead><tr><th>Year</th><th>${period.toUpperCase()}</th></tr></thead>
      <tbody>
        ${rows.map(r => `
          <tr>
            <td>${r.year}</td>
            <td>${r[period] ?? "—"}</td>
          </tr>`).join("")}
      </tbody>
    </table>`;
}

function renderRankedTable(rows) {
  if (!rows.length) { tableWrap.innerHTML = `<p class="empty">No data.</p>`; return; }

  tableWrap.innerHTML = `
    <table>
      <thead><tr><th>Rank</th><th>Year</th><th>Value</th></tr></thead>
      <tbody>
        ${rows.map(r => `
          <tr>
            <td>#${r.rank}</td>
            <td>${r.year}</td>
            <td>${r.value}</td>
          </tr>`).join("")}
      </tbody>
    </table>`;
}

/* ── start ───────────────────────────────────────────────── */

init().catch(console.error);
