/**
 * Chart.js Integration for Personal Expense Tracker
 * Renders interactive, theme-responsive financial charts with tooltip currency formatting.
 */

const chartInstances = {};

function getChartColors() {
    const isDark = document.documentElement.getAttribute("data-theme") === "dark";
    return {
        textColor: isDark ? "#94a3b8" : "#64748b",
        gridColor: isDark ? "rgba(255, 255, 255, 0.08)" : "rgba(0, 0, 0, 0.06)",
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    };
}

/**
 * 1. Income vs Expense Comparison Chart (Bar)
 */
function createIncomeExpenseChart(canvasId, incomeAmount, expenseAmount, currencySymbol = "₹") {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    const colors = getChartColors();
    const ctx = canvas.getContext("2d");

    chartInstances[canvasId] = new Chart(ctx, {
        type: "bar",
        data: {
            labels: ["Income", "Expenses"],
            datasets: [{
                label: "Amount",
                data: [incomeAmount, expenseAmount],
                backgroundColor: ["#16a34a", "#dc2626"],
                borderRadius: 8,
                barThickness: 54
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return ` ${currencySymbol}${context.parsed.y.toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: colors.textColor, font: { family: colors.fontFamily } }
                },
                y: {
                    grid: { color: colors.gridColor },
                    ticks: {
                        color: colors.textColor,
                        font: { family: colors.fontFamily },
                        callback: function (value) {
                            return `${currencySymbol}${value.toLocaleString("en-IN")}`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * 2. Category-wise Expense Breakdown Chart (Doughnut)
 */
function createCategoryDoughnutChart(canvasId, labels, amounts, currencySymbol = "₹") {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    const colors = getChartColors();
    const ctx = canvas.getContext("2d");

    const categoryPalette = [
        "#3b82f6", "#0d9488", "#f59e0b", "#ec4899", "#8b5cf6",
        "#10b981", "#ef4444", "#6366f1", "#14b8a6", "#f97316",
        "#64748b"
    ];

    if (!amounts || amounts.length === 0 || amounts.every(v => v === 0)) {
        // Display empty state in chart
        chartInstances[canvasId] = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: ["No Expense Data"],
                datasets: [{
                    data: [1],
                    backgroundColor: [colors.gridColor]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                }
            }
        });
        return;
    }

    chartInstances[canvasId] = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: amounts,
                backgroundColor: categoryPalette.slice(0, labels.length),
                borderWidth: 2,
                borderColor: document.documentElement.getAttribute("data-theme") === "dark" ? "#111827" : "#ffffff"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "68%",
            plugins: {
                legend: {
                    position: "right",
                    labels: {
                        color: colors.textColor,
                        font: { family: colors.fontFamily, size: 12 },
                        boxWidth: 12,
                        padding: 12
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const val = context.parsed;
                            return ` ${context.label}: ${currencySymbol}${val.toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * 3. Monthly Trends Chart (Dual Line / Smooth Area Chart)
 */
function createMonthlyTrendsChart(canvasId, labels, incomeData, expenseData, currencySymbol = "₹") {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    const colors = getChartColors();
    const ctx = canvas.getContext("2d");

    chartInstances[canvasId] = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Income",
                    data: incomeData,
                    borderColor: "#16a34a",
                    backgroundColor: "rgba(22, 163, 74, 0.08)",
                    borderWidth: 3,
                    tension: 0.35,
                    fill: true,
                    pointBackgroundColor: "#16a34a",
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                {
                    label: "Expenses",
                    data: expenseData,
                    borderColor: "#dc2626",
                    backgroundColor: "rgba(220, 38, 38, 0.08)",
                    borderWidth: 3,
                    tension: 0.35,
                    fill: true,
                    pointBackgroundColor: "#dc2626",
                    pointRadius: 4,
                    pointHoverRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: "index"
            },
            plugins: {
                legend: {
                    position: "top",
                    labels: {
                        color: colors.textColor,
                        font: { family: colors.fontFamily, weight: "600" },
                        boxWidth: 14
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return ` ${context.dataset.label}: ${currencySymbol}${context.parsed.y.toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: colors.gridColor },
                    ticks: { color: colors.textColor, font: { family: colors.fontFamily } }
                },
                y: {
                    grid: { color: colors.gridColor },
                    ticks: {
                        color: colors.textColor,
                        font: { family: colors.fontFamily },
                        callback: function (val) {
                            return `${currencySymbol}${val.toLocaleString("en-IN")}`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * 4. Budget vs Actual Bar Chart for Reports & Budget Page
 */
function createBudgetVsActualChart(canvasId, labels, budgetData, spentData, currencySymbol = "₹") {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    const colors = getChartColors();
    const ctx = canvas.getContext("2d");

    chartInstances[canvasId] = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Budget Limit",
                    data: budgetData,
                    backgroundColor: "rgba(13, 148, 136, 0.8)",
                    borderRadius: 6
                },
                {
                    label: "Actual Spent",
                    data: spentData,
                    backgroundColor: "rgba(220, 38, 38, 0.8)",
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "top",
                    labels: {
                        color: colors.textColor,
                        font: { family: colors.fontFamily, weight: "600" }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return ` ${context.dataset.label}: ${currencySymbol}${context.parsed.y.toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: colors.textColor, font: { family: colors.fontFamily } }
                },
                y: {
                    grid: { color: colors.gridColor },
                    ticks: {
                        color: colors.textColor,
                        font: { family: colors.fontFamily },
                        callback: function (v) {
                            return `${currencySymbol}${v.toLocaleString("en-IN")}`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * 5. Daily Spending Trend Line Chart
 */
function createDailySpendingChart(canvasId, dates, amounts, currencySymbol = "₹") {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    const colors = getChartColors();
    const ctx = canvas.getContext("2d");

    chartInstances[canvasId] = new Chart(ctx, {
        type: "line",
        data: {
            labels: dates,
            datasets: [{
                label: "Daily Expense",
                data: amounts,
                borderColor: "#0d9488",
                backgroundColor: "rgba(13, 148, 136, 0.12)",
                borderWidth: 2.5,
                fill: true,
                tension: 0.3,
                pointRadius: 3,
                pointBackgroundColor: "#0d9488"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function (c) {
                            return ` Spent: ${currencySymbol}${c.parsed.y.toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: colors.gridColor },
                    ticks: { color: colors.textColor, font: { family: colors.fontFamily, size: 11 } }
                },
                y: {
                    grid: { color: colors.gridColor },
                    ticks: {
                        color: colors.textColor,
                        font: { family: colors.fontFamily },
                        callback: function (val) {
                            return `${currencySymbol}${val.toLocaleString("en-IN")}`;
                        }
                    }
                }
            }
        }
    });
}

// Global hook to refresh charts when theme switches
window.refreshAllCharts = function () {
    // If page has a registered chart redraw function, invoke it
    if (typeof window.renderPageCharts === "function") {
        window.renderPageCharts();
    }
};

