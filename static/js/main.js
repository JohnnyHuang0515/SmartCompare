// static/js/main.js

class PriceComparison {
    constructor() {
        this.products = [];
        this.filteredProducts = [];
        this.currentSort = 'relevance';
        this.initializeElements();
        this.bindEvents();
    }

    initializeElements() {
        this.searchForm = document.getElementById('search-form');
        this.keywordInput = document.getElementById('keyword-input');
        this.searchBtn = document.getElementById('search-btn');
        this.statusMessage = document.getElementById('status-message');
        this.productGrid = document.getElementById('product-grid');
        this.noResults = document.getElementById('no-results');
        this.statsBar = document.getElementById('stats-bar');
        this.platformFilter = document.getElementById('platform-filter');
        this.priceRangeFilter = document.getElementById('price-range');
        this.sortButtons = document.querySelectorAll('.sort-btn');
        this.resultsSection = document.getElementById('results-section');
    }

    bindEvents() {
        this.searchForm.addEventListener('submit', (e) => this.handleSearch(e));
        this.platformFilter.addEventListener('change', () => this.applyFilters());
        this.priceRangeFilter.addEventListener('change', () => this.applyFilters());

        this.sortButtons.forEach(btn => {
            btn.addEventListener('click', () => this.handleSort(btn.dataset.sort));
        });
    }

    async handleSearch(event) {
        event.preventDefault();
        const keyword = this.keywordInput.value.trim();

        if (!keyword) {
            this.showMessage('請輸入搜尋關鍵字！', 'error');
            return;
        }

        this.showLoading(true);
        this.hideMessage();
        this.hideResults();

        try {
            // 發送 API 請求到您的 Flask 後端
            const response = await fetch(`/search?keyword=${encodeURIComponent(keyword)}`);

            if (!response.ok) {
                // 如果 HTTP 狀態碼不是 2xx
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP 錯誤！狀態碼：${response.status}`);
            }

            const products = await response.json();

            if (products && products.length > 0) {
                this.products = products;
                this.applyFilters();
                this.updateStats();
                this.showMessage(`找到 ${products.length} 個商品`, 'success');
                this.showResults();
            } else {
                this.showNoResults('沒有找到相關商品', '請嘗試其他關鍵字或調整篩選條件');
                this.showResults();
            }

        } catch (error) {
            console.error('搜尋失敗:', error);
            this.showMessage(`搜尋失敗：${error.message}`, 'error');
            this.showResults();
        } finally {
            this.showLoading(false);
        }
    }

    applyFilters() {
        let filtered = [...this.products];

        // 平台篩選
        const platformFilter = this.platformFilter.value;
        if (platformFilter !== 'all') {
            const platformMap = {
                'momo': 'momo',
                'pchome': 'pchome',
                'coupang': 'coupang'
            };

            const targetPlatform = platformMap[platformFilter];
            filtered = filtered.filter(product =>
                product.platforms.some(p =>
                    p.platform.toLowerCase().includes(targetPlatform) ||
                    p.platform.includes(targetPlatform)
                )
            );
        }

        // 價格區間篩選
        const priceRange = this.priceRangeFilter.value;
        if (priceRange !== 'all') {
            if (priceRange === '10000+') {
                filtered = filtered.filter(product => {
                    const minPrice = Math.min(...product.platforms.filter(p => p.is_available).map(p => p.price));
                    return minPrice >= 10000;
                });
            } else {
                const [min, max] = priceRange.split('-').map(Number);
                filtered = filtered.filter(product => {
                    const minPrice = Math.min(...product.platforms.filter(p => p.is_available).map(p => p.price));
                    return minPrice >= min && minPrice <= max;
                });
            }
        }

        this.filteredProducts = filtered;
        this.sortProducts();
        this.renderProducts();
    }

    handleSort(sortType) {
        this.currentSort = sortType;
        this.sortButtons.forEach(btn => btn.classList.remove('active'));
        document.querySelector(`[data-sort="${sortType}"]`).classList.add('active');
        this.sortProducts();
        this.renderProducts();
    }

    sortProducts() {
        switch (this.currentSort) {
            case 'price-low':
                this.filteredProducts.sort((a, b) => {
                    const aMin = Math.min(...a.platforms.filter(p => p.is_available).map(p => p.price));
                    const bMin = Math.min(...b.platforms.filter(p => p.is_available).map(p => p.price));
                    return aMin - bMin;
                });
                break;
            case 'price-high':
                this.filteredProducts.sort((a, b) => {
                    const aMin = Math.min(...a.platforms.filter(p => p.is_available).map(p => p.price));
                    const bMin = Math.min(...b.platforms.filter(p => p.is_available).map(p => p.price));
                    return bMin - aMin;
                });
                break;
            default: // relevance
                // 保持原始順序
                break;
        }
    }

    renderProducts() {
        if (this.filteredProducts.length === 0) {
            this.showNoResults('沒有符合條件的商品', '請調整篩選條件或嘗試其他關鍵字');
            return;
        }

        this.noResults.classList.add('hidden');
        this.statsBar.classList.remove('hidden');

        // 清空產品網格，但保留 no-results 元素
        const noResultsElement = this.productGrid.querySelector('#no-results');
        this.productGrid.innerHTML = '';
        if (noResultsElement) {
            this.productGrid.appendChild(noResultsElement);
        }

        this.filteredProducts.forEach(product => {
            const productCard = this.createProductCard(product);
            this.productGrid.appendChild(productCard);
        });

        // 更新統計數據
        this.updateFilteredStats();
    }

    createProductCard(product) {
        // 找出最低價格（只考慮可用的平台）
        const availablePlatforms = product.platforms.filter(p => p.is_available);
        const minPrice = availablePlatforms.length > 0 ?
            Math.min(...availablePlatforms.map(p => p.price)) : null;

        const card = document.createElement('div');
        card.className = 'product-card';

        const imageUrl = product.image || '/static/images/placeholder.png';

        card.innerHTML = `
            <img src="${imageUrl}"
                 alt="${product.name}"
                 class="product-image"
                 onerror="this.src='/static/images/placeholder.png'">
            <div class="product-content">
                <h3 class="product-title">${this.escapeHtml(product.name)}</h3>
                <div class="price-comparison">
                    ${product.platforms.map(platform => {
                        if (!platform.is_available) {
                            return `
                                <div class="platform-item" style="opacity: 0.6;">
                                    <span class="platform-name">${this.escapeHtml(platform.platform)}</span>
                                    <span class="platform-price" style="color: #999;">缺貨</span>
                                    <span class="platform-link" style="background: #ccc; cursor: not-allowed;">無法購買</span>
                                </div>
                            `;
                        }

                        const isBestPrice = minPrice !== null && platform.price === minPrice;
                        return `
                            <div class="platform-item ${isBestPrice ? 'best-price' : ''}">
                                <span class="platform-name">${this.escapeHtml(platform.platform)}</span>
                                <span class="platform-price">$${platform.price.toLocaleString()}</span>
                                <a href="${platform.url}" target="_blank" class="platform-link">
                                    ${isBestPrice ? '🏆 最低價' : '前往購買'}
                                </a>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;

        return card;
    }

    updateStats() {
        if (this.products.length === 0) return;

        // 總商品數
        document.getElementById('total-products').textContent = this.products.length;

        // 計算平均節省金額
        this.calculateAndDisplayStats(this.products);
    }

    updateFilteredStats() {
        if (this.filteredProducts.length === 0) return;

        // 更新顯示的商品數
        document.getElementById('total-products').textContent = this.filteredProducts.length;

        // 計算篩選後的統計
        this.calculateAndDisplayStats(this.filteredProducts);
    }

    calculateAndDisplayStats(productList) {
        let totalSavings = 0;
        const platformStats = {};
        let validProducts = 0;

        productList.forEach(product => {
            const availablePlatforms = product.platforms.filter(p => p.is_available);
            if (availablePlatforms.length < 2) return; // 至少要有兩個平台才能比較

            const prices = availablePlatforms.map(p => p.price);
            const minPrice = Math.min(...prices);
            const maxPrice = Math.max(...prices);

            totalSavings += (maxPrice - minPrice);
            validProducts++;

            // 統計最優平台
            const bestPlatform = availablePlatforms.find(p => p.price === minPrice);
            if (bestPlatform) {
                const platformName = bestPlatform.platform.replace(/購物網|網/g, ''); // 簡化平台名稱
                platformStats[platformName] = (platformStats[platformName] || 0) + 1;
            }
        });

        // 平均節省金額
        const avgSavings = validProducts > 0 ? Math.round(totalSavings / validProducts) : 0;
        document.getElementById('avg-savings').textContent = `$${avgSavings.toLocaleString()}`;

        // 最優平台
        const bestPlatformName = Object.keys(platformStats).length > 0
            ? Object.keys(platformStats).reduce((a, b) => platformStats[a] > platformStats[b] ? a : b)
            : '-';
        document.getElementById('best-platform').textContent = bestPlatformName;
    }

    // 輔助方法
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showLoading(show) {
        const btnText = this.searchBtn.querySelector('.btn-text');
        const spinner = this.searchBtn.querySelector('.loading-spinner');

        if (show) {
            btnText.textContent = '搜尋中...';
            spinner.classList.remove('hidden');
            this.searchBtn.disabled = true;
        } else {
            btnText.textContent = '搜尋比價';
            spinner.classList.add('hidden');
            this.searchBtn.disabled = false;
        }
    }

    showMessage(message, type) {
        this.statusMessage.textContent = message;
        this.statusMessage.className = `status-message ${type}`;
        this.statusMessage.classList.remove('hidden');

        // 自動隱藏成功訊息
        if (type === 'success') {
            setTimeout(() => {
                this.hideMessage();
            }, 3000);
        }
    }

    hideMessage() {
        this.statusMessage.classList.add('hidden');
    }

    showResults() {
        this.resultsSection.classList.remove('hidden');
    }

    hideResults() {
        this.resultsSection.classList.add('hidden');
    }

    showNoResults(title, hint) {
        this.noResults.classList.remove('hidden');
        this.statsBar.classList.add('hidden');

        // 更新 no-results 內容
        const noResultsText = this.noResults.querySelector('.no-results-text');
        const noResultsHint = this.noResults.querySelector('.no-results-hint');

        if (noResultsText) noResultsText.textContent = title;
        if (noResultsHint) noResultsHint.textContent = hint;

        // 清空產品網格
        Array.from(this.productGrid.children).forEach(child => {
            if (child.id !== 'no-results') {
                child.remove();
            }
        });
    }
}

// 當頁面載入完成時初始化價格比較系統
document.addEventListener('DOMContentLoaded', () => {
    new PriceComparison();
});