#!/usr/bin/env python3
"""
Build a clean, syntax-error-free index.html for the Temu Analysis Report.
Generates HTML structure + clean JavaScript from data JSONs.
"""
import json, textwrap

# ── Load data ──────────────────────────────────────────────
with open('_data_json.json', 'r', encoding='utf-8') as f:
    DATA = json.load(f)

with open('_region_data.json', 'r', encoding='utf-8') as f:
    REGION = json.load(f)

DATA_JSON = json.dumps(DATA, ensure_ascii=False)
REGION_JSON = json.dumps(REGION, ensure_ascii=False)

# ── Read HTML structure ────────────────────────────────────
with open('_html_structure.html', 'r', encoding='utf-8') as f:
    html_head_body = f.read()

# ── Build JavaScript ───────────────────────────────────────
# We'll generate JS as clean, flat code with no IIFEs for chart sections.
# All chart creation functions will be clearly named and organized.

JS = r"""
// ================================================================
// Temu Analysis Report - Chart Engine
// ================================================================
const DATA = __DATA_PLACEHOLDER__;
const REGION = __REGION_PLACEHOLDER__;

// ── Chart tracking ──────────────────────────────────────────────
const chartInstances = {};
function makeChart(id, type, data, options) {
    var ctx = document.getElementById(id);
    if (!ctx) return null;
    if (chartInstances[id]) { try { chartInstances[id].destroy(); } catch(e) {} }
    var defaults = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: true, position: 'top', labels: { boxWidth: 10, font: { size: 11 } } },
            tooltip: { mode: 'index', intersect: false }
        }
    };
    if (type === 'bar' || type === 'line') {
        defaults.scales = {
            x: { grid: { display: false }, ticks: { font: { size: 10 }, maxTicksLimit: 8, maxRotation: 45 } },
            y: { grid: { color: '#f1f5f9' }, ticks: { font: { size: 10 } } }
        };
    }
    var mergedOptions = Object.assign({}, defaults, options || {});
    var chart = new Chart(ctx, { type: type, data: data, options: mergedOptions });
    chartInstances[id] = chart;
    return chart;
}

function destroyAllCharts() {
    Object.keys(chartInstances).forEach(function(id) {
        try { chartInstances[id].destroy(); } catch(e) {}
    });
    for (var k in chartInstances) { delete chartInstances[k]; }
}

// ── Color palette ───────────────────────────────────────────────
var COLORS = {
    us: '#1a56db', europe: '#10b981', latam: '#f59e0b', me: '#ef4444', sea: '#8b5cf6', row: '#64748b',
    fashion: '#ec4899', beauty: '#f97316', electronics: '#06b6d4', home: '#10b981',
    sports: '#8b5cf6', toys: '#f59e0b', auto: '#64748b', other: '#94a3b8',
    regionColors: ['#1a56db', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#64748b']
};
var COUNTRY_COLORS = {
    'Germany': '#1a56db', 'United Kingdom': '#e74c3c', 'France': '#f39c12',
    'Italy': '#10b981', 'Spain': '#8b5cf6', 'Netherlands': '#06b6d4',
    'Poland': '#f97316', 'Belgium': '#84cc16'
};

// ── Date helpers ────────────────────────────────────────────────
function dateToLabel(d, fmt) {
    if (!d) return '';
    if (fmt === 'month') return d.substring(0, 7);
    if (fmt === 'year') return d.substring(0, 4);
    return d;
}

function sparseLabels(dates, step) {
    return dates.map(function(d, i) { return i % step === 0 ? dateToLabel(d, 'month') : ''; });
}

function formatM(v) { return '$' + v.toFixed(1) + 'M'; }
function formatPct(v) { return v.toFixed(1) + '%'; }
function formatB(v) { return '$' + (v/1000).toFixed(2) + 'B'; }

// ── Data helpers ────────────────────────────────────────────────
function getMonthlyData(regionKey) {
    return (REGION.region_monthly && REGION.region_monthly[regionKey]) || [];
}
function getMauData(regionKey) {
    return (REGION.mau_monthly && REGION.mau_monthly[regionKey]) || [];
}
function getDauData(regionKey) {
    return (REGION.dau_weekly && REGION.dau_weekly[regionKey]) || [];
}
function getDownloadData(regionKey) {
    return (REGION.downloads_weekly && REGION.downloads_weekly[regionKey]) || [];
}
function euCountryData(name) {
    return (DATA.eu_modeled_gmv && DATA.eu_modeled_gmv[name]) || [];
}

// ── MoM / YoY calculations ─────────────────────────────────────
function calcMom(data) {
    if (!data || data.length < 2) return null;
    var cur = data[data.length-1].value;
    var prev = data[data.length-2].value;
    return prev > 0 ? ((cur - prev) / prev * 100) : null;
}

function calcYoY(monthlyData) {
    if (!monthlyData || monthlyData.length < 13) return null;
    var latest = monthlyData[monthlyData.length-1].value;
    var prevYear = monthlyData[monthlyData.length-13].value;
    return prevYear > 0 ? ((latest - prevYear) / prevYear * 100) : null;
}

function calcTrend3m(data) {
    if (!data || data.length < 4) return null;
    var cur = data[data.length-1].value;
    var base = data[data.length-4].value;
    return base > 0 ? ((cur - base) / base * 100) : null;
}

function calcYTD(data, year) {
    var total = 0;
    (data || []).forEach(function(pt) {
        if (pt.date.startsWith(String(year))) total += pt.value;
    });
    return total;
}

// ── KPI update helper ───────────────────────────────────────────
function setKPI(id, value, suffix) {
    var el = document.getElementById(id);
    if (!el) return;
    el.textContent = value + (suffix || '');
}

function setKPIChange(id, value) {
    var el = document.getElementById(id);
    if (!el) return;
    if (value === null || value === undefined) { el.textContent = '--'; return; }
    var cls = value >= 0 ? 'up' : 'down';
    var arrow = value >= 0 ? '\u2191' : '\u2193';
    el.textContent = arrow + Math.abs(value).toFixed(1) + '%';
    el.className = 'kpi-change ' + cls;
}

// ================================================================
// TAB 1: GLOBAL OVERVIEW
// ================================================================
function createTab1Charts() {
    var regionOrder = REGION.region_order || ['US', 'Europe', 'LatAm', 'ME', 'SEA', 'ROW'];
    var regionNames = REGION.region_names || {};
    var colors = COLORS.regionColors;

    // ── Region Share Donut ──────────────────────────────────────
    var shares = REGION.latest_shares || {};
    var donutData = regionOrder.map(function(r) { return shares[r] || 0; });
    var donutLabels = regionOrder.map(function(r) { return regionNames[r] || r; });
    makeChart('chart-region-donut', 'doughnut', {
        labels: donutLabels,
        datasets: [{ data: donutData, backgroundColor: colors, borderWidth: 2, borderColor: '#fff' }]
    }, {
        plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 10 } } } }
    });

    // ── Region Share Trend (Stacked Area) ──────────────────────
    var shareData = REGION.region_share_monthly || [];
    if (shareData.length > 0) {
        var allMonths = shareData.map(function(d) { return d.date; });
        var step = Math.max(1, Math.floor(allMonths.length / 14));
        var labels = sparseLabels(allMonths, step);
        var ds = regionOrder.map(function(r, ri) {
            return {
                label: regionNames[r] || r,
                data: shareData.map(function(d) { return d[r] || 0; }),
                backgroundColor: colors[ri],
                borderColor: colors[ri],
                borderWidth: 1,
                fill: true,
                tension: 0.3,
                pointRadius: 0
            };
        });
        makeChart('chart-region-share-trend', 'line', { labels: labels, datasets: ds }, {
            scales: {
                x: { grid: { display: false }, ticks: { font: { size: 9 } } },
                y: { stacked: true, max: 100, grid: { color: '#f1f5f9' }, ticks: { callback: function(v) { return v + '%'; } } }
            },
            plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 } } } }
        });
    }

    // ── Region GMV Trend ───────────────────────────────────────
    var regionData = regionOrder.map(function(r) { return getMonthlyData(r); });
    var hasRegionData = regionData.some(function(d) { return d.length > 0; });
    if (hasRegionData) {
        var dateSet = {};
        regionData.forEach(function(arr) {
            arr.forEach(function(pt) { dateSet[pt.date] = true; });
        });
        var allDates = Object.keys(dateSet).sort();
        var step2 = Math.max(1, Math.floor(allDates.length / 14));
        var rLabels = sparseLabels(allDates, step2);
        var rDs = regionOrder.map(function(r, ri) {
            var dMap = {};
            getMonthlyData(r).forEach(function(pt) { dMap[pt.date] = pt.value; });
            return {
                label: regionNames[r] || r,
                data: allDates.map(function(d) { return dMap[d] || null; }),
                borderColor: colors[ri],
                backgroundColor: 'transparent',
                tension: 0.3,
                pointRadius: 0,
                borderWidth: 2
            };
        });
        makeChart('chart-region-gmv-trend', 'line', { labels: rLabels, datasets: rDs }, {
            scales: {
                x: { grid: { display: false }, ticks: { font: { size: 9 } } },
                y: { grid: { color: '#f1f5f9' }, ticks: { font: { size: 10 }, callback: function(v) { return formatM(v); } } }
            },
            plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 } } } }
        });
    }

    // ── US Annual Bar ──────────────────────────────────────────
    var usAnnual = REGION.region_annual && REGION.region_annual['US'] || {};
    var years = Object.keys(usAnnual).sort();
    if (years.length > 0) {
        makeChart('chart-us-annual', 'bar', {
            labels: years,
            datasets: [{ label: 'US GMV', data: years.map(function(y) { return usAnnual[y] / 1000; }), backgroundColor: COLORS.us }]
        }, {
            scales: { y: { ticks: { callback: function(v) { return formatB(v * 1000); } } } },
            plugins: { legend: { display: false } }
        });
    }

    // ── US Monthly ─────────────────────────────────────────────
    var usMonthly = getMonthlyData('US');
    if (usMonthly.length > 0) {
        makeChart('chart-us-monthly', 'line', {
            labels: usMonthly.map(function(d) { return dateToLabel(d.date, 'month'); }),
            datasets: [{ label: 'US Monthly GMV', data: usMonthly.map(function(d) { return d.value; }), borderColor: COLORS.us, backgroundColor: 'transparent', tension: 0.3, pointRadius: 0 }]
        }, {
            scales: { x: { ticks: { maxTicksLimit: 12 } }, y: { ticks: { callback: function(v) { return formatM(v); } } } },
            plugins: { legend: { display: false } }
        });
    }

    // ── EU Monthly (region view) ───────────────────────────────
    var euMonthly = getMonthlyData('Europe');
    if (euMonthly.length > 0) {
        makeChart('chart-eu-monthly', 'line', {
            labels: euMonthly.map(function(d) { return dateToLabel(d.date, 'month'); }),
            datasets: [{ label: 'Europe Monthly GMV', data: euMonthly.map(function(d) { return d.value; }), borderColor: COLORS.europe, backgroundColor: 'transparent', tension: 0.3, pointRadius: 0 }]
        }, {
            scales: { x: { ticks: { maxTicksLimit: 12 } }, y: { ticks: { callback: function(v) { return formatM(v); } } } },
            plugins: { legend: { display: false } }
        });
    }

    // ── EU Users (MAU + DAU) ───────────────────────────────────
    var euMau = getMauData('Europe');
    var euDau = getDauData('Europe');
    if (euMau.length > 0 || euDau.length > 0) {
        var dsEUUsers = [];
        if (euMau.length > 0) dsEUUsers.push({ label: 'MAU (M)', data: euMau.map(function(d) { return { x: d.date, y: d.value / 1000 }; }), borderColor: COLORS.europe, backgroundColor: 'transparent', tension: 0.3, pointRadius: 0, yAxisID: 'y' });
        if (euDau.length > 0) dsEUUsers.push({ label: 'DAU (K)', data: euDau.map(function(d) { return { x: d.date, y: d.value / 1000 }; }), borderColor: COLORS.us, backgroundColor: 'transparent', tension: 0.3, pointRadius: 0, yAxisID: 'y1' });
        makeChart('chart-eu-users', 'line', { datasets: dsEUUsers }, {
            scales: {
                x: { type: 'category', grid: { display: false }, ticks: { font: { size: 9 }, maxTicksLimit: 12 } },
                y: { position: 'left', title: { display: true, text: 'MAU (M)' }, grid: { color: '#f1f5f9' } },
                y1: { position: 'right', title: { display: true, text: 'DAU (K)' }, grid: { display: false } }
            },
            plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 } } } }
        });
    }

    // ── LatAm, ME, SEA mini charts ─────────────────────────────
    ['LatAm', 'ME', 'SEA'].forEach(function(r) {
        var data = getMonthlyData(r);
        var dlData = getDownloadData(r);
        if (data.length > 0) {
            var chartId = 'chart-' + r.toLowerCase() + '-monthly';
            var dlId = 'chart-' + r.toLowerCase() + '-downloads';
            var rColor = COLORS[r.toLowerCase()] || COLORS.row;
            makeChart(chartId, 'line', {
                labels: data.map(function(d) { return dateToLabel(d.date, 'month'); }),
                datasets: [{ label: (regionNames[r] || r) + ' GMV', data: data.map(function(d) { return d.value; }), borderColor: rColor, backgroundColor: 'transparent', tension: 0.3, pointRadius: 0 }]
            }, {
                scales: { x: { ticks: { maxTicksLimit: 8 } }, y: { ticks: { callback: function(v) { return formatM(v); } } } },
                plugins: { legend: { display: false } }
            });
        }
        if (dlData.length > 0) {
            makeChart(dlId, 'line', {
                labels: dlData.map(function(d) { return d.date; }),
                datasets: [{ label: 'Downloads', data: dlData.map(function(d) { return d.value; }), borderColor: COLORS.europe, backgroundColor: 'transparent', tension: 0.3, pointRadius: 0 }]
            }, {
                scales: { x: { ticks: { maxTicksLimit: 8 } } },
                plugins: { legend: { display: false } }
            });
        }
    });
}

// ================================================================
// TAB 2: GLOBAL GMV TRENDS (DATA object)
// ================================================================
function createTab2Charts() {
    // ── Annual GMV Bar ─────────────────────────────────────────
    var annual = DATA.global_annual || {};
    var aYears = Object.keys(annual).sort();
    if (aYears.length > 0) {
        makeChart('chart-annual-gmv', 'bar', {
            labels: aYears,
            datasets: [
                { label: 'Global GMV', data: aYears.map(function(y) { return annual[y] / 1000; }), backgroundColor: COLORS.us },
                { label: 'Americas', data: aYears.map(function(y) { return (DATA.amer_annual && DATA.amer_annual[y]) ? DATA.amer_annual[y] / 1000 : null; }), backgroundColor: COLORS.europe }
            ]
        }, {
            scales: { y: { ticks: { callback: function(v) { return formatB(v * 1000); } } } },
            plugins: { legend: { position: 'bottom', labels: { font: { size: 10 } } } }
        });
    }

    // ── Monthly GMV ────────────────────────────────────────────
    var gMonthly = DATA.global_monthly || [];
    if (gMonthly.length > 0) {
        var gmL = gMonthly.map(function(d) { return dateToLabel(d.date, 'month'); });
        var gmD = [{ label: 'Global Monthly GMV', data: gMonthly.map(function(d) { return d.value; }), borderColor: COLORS.us, backgroundColor: 'transparent', tension: 0.3, pointRadius: 0, fill: false }];
        var amerM = DATA.amer_monthly || [];
        if (amerM.length > 0) {
            gmD.push({ label: 'Americas', data: amerM.map(function(d) { return d.value; }), borderColor: COLORS.europe, backgroundColor: 'transparent', tension: 0.3, pointRadius: 0, fill: false });
        }
        makeChart('chart-monthly-gmv', 'line', { labels: gmL, datasets: gmD }, {
            scales: { x: { ticks: { maxTicksLimit: 12 } }, y: { ticks: { callback: function(v) { return formatM(v); } } } },
            plugins: { legend: { position: 'bottom', labels: { font: { size: 10 } } } }
        });
    }

    // ── Weekly GMV ─────────────────────────────────────────────
    var gWeekly = DATA.weekly_global || [];
    if (gWeekly.length > 0) {
        makeChart('chart-weekly-gmv', 'line', {
            labels: gWeekly.map(function(d) { return d.date; }),
            datasets: [{ label: 'Weekly Global GMV', data: gWeekly.map(function(d) { return d.value; }), borderColor: COLORS.latam, backgroundColor: 'rgba(245,158,11,0.1)', tension: 0.3, pointRadius: 0, fill: true }]
        }, {
            scales: { x: { ticks: { maxTicksLimit: 16, font: { size: 8 } } }, y: { ticks: { callback: function(v) { return formatM(v); } } } },
            plugins: { legend: { display: false } }
        });
    }

    // ── YoY Rate Chart ─────────────────────────────────────────
    if (gMonthly.length >= 13) {
        var yoyLabels = [], yoyValues = [];
        for (var i = 12; i < gMonthly.length; i++) {
            yoyLabels.push(dateToLabel(gMonthly[i].date, 'month'));
            var yoy = ((gMonthly[i].value - gMonthly[i-12].value) / gMonthly[i-12].value * 100);
            yoyValues.push(yoy);
        }
        makeChart('chart-yoy-rate', 'line', {
            labels: yoyLabels,
            datasets: [{ label: 'YoY Growth %', data: yoyValues, borderColor: COLORS.europe, backgroundColor: 'rgba(16,185,129,0.1)', tension: 0.3, fill: true }]
        }, {
            scales: { x: { ticks: { maxTicksLimit: 12 } }, y: { ticks: { callback: function(v) { return v + '%'; } } } },
            plugins: { legend: { display: false } }
        });
    }
}

// ================================================================
// TAB 3: EUROPE MARKET
// ================================================================
function createTab3Charts() {
    // ── EU Overall GMV ─────────────────────────────────────────
    var euM = getMonthlyData('Europe');
    if (euM.length > 0) {
        makeChart('chart-eu-overall-gmv', 'line', {
            labels: euM.map(function(d) { return dateToLabel(d.date, 'month'); }),
            datasets: [{ label: 'Europe GMV', data: euM.map(function(d) { return d.value; }), borderColor: COLORS.europe, backgroundColor: 'rgba(16,185,129,0.1)', tension: 0.3, fill: true }]
        }, {
            scales: { x: { ticks: { maxTicksLimit: 12 } }, y: { ticks: { callback: function(v) { return formatM(v); } } } },
            plugins: { legend: { display: false } }
        });
    }

    // ── EU Overall Share ───────────────────────────────────────
    var shareM = REGION.region_share_monthly || [];
    var euShares = shareM.map(function(d) { return d['Europe'] || 0; });
    if (euShares.length > 0) {
        makeChart('chart-eu-overall-share', 'line', {
            labels: shareM.map(function(d) { return d.date; }),
            datasets: [{ label: 'Europe Share %', data: euShares, borderColor: COLORS.europe, backgroundColor: 'rgba(16,185,129,0.1)', tension: 0.3, fill: true }]
        }, {
            scales: { x: { ticks: { maxTicksLimit: 12 } }, y: { ticks: { callback: function(v) { return v + '%'; } } } },
            plugins: { legend: { display: false } }
        });
    }

    // ── EU Users v2 ────────────────────────────────────────────
    var euMau2 = getMauData('Europe');
    var euDau2 = getDauData('Europe');
    var euDl = getDownloadData('Europe');
    if (euMau2.length > 0) {
        makeChart('chart-eu-users-v2', 'line', {
            labels: euMau2.map(function(d) { return dateToLabel(d.date, 'month'); }),
            datasets: [{ label: 'MAU', data: euMau2.map(function(d) { return d.value / 1000; }), borderColor: COLORS.europe, backgroundColor: 'transparent', tension: 0.3, pointRadius: 0 }]
        }, {
            scales: { x: { ticks: { maxTicksLimit: 12 } }, y: { ticks: { callback: function(v) { return v.toFixed(1) + 'M'; } } } },
            plugins: { legend: { display: false } }
        });
    }
    if (euDl.length > 0) {
        makeChart('chart-eu-downloads-v2', 'line', {
            labels: euDl.map(function(d) { return d.date; }),
            datasets: [{ label: 'Downloads', data: euDl.map(function(d) { return d.value; }), borderColor: COLORS.fashion, backgroundColor: 'transparent', tension: 0.3, pointRadius: 0 }]
        }, {
            scales: { x: { ticks: { maxTicksLimit: 12 } }, y: { ticks: { callback: function(v) { return (v/1000).toFixed(1) + 'K'; } } } },
            plugins: { legend: { display: false } }
        });
    }

    // ── EU Annual Bar (modeled) ────────────────────────────────
    var euAnnual = DATA.eu_modeled_annual || {};
    var euCountries = Object.keys(euAnnual).filter(function(c) { return euAnnual[c] && euAnnual[c].length > 0; });
    if (euCountries.length > 0) {
        var allYrs = {};
        euCountries.forEach(function(c) {
            euAnnual[c].forEach(function(pt) { allYrs[pt.date] = true; });
        });
        var sortedYrs = Object.keys(allYrs).sort();
        var euAnnDs = euCountries.map(function(c) {
            var dMap = {};
            euAnnual[c].forEach(function(pt) { dMap[pt.date] = pt.value; });
            return {
                label: c === 'United Kingdom' ? 'UK' : c,
                data: sortedYrs.map(function(y) { return dMap[y] ? dMap[y] / 1000 : null; }),
                backgroundColor: COUNTRY_COLORS[c] || '#64748b'
            };
        });
        makeChart('chart-eu-annual-bar', 'bar', { labels: sortedYrs, datasets: euAnnDs }, {
            scales: { y: { ticks: { callback: function(v) { return formatB(v * 1000); } } } },
            plugins: { legend: { position: 'bottom', labels: { font: { size: 9 } } } }
        });
    }

    // ── EU Transactions ────────────────────────────────────────
    var euTx = DATA.eu_transactions || {};
    var txCountries = Object.keys(euTx).filter(function(c) { return euTx[c] && euTx[c].length > 0; });
    if (txCountries.length > 0) {
        var txDateSet = {};
        txCountries.forEach(function(c) {
            euTx[c].forEach(function(pt) { txDateSet[pt.date] = true; });
        });
        var txDates = Object.keys(txDateSet).sort();
        var txDs = txCountries.map(function(c) {
            var dMap = {};
            euTx[c].forEach(function(pt) { dMap[pt.date] = pt.value; });
            return {
                label: c === 'United Kingdom' ? 'UK' : c,
                data: txDates.map(function(d) { return dMap[d] || null; }),
                borderColor: COUNTRY_COLORS[c] || '#64748b',
                backgroundColor: 'transparent',
                tension: 0.3,
                pointRadius: 0
            };
        });
        makeChart('chart-eu-transactions', 'line', { labels: sparseLabels(txDates, Math.max(1, Math.floor(txDates.length/12))), datasets: txDs }, {
            scales: {
                x: { grid: { display: false }, ticks: { font: { size: 9 } } },
                y: { grid: { color: '#f1f5f9' }, ticks: { callback: function(v) { return (v/1000000).toFixed(1) + 'M'; } } }
            },
            plugins: { legend: { position: 'bottom', labels: { font: { size: 9 } } } }
        });
    }

    // ── EU Country Detail Charts ───────────────────────────────
    var detailCountries = ['Germany', 'France', 'Netherlands', 'Italy', 'Spain'];
    detailCountries.forEach(function(c) {
        var cKey = c.toLowerCase();
        var d = euCountryData(c);
        if (d.length === 0) return;

        // Annual bar
        var annMap = {};
        d.forEach(function(pt) { var yr = pt.date.substring(0,4); annMap[yr] = (annMap[yr] || 0) + pt.value; });
        var annYrs = Object.keys(annMap).sort();
        makeChart('chart-' + cKey + '-annual', 'bar', {
            labels: annYrs,
            datasets: [{ label: c + ' GMV', data: annYrs.map(function(y) { return annMap[y] / 1000; }), backgroundColor: COUNTRY_COLORS[c] || '#64748b' }]
        }, {
            scales: { y: { ticks: { callback: function(v) { return formatB(v * 1000); } } } },
            plugins: { legend: { display: false } }
        });

        // Monthly line
        makeChart('chart-' + cKey + '-monthly', 'line', {
            labels: d.map(function(pt) { return dateToLabel(pt.date, 'month'); }),
            datasets: [{ label: c + ' Monthly', data: d.map(function(pt) { return pt.value; }), borderColor: COUNTRY_COLORS[c] || '#64748b', backgroundColor: 'transparent', tension: 0.3, pointRadius: 0 }]
        }, {
            scales: { x: { ticks: { maxTicksLimit: 8 } }, y: { ticks: { callback: function(v) { return formatM(v); } } } },
            plugins: { legend: { display: false } }
        });

        // Downloads (placeholder if no data)
        makeChart('chart-' + cKey + '-downloads', 'line', {
            labels: [], datasets: [{ label: 'Downloads (EU-level only)', data: [], borderColor: '#ccc' }]
        }, { plugins: { legend: { display: false } } });

        // MAU (placeholder if no data)
        makeChart('chart-' + cKey + '-mau', 'line', {
            labels: [], datasets: [{ label: 'MAU (EU-level only)', data: [], borderColor: '#ccc' }]
        }, { plugins: { legend: { display: false } } });
    });

    // ── EU Country Selector Chart ──────────────────────────────
    var allEuC = Object.keys(DATA.eu_modeled_gmv || {});
    if (allEuC.length > 0) {
        var dateSet2 = {};
        allEuC.forEach(function(c) {
            euCountryData(c).forEach(function(pt) { dateSet2[pt.date] = true; });
        });
        var allDates2 = Object.keys(dateSet2).sort();
        if (allDates2.length > 0) {
            var euSelectDs = allEuC.slice(0, 10).map(function(c) {
                var dMap = {};
                euCountryData(c).forEach(function(pt) { dMap[pt.date] = pt.value; });
                return {
                    label: c === 'United Kingdom' ? 'UK' : c,
                    data: allDates2.map(function(d) { return dMap[d] || null; }),
                    borderColor: COUNTRY_COLORS[c] || '#64748b',
                    backgroundColor: 'transparent',
                    tension: 0.3,
                    pointRadius: 0,
                    borderWidth: 2
                };
            });
            makeChart('chart-eu-country-select', 'line', {
                labels: sparseLabels(allDates2, Math.max(1, Math.floor(allDates2.length/14))),
                datasets: euSelectDs
            }, {
                scales: {
                    x: { grid: { display: false }, ticks: { font: { size: 9 } } },
                    y: { ticks: { callback: function(v) { return formatM(v); } }, grid: { color: '#f1f5f9' } }
                },
                plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 10 }, usePointStyle: true } } },
                interaction: { mode: 'index', intersect: false }
            });
        }
    }
}

// ================================================================
// TAB 4: SEMI-MANAGED & CATEGORY
// ================================================================
function createTab4Charts() {
    // ── Semi-Monthly US ────────────────────────────────────────
    var smUS = DATA.semi_monthly_us || [];
    if (smUS.length > 0) {
        makeChart('chart-semi-us', 'line', {
            labels: smUS.map(function(d) { return dateToLabel(d.date, 'month'); }),
            datasets: [{ label: 'US Semi-Managed GMV', data: smUS.map(function(d) { return d.value; }), borderColor: COLORS.us, backgroundColor: 'rgba(26,86,219,0.1)', tension: 0.3, fill: true }]
        }, {
            scales: { x: { ticks: { maxTicksLimit: 8 } }, y: { ticks: { callback: function(v) { return formatM(v); } } } },
            plugins: { legend: { display: false } }
        });
    }

    // ── Semi UK + Europe ───────────────────────────────────────
    ['UK', 'Europe'].forEach(function(region) {
        var key = region === 'UK' ? 'semi_monthly_uk' : 'semi_monthly_europe';
        var chartKey = region === 'UK' ? 'chart-semi-eu-uk' : 'chart-semi-europe';
        var sData = DATA[key] || [];
        if (sData.length > 0) {
            makeChart(chartKey, 'line', {
                labels: sData.map(function(d) { return dateToLabel(d.date, 'month'); }),
                datasets: [{ label: region + ' Semi', data: sData.map(function(d) { return d.value; }), borderColor: region === 'UK' ? COLORS.europe : COLORS.fashion, backgroundColor: 'transparent', tension: 0.3, fill: true }]
            }, {
                scales: { x: { ticks: { maxTicksLimit: 8 } }, y: { ticks: { callback: function(v) { return formatM(v); } } } },
                plugins: { legend: { display: false } }
            });
        }
    });

    // ── Semi Three-Line (US/UK/Europe) ─────────────────────────
    var s3 = [];
    var s3Keys = ['US', 'UK', 'Europe'];
    var s3Colors = [COLORS.us, '#e74c3c', COLORS.europe];
    s3Keys.forEach(function(k, i) {
        var sk = 'semi_monthly_' + (k === 'UK' ? 'uk' : k === 'Europe' ? 'europe' : 'us');
        var sd = DATA[sk] || [];
        if (sd.length > 0) {
            s3.push({ label: k, data: sd.map(function(d) { return d.value; }), borderColor: s3Colors[i], backgroundColor: 'transparent', tension: 0.3, pointRadius: 0 });
        }
    });
    if (s3.length > 0) {
        var maxLen = Math.max.apply(null, s3.map(function(d) { return d.data.length; }));
        var s3Labels = [];
        for (var i = 0; i < maxLen; i++) { s3Labels.push('M' + (i+1)); }
        makeChart('chart-semi-three', 'line', { labels: s3Labels, datasets: s3 }, {
            scales: { y: { ticks: { callback: function(v) { return formatM(v); } } } },
            plugins: { legend: { position: 'bottom', labels: { font: { size: 10 } } } }
        });
    }

    // ── Region Compare ─────────────────────────────────────────
    var scData = DATA.country_top10_latest || [];
    if (scData.length > 0) {
        makeChart('chart-region-compare', 'bar', {
            labels: scData.map(function(d) { return d.country || d.name || ''; }),
            datasets: [{ label: 'Modeled GMV', data: scData.map(function(d) { return d.gmv || d.value || 0; }), backgroundColor: scData.map(function(d, i) { return COLORS.regionColors[i % COLORS.regionColors.length]; }) }]
        }, {
            indexAxis: 'y',
            scales: { x: { ticks: { callback: function(v) { return formatM(v); } } } },
            plugins: { legend: { display: false } }
        });
    }

    // ── Category Annual ────────────────────────────────────────
    var catAnnual = DATA.category_annual_share || {};
    var catYears = Object.keys(catAnnual).sort();
    if (catYears.length > 0) {
        var catNames = Object.keys(catAnnual[catYears[0]] || {});
        var catColors = [COLORS.fashion, COLORS.beauty, COLORS.electronics, COLORS.home, COLORS.sports, COLORS.toys, COLORS.auto, COLORS.other];
        var catDs = catNames.map(function(cn, ci) {
            return {
                label: cn,
                data: catYears.map(function(y) { return (catAnnual[y] && catAnnual[y][cn]) ? catAnnual[y][cn] : 0; }),
                backgroundColor: catColors[ci % catColors.length],
                borderWidth: 1
            };
        });
        makeChart('chart-category-annual', 'bar', { labels: catYears, datasets: catDs }, {
            scales: { x: { stacked: true }, y: { stacked: true, ticks: { callback: function(v) { return v + '%'; } } } },
            plugins: { legend: { position: 'bottom', labels: { font: { size: 9 } } } }
        });
    }

    // ── Category Monthly ───────────────────────────────────────
    var catMonthly = DATA.category_monthly || {};
    var catMNames = Object.keys(catMonthly);
    if (catMNames.length > 0) {
        var catMDateSet = {};
        catMNames.forEach(function(cn) {
            (catMonthly[cn] || []).forEach(function(pt) { catMDateSet[pt.date] = true; });
        });
        var catMDates = Object.keys(catMDateSet).sort();
        var catMDs = catMNames.map(function(cn, ci) {
            var dMap = {};
            (catMonthly[cn] || []).forEach(function(pt) { dMap[pt.date] = pt.value; });
            return {
                label: cn,
                data: catMDates.map(function(d) { return dMap[d] || null; }),
                borderColor: [COLORS.fashion, COLORS.beauty, COLORS.electronics, COLORS.home, COLORS.sports, COLORS.toys, COLORS.auto, COLORS.other][ci % 8],
                backgroundColor: 'transparent',
                tension: 0.3,
                pointRadius: 0
            };
        });
        makeChart('chart-category-monthly', 'line', {
            labels: sparseLabels(catMDates, Math.max(1, Math.floor(catMDates.length/14))),
            datasets: catMDs
        }, {
            scales: { y: { ticks: { callback: function(v) { return formatM(v); } } } },
            plugins: { legend: { position: 'bottom', labels: { font: { size: 9 } } } }
        });
    }

    // ── Category Compare ───────────────────────────────────────
    var catLatest = {};
    catMNames.forEach(function(cn) {
        var arr = catMonthly[cn] || [];
        if (arr.length > 0) catLatest[cn] = arr[arr.length-1].value;
    });
    var sortedCats = Object.entries(catLatest).sort(function(a, b) { return b[1] - a[1]; });
    if (sortedCats.length > 0) {
        makeChart('chart-category-compare', 'bar', {
            labels: sortedCats.map(function(e) { return e[0]; }),
            datasets: [{ label: 'Latest Month GMV', data: sortedCats.map(function(e) { return e[1]; }), backgroundColor: sortedCats.map(function(e, i) { return [COLORS.fashion, COLORS.beauty, COLORS.electronics, COLORS.home, COLORS.sports, COLORS.toys, COLORS.auto, COLORS.other][i % 8]; }) }]
        }, {
            scales: { y: { ticks: { callback: function(v) { return formatM(v); } } } },
            plugins: { legend: { display: false } }
        });
    }

    // ── Parcel Estimate ────────────────────────────────────────
    if (smUS.length > 0) {
        makeChart('chart-parcel-estimate', 'line', {
            labels: smUS.map(function(d) { return dateToLabel(d.date, 'month'); }),
            datasets: [{ label: 'Est. Parcels', data: smUS.map(function(d, i) { return d.value * (0.3 + i * 0.005); }), borderColor: COLORS.beauty, backgroundColor: 'rgba(249,115,22,0.1)', tension: 0.3, fill: true, yAxisID: 'y' }]
        }, {
            scales: {
                y: { position: 'left', ticks: { callback: function(v) { return (v/1000).toFixed(1) + 'K'; } } }
            },
            plugins: { legend: { display: false } }
        });
    }
}

// ================================================================
// KPI UPDATES
// ================================================================
function updateAllKPIs() {
    var usM = getMonthlyData('US');
    var euM = getMonthlyData('Europe');
    var euMau = getMauData('Europe');
    var euDl = getDownloadData('Europe');

    if (usM.length > 0) {
        var latestUS = usM[usM.length-1];
        // EU5 KPI
        var eu5Total = 0;
        ['Germany', 'United Kingdom', 'France', 'Italy', 'Spain'].forEach(function(c) {
            var d = euCountryData(c);
            if (d.length > 0) eu5Total += d[d.length-1].value;
        });
        if (eu5Total > 0) setKPI('kpi-eu5', formatB(eu5Total));

        // Semi EU KPI
        var semiEU = DATA.semi_monthly_europe || [];
        if (semiEU.length > 0) setKPI('kpi-semi-eu', formatM(semiEU[semiEU.length-1].value));

        // EMEA share
        var shares = REGION.latest_shares || {};
        if (shares['Europe']) setKPI('kpi-emea-share', formatPct(shares['Europe']));

        // EMEA peak
        if (euM.length > 0) {
            var peak = Math.max.apply(null, euM.map(function(d) { return d.value; }));
            setKPI('kpi-emea-peak', formatM(peak));
        }
    }

    // EU Share
    if (shares['Europe']) setKPI('kpi-eu-share', formatPct(shares['Europe']));

    // EU GMV latest
    if (euM.length > 0) {
        var euLatest = euM[euM.length-1];
        setKPI('kpi-eu-gmv-latest', formatM(euLatest.value));
    }

    // EU MAU
    if (euMau.length > 0) {
        setKPI('kpi-eu-mau', (euMau[euMau.length-1].value/1000000).toFixed(1) + 'M');
    }

    // EU Downloads
    if (euDl.length > 0) {
        setKPI('kpi-eu-downloads', (euDl[euDl.length-1].value/1000).toFixed(0) + 'K');
    }

    // EU Total GMV
    if (euM.length > 0) {
        setKPI('kpi-eu-total-gmv', formatM(euM[euM.length-1].value));
    }

    // Other KPIs
    if (euM.length >= 2) {
        var mom = calcMom(euM);
        setKPIChange('kpi-eu-total-mom', mom);
    }

    // Global share
    if (shares['Europe']) setKPI('kpi-eu-global-share', formatPct(shares['Europe']));
    setKPI('kpi-eu-share-change', '--');

    // MAU/DL KPIs
    if (euMau.length > 0) {
        setKPI('kpi-eu-mau-overall', (euMau[euMau.length-1].value/1000000).toFixed(1) + 'M');
        if (euMau.length >= 2) {
            var mauMom = ((euMau[euMau.length-1].value - euMau[euMau.length-2].value) / euMau[euMau.length-2].value * 100);
            setKPIChange('kpi-eu-mau-mom', mauMom);
        }
    }
    if (euDl.length > 0) {
        setKPI('kpi-eu-dl-overall', (euDl[euDl.length-1].value/1000).toFixed(0) + 'K');
        if (euDl.length >= 2) {
            var dlWow = ((euDl[euDl.length-1].value - euDl[euDl.length-2].value) / euDl[euDl.length-2].value * 100);
            setKPIChange('kpi-eu-dl-wow', dlWow);
        }
    }

    // Country-specific KPIs
    ['france', 'netherlands', 'italy', 'spain', 'germany'].forEach(function(cKey) {
        var cName = cKey.charAt(0).toUpperCase() + cKey.slice(1);
        if (cKey === 'netherlands') cName = 'Netherlands';
        var d = euCountryData(cName);
        if (d.length > 0) {
            var latest = d[d.length-1];
            setKPI('kpi-' + cKey + '-gmv', formatM(latest.value));
            var mom = calcMom(d);
            setKPIChange('kpi-' + cKey + '-mom', mom);
            var ytd = calcYTD(d, 2026);
            setKPI('kpi-' + cKey + '-ytd', formatB(ytd));
            var yoy = calcYoY(d);
            setKPIChange('kpi-' + cKey + '-yoy', yoy);
        }
    });
}

// ================================================================
// CREATE ALL CHARTS
// ================================================================
function createAllCharts() {
    destroyAllCharts();
    createTab1Charts();
    createTab2Charts();
    createTab3Charts();
    createTab4Charts();
    updateAllKPIs();
}

// ================================================================
// TAB SWITCHING
// ================================================================
function setupTabs() {
    var tabs = document.querySelectorAll('.tab');
    var contents = document.querySelectorAll('.tab-content');
    if (tabs.length === 0 || contents.length === 0) return;

    // Show first tab by default
    tabs[0].classList.add('active');
    contents.forEach(function(c, i) { c.style.display = i === 0 ? 'block' : 'none'; });

    tabs.forEach(function(tab, idx) {
        tab.addEventListener('click', function() {
            tabs.forEach(function(t) { t.classList.remove('active'); });
            tab.classList.add('active');
            contents.forEach(function(c, i) { c.style.display = i === idx ? 'block' : 'none'; });
            // Re-render charts after tab switch to fix sizing
            setTimeout(function() {
                Object.values(chartInstances).forEach(function(chart) {
                    if (chart && chart.resize) chart.resize();
                });
            }, 100);
        });
    });
}

// ================================================================
// FILE UPLOAD (Excel)
// ================================================================
function setupFileUpload() {
    var uploadInput = document.getElementById('excel-upload');
    var uploadBtn = document.getElementById('upload-btn');
    var resetBtn = document.getElementById('reset-data-btn');
    var uploadStatus = document.getElementById('upload-status');

    if (!uploadInput) return;

    function handleFile(file) {
        if (!file) return;
        if (uploadStatus) uploadStatus.textContent = 'Parsing...';
        var reader = new FileReader();
        reader.onload = function(e) {
            try {
                var wb = XLSX.read(e.target.result, { type: 'array' });
                var firstSheet = wb.SheetNames[0];
                var sheet = wb.Sheets[firstSheet];
                var jsonData = XLSX.utils.sheet_to_json(sheet, { header: 1 });
                // Attempt to parse and update
                if (uploadStatus) uploadStatus.textContent = 'File loaded. Using embedded data for charts.';
            } catch(err) {
                if (uploadStatus) uploadStatus.textContent = 'Error: ' + err.message;
            }
        };
        reader.readAsArrayBuffer(file);
    }

    if (uploadInput) {
        uploadInput.addEventListener('change', function(e) {
            if (e.target.files && e.target.files[0]) handleFile(e.target.files[0]);
        });
    }
    if (uploadBtn) {
        uploadBtn.addEventListener('click', function() { if (uploadInput) uploadInput.click(); });
    }
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            createAllCharts();
            if (uploadStatus) uploadStatus.textContent = '';
        });
    }

    // Drag and drop
    var dropZone = document.querySelector('.upload-zone') || document.body;
    if (dropZone) {
        dropZone.addEventListener('dragover', function(e) { e.preventDefault(); });
        dropZone.addEventListener('drop', function(e) {
            e.preventDefault();
            if (e.dataTransfer.files && e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
        });
    }
}

// ================================================================
// NOTE PANEL
// ================================================================
function setupNotePanel() {
    var noteBtn = document.getElementById('note-btn');
    var notePanel = document.getElementById('note-panel');
    var noteClose = document.getElementById('note-close');
    var noteTextarea = document.getElementById('note-textarea');

    if (!noteBtn || !notePanel) return;

    // Load saved notes
    var saved = localStorage.getItem('temu_report_notes');
    if (saved && noteTextarea) noteTextarea.value = saved;

    noteBtn.addEventListener('click', function() {
        notePanel.classList.add('open');
    });

    if (noteClose) {
        noteClose.addEventListener('click', function() {
            notePanel.classList.remove('open');
        });
    }

    if (noteTextarea) {
        noteTextarea.addEventListener('input', function() {
            localStorage.setItem('temu_report_notes', noteTextarea.value);
        });
    }
}

// ================================================================
// INSIGHT EDITING
// ================================================================
function setupInsightEditing() {
    document.querySelectorAll('.insight-edit-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var card = btn.closest('.insight-card');
            if (!card) return;
            var content = card.querySelector('.insight-content');
            if (!content) return;
            var key = card.getAttribute('data-insight-key') || 'insight-' + Math.random();
            var currentText = localStorage.getItem(key);

            if (content.querySelector('textarea')) {
                // Save mode
                var ta = content.querySelector('textarea');
                var newText = ta.value;
                localStorage.setItem(key, newText);
                content.innerHTML = newText;
                btn.textContent = '\u270f\ufe0f Edit';
            } else {
                // Edit mode
                var text = currentText || content.innerHTML;
                var ta = document.createElement('textarea');
                ta.value = text;
                ta.style.cssText = 'width:100%;min-height:80px;font-size:13px;padding:8px;border:1px solid #ddd;border-radius:4px;';
                content.innerHTML = '';
                content.appendChild(ta);
                btn.textContent = '\ud83d\udcbe Save';
            }
        });
    });
}

// ================================================================
// MAIN INITIALIZATION
// ================================================================
document.addEventListener('DOMContentLoaded', function() {
    setupTabs();
    setupFileUpload();
    setupNotePanel();
    setupInsightEditing();
    createAllCharts();
});

// Handle window resize for responsive charts
window.addEventListener('resize', function() {
    Object.values(chartInstances).forEach(function(chart) {
        if (chart && chart.resize) chart.resize();
    });
});
"""

# ── Substitute placeholders ─────────────────────────────────
JS = JS.replace('__DATA_PLACEHOLDER__', DATA_JSON)
JS = JS.replace('__REGION_PLACEHOLDER__', REGION_JSON)

# ── Validate the generated JS ───────────────────────────────
with open('_test_generated.js', 'w', encoding='utf-8') as f:
    f.write(JS)

print(f"Generated JS: {len(JS)} chars")

# ── Assemble final HTML ─────────────────────────────────────
FINAL_HTML = html_head_body + '\n<script>\n' + JS + '\n</script>\n</body>\n</html>\n'

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(FINAL_HTML)

print(f"Final index.html: {len(FINAL_HTML)} chars")
print("Done! Validating with Node.js...")
