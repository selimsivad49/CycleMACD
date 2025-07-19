// CycleMACD Web Application JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const analysisForm = document.getElementById('analysisForm');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const resultsSection = document.getElementById('resultsSection');
    const resultsBody = document.getElementById('resultsBody');
    const chartModal = new bootstrap.Modal(document.getElementById('chartModal'));

    // フォーム送信処理
    analysisForm.addEventListener('submit', function(e) {
        e.preventDefault();
        performAnalysis();
    });

    function performAnalysis() {
        const selectedSymbols = getSelectedSymbols();
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        const timeframe = document.getElementById('timeframe').value;

        if (selectedSymbols.length === 0) {
            alert('分析する銘柄を選択してください。');
            return;
        }

        // ローディング表示
        showLoading();
        hideResults();

        // APIリクエスト
        fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                symbols: selectedSymbols,
                start_date: startDate,
                end_date: endDate,
                timeframe: timeframe
            })
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.success) {
                displayResults(data.results);
            } else {
                alert('分析中にエラーが発生しました: ' + data.error);
            }
        })
        .catch(error => {
            hideLoading();
            console.error('Error:', error);
            alert('通信エラーが発生しました。');
        });
    }

    function getSelectedSymbols() {
        const checkboxes = document.querySelectorAll('#symbolCheckboxes input[type="checkbox"]:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }

    function showLoading() {
        loadingOverlay.style.display = 'flex';
    }

    function hideLoading() {
        loadingOverlay.style.display = 'none';
    }

    function hideResults() {
        resultsSection.style.display = 'none';
    }

    function displayResults(results) {
        resultsBody.innerHTML = '';
        
        // 戦略リターンでソート
        results.sort((a, b) => {
            if (!a.success) return 1;
            if (!b.success) return -1;
            return b.data.total_return_strategy - a.data.total_return_strategy;
        });

        results.forEach(result => {
            const row = createResultRow(result);
            resultsBody.appendChild(row);
        });

        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    function createResultRow(result) {
        const row = document.createElement('tr');
        
        if (!result.success) {
            row.className = 'error-row';
            row.innerHTML = `
                <td><strong>${result.symbol}</strong></td>
                <td colspan="11" class="text-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${result.error}
                </td>
            `;
            return row;
        }

        const data = result.data;
        const tradeStats = result.trade_statistics;
        row.className = 'success-row fade-in';
        
        // Long/Short統計の取得
        const longStats = tradeStats.by_direction?.LONG || {};
        const shortStats = tradeStats.by_direction?.SHORT || {};
        
        row.innerHTML = `
            <td><strong>${result.symbol}</strong></td>
            <td>${formatPercentage(data.total_return_strategy)}</td>
            <td>${formatPercentage(data.total_return_market)}</td>
            <td>${data.trades}</td>
            <td>${formatPercentage(data.win_rate)}</td>
            <td class="negative">${formatPercentage(data.max_drawdown)}</td>
            <td>${data.sharpe_ratio.toFixed(2)}</td>
            <td>${longStats.win_rate ? longStats.win_rate.toFixed(1) + '%' : 'N/A'}</td>
            <td>${shortStats.win_rate ? shortStats.win_rate.toFixed(1) + '%' : 'N/A'}</td>
            <td>${longStats.pl_ratio ? longStats.pl_ratio.toFixed(2) : 'N/A'}</td>
            <td>${shortStats.pl_ratio ? shortStats.pl_ratio.toFixed(2) : 'N/A'}</td>
            <td>
                <button class="chart-button" onclick="showChart('${result.symbol}')" title="チャート表示">
                    <i class="fas fa-chart-line"></i>
                </button>
            </td>
        `;

        return row;
    }

    function formatPercentage(value) {
        const percentage = (value * 100).toFixed(2) + '%';
        if (value > 0) {
            return `<span class="positive">+${percentage}</span>`;
        } else if (value < 0) {
            return `<span class="negative">${percentage}</span>`;
        }
        return percentage;
    }

    // チャート表示関数をグローバルスコープに
    window.showChart = function(symbol) {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        const timeframe = document.getElementById('timeframe').value;
        
        const chartModalTitle = document.getElementById('chartModalTitle');
        const chartLoading = document.getElementById('chartLoading');
        const chartImage = document.getElementById('chartImage');
        const chartError = document.getElementById('chartError');

        const timeframeNames = {'D': '日足', 'W': '週足', 'M': '月足'};
        chartModalTitle.textContent = `${symbol} - 詳細チャート (${timeframeNames[timeframe]})`;
        
        // 初期状態
        chartLoading.classList.remove('d-none');
        chartImage.style.display = 'none';
        chartError.classList.add('d-none');
        document.getElementById('tradeStatistics').style.display = 'none';
        
        chartModal.show();

        fetch(`/chart/${symbol}?start_date=${startDate}&end_date=${endDate}&timeframe=${timeframe}`)
            .then(response => response.json())
            .then(data => {
                chartLoading.classList.add('d-none');
                
                if (data.chart) {
                    chartImage.src = 'data:image/png;base64,' + data.chart;
                    chartImage.style.display = 'block';
                    
                    // 取引統計を表示
                    if (data.trade_statistics) {
                        displayTradeStatistics(data.trade_statistics);
                        document.getElementById('tradeStatistics').style.display = 'block';
                    }
                } else {
                    chartError.textContent = data.error || 'チャート生成に失敗しました';
                    chartError.classList.remove('d-none');
                }
            })
            .catch(error => {
                chartLoading.classList.add('d-none');
                chartError.textContent = '通信エラーが発生しました';
                chartError.classList.remove('d-none');
                console.error('Chart error:', error);
            });
    };

    function displayTradeStatistics(tradeStats) {
        const overallStats = document.getElementById('overallStats');
        const longStats = document.getElementById('longStats');
        const shortStats = document.getElementById('shortStats');

        // 全体統計
        if (tradeStats.overall) {
            const overall = tradeStats.overall;
            overallStats.innerHTML = `
                <small class="text-muted">総取引数:</small> <strong>${overall.total_trades}</strong><br>
                <small class="text-muted">勝率:</small> <strong>${overall.win_rate.toFixed(1)}%</strong><br>
                <small class="text-muted">P/L比:</small> <strong>${overall.pl_ratio.toFixed(2)}</strong><br>
                <small class="text-muted">総損益:</small> <strong>${overall.total_pnl.toFixed(2)}</strong><br>
                <small class="text-muted">平均保有:</small> <strong>${overall.avg_holding_days.toFixed(1)}日</strong>
            `;
        }

        // Long統計
        if (tradeStats.by_direction && tradeStats.by_direction.LONG) {
            const long = tradeStats.by_direction.LONG;
            longStats.innerHTML = `
                <small class="text-muted">取引数:</small> <strong>${long.trade_count}</strong><br>
                <small class="text-muted">勝率:</small> <strong>${long.win_rate.toFixed(1)}%</strong><br>
                <small class="text-muted">P/L比:</small> <strong>${long.pl_ratio.toFixed(2)}</strong><br>
                <small class="text-muted">総損益:</small> <strong>${long.total_profit.toFixed(2)}</strong><br>
                <small class="text-muted">最大DD:</small> <strong>${long.max_drawdown.toFixed(2)}</strong>
            `;
        } else {
            longStats.innerHTML = '<small class="text-muted">LONG取引なし</small>';
        }

        // Short統計
        if (tradeStats.by_direction && tradeStats.by_direction.SHORT) {
            const short = tradeStats.by_direction.SHORT;
            shortStats.innerHTML = `
                <small class="text-muted">取引数:</small> <strong>${short.trade_count}</strong><br>
                <small class="text-muted">勝率:</small> <strong>${short.win_rate.toFixed(1)}%</strong><br>
                <small class="text-muted">P/L比:</small> <strong>${short.pl_ratio.toFixed(2)}</strong><br>
                <small class="text-muted">総損益:</small> <strong>${short.total_profit.toFixed(2)}</strong><br>
                <small class="text-muted">最大DD:</small> <strong>${short.max_drawdown.toFixed(2)}</strong>
            `;
        } else {
            shortStats.innerHTML = '<small class="text-muted">SHORT取引なし</small>';
        }
    }

    // 銘柄選択ユーティリティ関数をグローバルスコープに
    window.selectAllSymbols = function() {
        const checkboxes = document.querySelectorAll('#symbolCheckboxes input[type="checkbox"]');
        checkboxes.forEach(cb => cb.checked = true);
    };

    window.clearAllSymbols = function() {
        const checkboxes = document.querySelectorAll('#symbolCheckboxes input[type="checkbox"]');
        checkboxes.forEach(cb => cb.checked = false);
    };

    // 今日の日付を終了日のデフォルトに設定
    const today = new Date().toISOString().split('T')[0];
    const endDateInput = document.getElementById('endDate');
    if (endDateInput.value === '2024-12-31' && today < '2024-12-31') {
        endDateInput.value = today;
    }
});