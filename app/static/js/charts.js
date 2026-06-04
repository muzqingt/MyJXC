/**
 * 图表组件库 — Chart.js 封装
 */

/**
 * 渲染销售趋势折线图
 * @param {string} canvasId - Canvas 元素 ID
 * @param {Object} data - {dates: [], amounts: []}
 */
function renderSalesTrendChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [{
                label: '销售金额 (¥)',
                data: data.amounts,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return '¥' + context.parsed.y.toLocaleString();
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '¥' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

/**
 * 渲染库存概览柱状图
 * @param {string} canvasId - Canvas 元素 ID
 * @param {Array} data - [{warehouse: string, stock: number}]
 */
function renderStockOverviewChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const colors = [
        'rgb(54, 162, 235)',
        'rgb(255, 99, 132)',
        'rgb(75, 192, 192)',
        'rgb(255, 205, 86)',
        'rgb(153, 102, 255)',
        'rgb(255, 159, 64)'
    ];

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.warehouse),
            datasets: [{
                label: '库存数量',
                data: data.map(d => d.stock),
                backgroundColor: colors.slice(0, data.length),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

/**
 * 渲染财务摘要折线图（收支对比）
 * @param {string} canvasId - Canvas 元素 ID
 * @param {Object} data - {dates: [], income: [], expense: []}
 */
function renderFinanceSummaryChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [
                {
                    label: '收入',
                    data: data.income,
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1
                },
                {
                    label: '支出',
                    data: data.expense,
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ¥' + context.parsed.y.toLocaleString();
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '¥' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

/**
 * 渲染饼图
 * @param {string} canvasId - Canvas 元素 ID
 * @param {Object} data - {labels: [], values: []}
 * @param {Object} options - 可选配置
 */
function renderPieChart(canvasId, data, options = {}) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const colors = [
        'rgb(54, 162, 235)',
        'rgb(255, 99, 132)',
        'rgb(75, 192, 192)',
        'rgb(255, 205, 86)',
        'rgb(153, 102, 255)',
        'rgb(255, 159, 64)',
        'rgb(201, 203, 207)',
        'rgb(46, 204, 113)'
    ];

    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: colors.slice(0, data.labels.length),
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return context.label + ': ' + context.parsed + ' (' + percentage + '%)';
                        }
                    }
                }
            },
            ...options
        }
    });
}

/**
 * 渲染环形图（仪表盘风格）
 * @param {string} canvasId - Canvas 元素 ID
 * @param {Object} data - {labels: [], values: []}
 * @param {Object} options - 可选配置
 */
function renderDoughnutChart(canvasId, data, options = {}) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const colors = [
        'rgb(54, 162, 235)',
        'rgb(255, 99, 132)',
        'rgb(75, 192, 192)',
        'rgb(255, 205, 86)',
        'rgb(153, 102, 255)',
        'rgb(255, 159, 64)'
    ];

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: colors.slice(0, data.labels.length),
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            ...options
        }
    });
}

/**
 * 通用图表创建函数
 * @param {string} canvasId - Canvas 元素 ID
 * @param {string} type - 图表类型 (line, bar, pie, doughnut)
 * @param {Object} data - 图表数据
 * @param {Object} options - 可选配置
 * @returns {Chart} Chart 实例
 */
function createChart(canvasId, type, data, options = {}) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    const defaultColors = [
        'rgb(54, 162, 235)',
        'rgb(255, 99, 132)',
        'rgb(75, 192, 192)',
        'rgb(255, 205, 86)',
        'rgb(153, 102, 255)',
        'rgb(255, 159, 64)'
    ];

    // 为没有颜色的数据集添加默认颜色
    if (data.datasets) {
        data.datasets.forEach((dataset, index) => {
            if (!dataset.backgroundColor) {
                dataset.backgroundColor = type === 'line'
                    ? defaultColors[index % defaultColors.length].replace('rgb', 'rgba').replace(')', ', 0.2)')
                    : defaultColors.slice(0, data.labels?.length || 6);
            }
            if (!dataset.borderColor && type === 'line') {
                dataset.borderColor = defaultColors[index % defaultColors.length];
            }
        });
    }

    return new Chart(ctx, {
        type: type,
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            ...options
        }
    });
}
