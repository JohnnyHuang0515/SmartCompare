class PriceComparison {
    constructor() {
        this.products = [];
        this.filteredProducts = [];
        this.currentSort = 'relevance';
        this.isSearching = false;
        this.animationQueue = [];
        this.searchHistory = JSON.parse(localStorage.getItem('searchHistory') || '[]');
        
        this.initializeElements();
        this.bindEvents();
        this.initializeAnimations();
        this.showWelcomeAnimation();
    }

    initializeElements() {
        this.searchForm = document.getElementById('search-form');
        this.keywordInput = document.getElementById('keyword-input');
        this.searchBtn = document.getElementById('search-btn');
        this.spinner = this.searchBtn.querySelector('.loading-spinner');
        this.btnText = this.searchBtn.querySelector('.btn-text');
        this.statusMessage = document.getElementById('status-message');
        this.productGrid = document.getElementById('product-grid');
        this.noResults = document.getElementById('no-results');
        this.statsBar = document.getElementById('stats-bar');
        this.platformFilter = document.getElementById('platform-filter');
        this.priceRangeFilter = document.getElementById('price-range');
        this.sortButtons = document.querySelectorAll('.sort-btn');
        this.resultsSection = document.getElementById('results-section');

        // Stats elements
        this.totalProductsEl = document.getElementById('total-products');
        this.avgSavingsEl = document.getElementById('avg-savings');
        this.bestPlatformEl = document.getElementById('best-platform');
    }

    bindEvents() {
        // 搜尋表單事件
        this.searchForm.addEventListener('submit', (e) => this.handleSearch(e));
        
        // 輸入框事件 - 增加即時搜尋建議
        this.keywordInput.addEventListener('input', this.debounce((e) => {
            this.handleInputChange(e.target.value);
        }, 300));
        
        this.keywordInput.addEventListener('focus', () => this.handleInputFocus());
        this.keywordInput.addEventListener('blur', () => this.handleInputBlur());
        
        // 篩選和排序事件
        this.platformFilter.addEventListener('change', () => {
            this.addToAnimationQueue(() => this.applyFiltersAndSort());
            this.triggerFilterAnimation(this.platformFilter);
        });
        
        this.priceRangeFilter.addEventListener('input', () => {
            this.addToAnimationQueue(() => this.applyFiltersAndSort());
            this.triggerFilterAnimation(this.priceRangeFilter);
        });
        
        this.sortButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                this.handleSort(btn.dataset.sort);
                this.triggerButtonPulse(btn);
            });
        });

        // 鍵盤快捷鍵
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));

        // 滾動動畫
        window.addEventListener('scroll', this.throttle(() => this.handleScrollAnimations(), 16));

        // 視窗大小變化
        window.addEventListener('resize', this.debounce(() => this.handleResize(), 250));
    }

    initializeAnimations() {
        // 初始化觀察器用於滾動動畫
        this.intersectionObserver = new IntersectionObserver(
            (entries) => this.handleIntersection(entries),
            { threshold: 0.1, rootMargin: '50px' }
        );

        // 初始化動畫隊列處理器
        this.processAnimationQueue();
    }

    showWelcomeAnimation() {
        const noResultsText = this.noResults.querySelector('.no-results-text');
        const noResultsHint = this.noResults.querySelector('.no-results-hint');

        if (noResultsText) {
            noResultsText.textContent = '🎯 準備好開始比價了嗎？';
            this.typeWriterEffect(noResultsText, '🎯 準備好開始比價了嗎？', 50);
        }

        if (noResultsHint) {
            noResultsHint.textContent = '輸入商品名稱，我們幫您找到最棒的價格！✨';
            setTimeout(() => {
                this.typeWriterEffect(noResultsHint, '輸入商品名稱，我們幫您找到最棒的價格！✨', 30);
            }, 1000);
        }

        this.showNoResults('', '');
    }

    // 防抖函數
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // 節流函數
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        }
    }

    // 打字機效果
    typeWriterEffect(element, text, speed = 50) {
        element.textContent = '';
        let i = 0;
        const timer = setInterval(() => {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
            } else {
                clearInterval(timer);
            }
        }, speed);
    }

    // 輸入框變化處理
    handleInputChange(value) {
        if (value.length > 2) {
            this.showSearchSuggestions(value);
        } else {
            this.hideSearchSuggestions();
        }

        // 動態調整輸入框樣式
        if (value.length > 0) {
            this.keywordInput.classList.add('has-content');
        } else {
            this.keywordInput.classList.remove('has-content');
        }
    }

    // 輸入框焦點處理
    handleInputFocus() {
        this.keywordInput.parentElement.classList.add('focused');
        this.triggerRippleEffect(this.keywordInput);
    }

    handleInputBlur() {
        this.keywordInput.parentElement.classList.remove('focused');
        setTimeout(() => this.hideSearchSuggestions(), 200);
    }

    // 鍵盤快捷鍵
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + K 快速搜尋
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            this.keywordInput.focus();
            this.keywordInput.select();
        }

        // Escape 清空搜尋
        if (e.key === 'Escape') {
            this.keywordInput.value = '';
            this.keywordInput.blur();
            this.hideSearchSuggestions();
        }
    }

    // 搜尋處理 - 增強版
    async handleSearch(e) {
        e.preventDefault();

        if (this.isSearching) return;

        const keyword = this.keywordInput.value.trim();
        if (!keyword) {
            this.showMessage('💡 請輸入您想搜尋的商品名稱', 'warning');
            this.shakeAnimation(this.keywordInput);
            return;
        }

        this.isSearching = true;
        this.addToSearchHistory(keyword);
        this.setLoadingState(true);
        this.hideMessage();
        this.prepareForNewSearch();

        try {
            // 添加搜尋開始動畫
            this.triggerSearchStartAnimation();

            const response = await fetch('/search?keyword=' + encodeURIComponent(keyword));
            const data = await response.json();

            // 模擬更真實的載入時間（可選）
            await this.simulateProcessingTime(500);

            if (data.errors && data.errors.length > 0) {
                this.showMessage(`⚠️ 搜尋完成，但部分平台暫時無法存取：${data.errors.join(', ')}`, 'warning');
            }

            if (data.grouped_products && data.grouped_products.length > 0) {
                this.products = data.grouped_products;
                await this.animatedResultsTransition();
                this.applyFiltersAndSort();
                this.updateStats(data.summary);
                this.showResults();
                this.hideNoResults();
                this.showMessage(`🎉 太棒了！找到 ${data.grouped_products.length} 個相關商品`, 'success');
                this.triggerSuccessAnimation();
            } else {
                this.handleNoResultsFound();
            }

        } catch (error) {
            console.error('搜尋失敗:', error);
            this.handleSearchError();
        } finally {
            this.setLoadingState(false);
            this.isSearching = false;
        }
    }

    // 準備新搜尋
    prepareForNewSearch() {
        this.productGrid.style.opacity = '0';
        this.statsBar.classList.add('hidden');
        this.hideSearchSuggestions();

        // 清空產品卡片動畫
        const existingCards = this.productGrid.querySelectorAll('.product-card');
        existingCards.forEach((card, index) => {
            setTimeout(() => {
                card.style.transform = 'translateY(-20px)';
                card.style.opacity = '0';
            }, index * 50);
        });

        setTimeout(() => {
            this.productGrid.innerHTML = '';
        }, existingCards.length * 50 + 200);
    }

    // 搜尋開始動畫
    triggerSearchStartAnimation() {
        const searchCard = document.querySelector('.search-card');
        searchCard.style.transform = 'scale(0.98)';
        setTimeout(() => {
            searchCard.style.transform = 'scale(1)';
        }, 200);
    }

    // 模擬處理時間
    simulateProcessingTime(duration) {
        return new Promise(resolve => setTimeout(resolve, duration));
    }

    // 動畫化結果轉換
    async animatedResultsTransition() {
        return new Promise(resolve => {
            this.productGrid.style.opacity = '1';
            this.productGrid.style.transform = 'translateY(20px)';

            setTimeout(() => {
                this.productGrid.style.transform = 'translateY(0)';
                resolve();
            }, 100);
        });
    }

    // 處理無結果情況
    handleNoResultsFound() {
        this.products = [];
        this.filteredProducts = [];
        this.showNoResults('🔍 沒有找到相關商品', '試試其他關鍵字，或檢查拼寫是否正確');
        this.updateStats({ total_products: 0, avg_savings: 0, best_platform: 'N/A' });
        this.hideResults();
        this.showMessage('😕 很抱歉，沒有找到相關商品', 'warning');
    }

    // 處理搜尋錯誤
    handleSearchError() {
        this.showMessage('❌ 搜尋時發生錯誤，請稍後再試', 'error');
        this.showNoResults('⚠️ 搜尋失敗', '請檢查網路連線，或稍後再試');
        this.updateStats({ total_products: 0, avg_savings: 0, best_platform: 'N/A' });
        this.hideResults();
    }

    // 成功動畫
    triggerSuccessAnimation() {
        const searchBtn = this.searchBtn;
        searchBtn.style.transform = 'scale(1.05)';
        searchBtn.style.background = 'linear-gradient(135deg, #10b981, #059669)';

        setTimeout(() => {
            searchBtn.style.transform = '';
            searchBtn.style.background = '';
        }, 300);
    }

    // 應用篩選和排序 - 增強版
    applyFiltersAndSort() {
        let tempProducts = [...this.products];

        // 平台篩選
        const selectedPlatform = this.platformFilter.value;
        if (selectedPlatform && selectedPlatform !== 'all') {
            tempProducts = tempProducts.filter(productGroup =>
                productGroup.prices.some(p => p.platform === selectedPlatform)
            );
        }

        // 價格篩選
        const priceRange = this.priceRangeFilter.value;
        tempProducts = this.filterByPriceRange(tempProducts, priceRange);

        // 排序
        this.sortProducts(tempProducts);

        this.filteredProducts = tempProducts;
        this.renderProductsWithAnimation();
    }

    // 價格區間篩選
    filterByPriceRange(products, priceRange) {
        const ranges = {
            '0-100': [0, 100],
            '101-500': [101, 500],
            '501-1000': [501, 1000],
            '1001-above': [1001, Infinity]
        };

        if (!ranges[priceRange]) return products;

        const [min, max] = ranges[priceRange];
        return products.filter(product =>
            product.lowest_price >= min && product.lowest_price <= max
        );
    }

    // 產品排序
    sortProducts(products) {
        const sortFunctions = {
            'price-low': (a, b) => a.lowest_price - b.lowest_price,
            'price-high': (a, b) => b.lowest_price - a.lowest_price,
            'relevance': () => 0 // 保持原順序
        };

        const sortFn = sortFunctions[this.currentSort];
        if (sortFn) products.sort(sortFn);
    }

    // 排序處理
    handleSort(sortType) {
        this.currentSort = sortType;
        this.updateSortButtons(sortType);
        this.applyFiltersAndSort();
        this.triggerSortAnimation();
    }

    // 更新排序按鈕狀態
    updateSortButtons(activeSort) {
        this.sortButtons.forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.sort === activeSort) {
                btn.classList.add('active');
            }
        });
    }

    // 排序動畫
    triggerSortAnimation() {
        const cards = this.productGrid.querySelectorAll('.product-card');
        cards.forEach((card, index) => {
            card.style.transform = 'scale(0.9) rotateY(10deg)';
            card.style.opacity = '0.7';

            setTimeout(() => {
                card.style.transform = '';
                card.style.opacity = '';
            }, index * 50 + 200);
        });
    }

    // 帶動畫的產品渲染
    renderProductsWithAnimation() {
        this.productGrid.innerHTML = '';

        if (this.filteredProducts.length === 0) {
            this.showNoResults('🔍 沒有符合條件的商品', '試著調整篩選條件看看');
            return;
        }

        this.hideNoResults();

        this.filteredProducts.forEach((product, index) => {
            setTimeout(() => {
                const productCard = this.createProductCard(product);
                this.productGrid.appendChild(productCard);

                // 設置初始動畫狀態
                productCard.style.opacity = '0';
                productCard.style.transform = 'translateY(30px) scale(0.9)';

                // 觸發進入動畫
                requestAnimationFrame(() => {
                    productCard.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
                    productCard.style.opacity = '1';
                    productCard.style.transform = 'translateY(0) scale(1)';
                });

                // 添加到觀察器
                this.intersectionObserver.observe(productCard);

            }, index * 100); // 錯開動畫時間
        });
    }

    // 創建產品卡片
    createProductCard(product) {
        const productCard = document.createElement('div');
        productCard.classList.add('product-card');
        productCard.setAttribute('data-aos', 'fade-up');

        // 添加懸停效果事件
        this.addCardHoverEffects(productCard);

        // 圖片容器
        const imageContainer = this.createImageContainer(product);
        productCard.appendChild(imageContainer);

        // 內容容器
        const contentContainer = this.createContentContainer(product);
        productCard.appendChild(contentContainer);

        return productCard;
    }

    // 創建圖片容器
    createImageContainer(product) {
        const container = document.createElement('div');
        container.classList.add('product-image-container');

        const img = document.createElement('img');
        img.src = product.image;
        img.alt = product.name;
        img.loading = 'lazy'; // 懶載入

        // 圖片載入處理
        img.addEventListener('load', () => {
            img.classList.add('loaded');
        });

        img.addEventListener('error', () => {
            img.src = '/static/images/placeholder.png';
            img.classList.add('error');
        });

        container.appendChild(img);
        return container;
    }

    // 創建內容容器
    createContentContainer(product) {
        const container = document.createElement('div');
        container.classList.add('product-content');

        // 產品名稱
        const nameEl = document.createElement('h3');
        nameEl.classList.add('product-name');
        nameEl.textContent = product.name;
        nameEl.title = product.name; // 工具提示
        container.appendChild(nameEl);

        // 價格列表
        const priceList = this.createPriceList(product.prices);
        container.appendChild(priceList);

        return container;
    }

    // 創建價格列表
    createPriceList(prices) {
        const list = document.createElement('ul');
        list.classList.add('price-list');

        const sortedPrices = [...prices].sort((a, b) => a.price - b.price);

        sortedPrices.forEach((priceEntry, index) => {
            const item = document.createElement('li');
            item.classList.add('price-item');

            if (!priceEntry.is_available) {
                item.classList.add('unavailable');
            }

            if (index === 0) { // 最低價格
                item.classList.add('best-price');
            }

            item.innerHTML = `
              <div class="price-block" style="display: flex; justify-content: space-between; align-items: center;">
                <div class="price-info">
                  <span class="platform-name">${this.getPlatformIcon(priceEntry.platform)} ${priceEntry.platform}</span>
                  <span class="product-price ${index === 0 ? 'lowest' : ''}">NT$ ${priceEntry.price.toLocaleString()}</span>
                </div>
                <a href="${priceEntry.url}"
                   target="_blank"
                   class="buy-link ${!priceEntry.is_available ? 'disabled' : ''}"
                   ${!priceEntry.is_available ? 'tabindex="-1"' : ''}>
                    ${priceEntry.is_available ? '🛒 購買' : '❌售罄'}
                </a>
              </div>
            `;

            // 添加購買連結點擊動畫
            const buyLink = item.querySelector('.buy-link');
            if (priceEntry.is_available) {
                buyLink.addEventListener('click', (e) => {
                    this.triggerBuyClickAnimation(buyLink);
                });
            }

            list.appendChild(item);
        });

        return list;
    }

    // 獲取平台圖標
    getPlatformIcon(platform) {
        const icons = {
            'momo': '🛍️',
            'pchome': '🏪',
            'coupang': '📦',
            'default': '🛒'
        };
        return icons[platform.toLowerCase()] || icons.default;
    }

    // 卡片懸停效果
    addCardHoverEffects(card) {
        card.addEventListener('mouseenter', () => {
            this.triggerCardHoverIn(card);
        });

        card.addEventListener('mouseleave', () => {
            this.triggerCardHoverOut(card);
        });

        // 觸摸設備支持
        card.addEventListener('touchstart', () => {
            this.triggerCardHoverIn(card);
        });
    }

    triggerCardHoverIn(card) {
        card.style.transform = 'translateY(-8px) scale(1.02)';
        card.style.boxShadow = '0 20px 60px rgba(0, 0, 0, 0.25)';

        const img = card.querySelector('img');
        if (img) {
            img.style.transform = 'scale(1.1)';
        }
    }

    triggerCardHoverOut(card) {
        card.style.transform = '';
        card.style.boxShadow = '';

        const img = card.querySelector('img');
        if (img) {
            img.style.transform = '';
        }
    }

    // 購買按鈕點擊動畫
    triggerBuyClickAnimation(button) {
        button.style.transform = 'scale(0.95)';
        button.style.backgroundColor = '#10b981';

        setTimeout(() => {
            button.style.transform = 'scale(1.1)';
            setTimeout(() => {
                button.style.transform = '';
                button.style.backgroundColor = '';
            }, 150);
        }, 100);
    }

    // 統計更新 - 增強版
    updateStats(summary) {
        if (summary && summary.total_products > 0) {
            this.animateStatUpdate(this.totalProductsEl, 0, summary.total_products);
            this.animateStatUpdate(this.avgSavingsEl, 0, summary.avg_savings, 'currency');
            this.bestPlatformEl.textContent = summary.best_platform || 'N/A';

            // 顯示統計條帶動畫
            this.statsBar.classList.remove('hidden');
            this.statsBar.style.opacity = '0';
            this.statsBar.style.transform = 'translateY(-20px)';

            setTimeout(() => {
                this.statsBar.style.transition = 'all 0.5s ease';
                this.statsBar.style.opacity = '1';
                this.statsBar.style.transform = 'translateY(0)';
            }, 200);
        } else {
            this.resetStats();
        }
    }

    // 統計數字動畫
    animateStatUpdate(element, from, to, type = 'number') {
        const duration = 1000;
        const start = Date.now();
        const diff = to - from;

        const updateNumber = () => {
            const elapsed = Date.now() - start;
            const progress = Math.min(elapsed / duration, 1);
            const easeProgress = this.easeOutCubic(progress);
            const current = from + (diff * easeProgress);

            if (type === 'currency') {
                element.textContent = `NT$ ${Math.round(current).toLocaleString()}`;
            } else {
                element.textContent = Math.round(current).toLocaleString();
            }

            if (progress < 1) {
                requestAnimationFrame(updateNumber);
            }
        };

        updateNumber();
    }

    // 緩動函數
    easeOutCubic(t) {
        return 1 - Math.pow(1 - t, 3);
    }

    // 重置統計
    resetStats() {
        this.totalProductsEl.textContent = '0';
        this.avgSavingsEl.textContent = 'NT$ 0';
        this.bestPlatformEl.textContent = 'N/A';
        this.statsBar.classList.add('hidden');
    }

    // 載入狀態 - 增強版
    setLoadingState(isLoading) {
        if (isLoading) {
            this.btnText.innerHTML = '<span class="loading-text">🔍 搜尋中</span>';
            this.spinner.classList.remove('hidden');
            this.searchBtn.disabled = true;
            this.searchBtn.classList.add('loading');

            // 添加載入點點動畫
            this.startLoadingDotAnimation();
        } else {
            this.btnText.innerHTML = '🔍 搜尋比價';
            this.spinner.classList.add('hidden');
            this.searchBtn.disabled = false;
            this.searchBtn.classList.remove('loading');

            this.stopLoadingDotAnimation();
        }
    }

    // 載入點點動畫
    startLoadingDotAnimation() {
        let dots = '';
        this.loadingInterval = setInterval(() => {
            dots = dots.length >= 3 ? '' : dots + '.';
            const loadingText = this.btnText.querySelector('.loading-text');
            if (loadingText) {
                loadingText.textContent = `🔍 搜尋中${dots}`;
            }
        }, 500);
    }

    stopLoadingDotAnimation() {
        if (this.loadingInterval) {
            clearInterval(this.loadingInterval);
            this.loadingInterval = null;
        }
    }

    // 訊息顯示 - 增強版
    showMessage(message, type) {
        this.statusMessage.innerHTML = `
            <div class="message-content">
                <span class="message-icon">${this.getMessageIcon(type)}</span>
                <span class="message-text">${message}</span>
            </div>
        `;
        this.statusMessage.className = `status-message ${type}`;
        this.statusMessage.classList.remove('hidden');

        // 進入動畫
        this.statusMessage.style.transform = 'translateY(-20px) scale(0.9)';
        this.statusMessage.style.opacity = '0';

        requestAnimationFrame(() => {
            this.statusMessage.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
            this.statusMessage.style.transform = 'translateY(0) scale(1)';
            this.statusMessage.style.opacity = '1';
        });

        // 自動隱藏
        if (type === 'success' || type === 'warning') {
            setTimeout(() => this.hideMessage(), 4000);
        }
    }

    // 獲取訊息圖標
    getMessageIcon(type) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        return icons[type] || icons.info;
    }

    hideMessage() {
        if (!this.statusMessage.classList.contains('hidden')) {
            this.statusMessage.style.transform = 'translateY(-20px) scale(0.9)';
            this.statusMessage.style.opacity = '0';

            setTimeout(() => {
                this.statusMessage.classList.add('hidden');
                this.statusMessage.style.transform = '';
                this.statusMessage.style.opacity = '';
            }, 300);
        }
    }

    // 搖動動畫
    shakeAnimation(element) {
        element.style.animation = 'shake 0.5s ease-in-out';
        setTimeout(() => {
            element.style.animation = '';
        }, 500);
    }

    // 漣漪效果
    triggerRippleEffect(element) {
        const ripple = document.createElement('div');
        ripple.classList.add('ripple-effect');
        element.parentElement.appendChild(ripple);

        setTimeout(() => ripple.remove(), 600);
    }

    // 按鈕脈衝效果
    triggerButtonPulse(button) {
        button.style.transform = 'scale(1.1)';
        setTimeout(() => {
            button.style.transform = '';
        }, 200);
    }

    // 篩選器動畫
    triggerFilterAnimation(filter) {
        filter.style.transform = 'scale(1.05)';
        filter.style.boxShadow = '0 0 20px rgba(102, 126, 234, 0.3)';

        setTimeout(() => {
            filter.style.transform = '';
            filter.style.boxShadow = '';
        }, 200);
    }

    // 動畫隊列管理
    addToAnimationQueue(animation) {
        this.animationQueue.push(animation);
    }

    processAnimationQueue() {
        setInterval(() => {
            if (this.animationQueue.length > 0) {
                const animation = this.animationQueue.shift();
                animation();
            }
        }, 100);
    }

    // 交集觀察器處理
    handleIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('in-view');
                this.intersectionObserver.unobserve(entry.target);
            }
        });
    }

    // 滾動動畫處理
    handleScrollAnimations() {
        const scrollTop = window.pageYOffset;
        const cards = this.productGrid.querySelectorAll('.product-card');

        cards.forEach((card, index) => {
            const cardTop = card.offsetTop;
            const cardHeight = card.offsetHeight;
            const windowHeight = window.innerHeight;

            // 視差效果
            if (cardTop < scrollTop + windowHeight && cardTop + cardHeight > scrollTop) {
                const parallaxValue = (scrollTop - cardTop) * 0.1;
                card.style.transform = `translateY(${parallaxValue}px)`;
            }
        });

        // 更新標題欄透明度
        const header = document.querySelector('.search-card');
        if (header) {
            const opacity = Math.max(0.8, 1 - scrollTop / 200);
            header.style.background = `rgba(157, 143, 214, ${opacity})`;
        }
    }

    // 視窗大小變化處理
    handleResize() {
        // 重新計算卡片佈局
        this.recalculateLayout();

        // 調整搜尋建議位置
        this.adjustSuggestionsPosition();
    }

    // 重新計算佈局
    recalculateLayout() {
        const cards = this.productGrid.querySelectorAll('.product-card');
        cards.forEach(card => {
            card.style.transform = '';
            card.style.transition = 'all 0.3s ease';
        });
    }

    // 搜尋建議功能
    showSearchSuggestions(query) {
        const suggestions = this.generateSuggestions(query);
        if (suggestions.length === 0) return;

        let suggestionsContainer = document.getElementById('search-suggestions');
        if (!suggestionsContainer) {
            suggestionsContainer = this.createSuggestionsContainer();
        }

        suggestionsContainer.innerHTML = '';
        suggestions.forEach(suggestion => {
            const item = document.createElement('div');
            item.classList.add('suggestion-item');
            item.innerHTML = `
                <span class="suggestion-icon">🔍</span>
                <span class="suggestion-text">${suggestion}</span>
            `;

            item.addEventListener('click', () => {
                this.keywordInput.value = suggestion;
                this.hideSearchSuggestions();
                this.handleSearch({ preventDefault: () => {} });
            });

            suggestionsContainer.appendChild(item);
        });

        this.showSuggestionsWithAnimation(suggestionsContainer);
    }

    // 創建建議容器
    createSuggestionsContainer() {
        const container = document.createElement('div');
        container.id = 'search-suggestions';
        container.classList.add('search-suggestions');
        this.keywordInput.parentElement.appendChild(container);
        return container;
    }

    // 生成搜尋建議
    generateSuggestions(query) {
        const commonSuggestions = [
            'iPhone 15', 'MacBook Air', 'iPad Pro', 'AirPods Pro',
            'Samsung Galaxy', 'Nintendo Switch', 'PlayStation 5',
            'Apple Watch', 'Surface Pro', '咖啡機', '空氣清淨機',
            '掃地機器人', '電動牙刷', '筆記型電腦', '行動電源'
        ];

        const historySuggestions = this.searchHistory.filter(item =>
            item.toLowerCase().includes(query.toLowerCase())
        );

        const matchingSuggestions = commonSuggestions.filter(item =>
            item.toLowerCase().includes(query.toLowerCase())
        );

        return [...new Set([...historySuggestions, ...matchingSuggestions])].slice(0, 5);
    }

    // 顯示建議動畫
    showSuggestionsWithAnimation(container) {
        container.style.opacity = '0';
        container.style.transform = 'translateY(-10px)';
        container.classList.remove('hidden');

        requestAnimationFrame(() => {
            container.style.transition = 'all 0.2s ease';
            container.style.opacity = '1';
            container.style.transform = 'translateY(0)';
        });
    }

    // 隱藏搜尋建議
    hideSearchSuggestions() {
        const suggestionsContainer = document.getElementById('search-suggestions');
        if (suggestionsContainer && !suggestionsContainer.classList.contains('hidden')) {
            suggestionsContainer.style.opacity = '0';
            suggestionsContainer.style.transform = 'translateY(-10px)';

            setTimeout(() => {
                suggestionsContainer.classList.add('hidden');
            }, 200);
        }
    }

    // 調整建議位置
    adjustSuggestionsPosition() {
        const suggestionsContainer = document.getElementById('search-suggestions');
        if (suggestionsContainer) {
            const inputRect = this.keywordInput.getBoundingClientRect();
            suggestionsContainer.style.top = `${inputRect.bottom + 5}px`;
            suggestionsContainer.style.left = `${inputRect.left}px`;
            suggestionsContainer.style.width = `${inputRect.width}px`;
        }
    }

    // 搜尋歷史管理
    addToSearchHistory(keyword) {
        if (!keyword || this.searchHistory.includes(keyword)) return;

        this.searchHistory.unshift(keyword);
        this.searchHistory = this.searchHistory.slice(0, 10); // 保留最近10次

        try {
            localStorage.setItem('searchHistory', JSON.stringify(this.searchHistory));
        } catch (e) {
            console.warn('無法儲存搜尋歷史:', e);
        }
    }

    // 顯示/隱藏結果區域
    showResults() {
        this.resultsSection.classList.remove('hidden');
        this.resultsSection.style.opacity = '0';

        setTimeout(() => {
            this.resultsSection.style.transition = 'opacity 0.5s ease';
            this.resultsSection.style.opacity = '1';
        }, 100);
    }

    hideResults() {
        this.resultsSection.style.opacity = '0';
        setTimeout(() => {
            this.resultsSection.classList.add('hidden');
        }, 300);
    }

    // 顯示/隱藏無結果訊息
    showNoResults(title, message) {
        const titleEl = this.noResults.querySelector('.no-results-text');
        const messageEl = this.noResults.querySelector('.no-results-hint');

        if (title && titleEl) titleEl.textContent = title;
        if (message && messageEl) messageEl.textContent = message;

        this.noResults.classList.remove('hidden');
        this.noResults.style.opacity = '0';

        setTimeout(() => {
            this.noResults.style.transition = 'opacity 0.3s ease';
            this.noResults.style.opacity = '1';
        }, 100);
    }

    hideNoResults() {
        this.noResults.style.opacity = '0';
        setTimeout(() => {
            this.noResults.classList.add('hidden');
        }, 300);
    }

    // 清理資源
    destroy() {
        // 清理事件監聽器
        if (this.intersectionObserver) {
            this.intersectionObserver.disconnect();
        }

        // 清理動畫定時器
        if (this.loadingInterval) {
            clearInterval(this.loadingInterval);
        }

        // 清理動畫隊列
        this.animationQueue = [];

        console.log('PriceComparison 已清理');
    }
}

// 初始化應用程式
document.addEventListener('DOMContentLoaded', () => {
    const priceComparison = new PriceComparison();

    // 全域錯誤處理
    window.addEventListener('error', (e) => {
        console.error('全域錯誤:', e.error);
        priceComparison.showMessage('❌ 發生未預期的錯誤', 'error');
    });

    // 全域未處理的 Promise 拒絕
    window.addEventListener('unhandledrejection', (e) => {
        console.error('未處理的 Promise 拒絕:', e.reason);
        priceComparison.showMessage('❌ 網路請求失敗', 'error');
        e.preventDefault();
    });
});

// CSS 動畫定義（如果需要額外的 CSS 動畫）
const additionalStyles = `
@keyframes shake {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-5px); }
    75% { transform: translateX(5px); }
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.ripple-effect {
    position: absolute;
    border-radius: 50%;
    background: rgba(102, 126, 234, 0.3);
    transform: scale(0);
    animation: ripple 0.6s linear;
    pointer-events: none;
}

@keyframes ripple {
    to {
        transform: scale(4);
        opacity: 0;
    }
}

.product-card.in-view {
    animation: fadeInUp 0.6s ease forwards;
}

.search-suggestions {
    position: absolute;
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
    z-index: 1000;
    max-height: 300px;
    overflow-y: auto;
}

.suggestion-item {
    padding: 12px 16px;
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    transition: background-color 0.2s ease;
}

.suggestion-item:hover {
    background-color: #f3f4f6;
}

.suggestion-item:first-child {
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
}

.suggestion-item:last-child {
    border-bottom-left-radius: 12px;
    border-bottom-right-radius: 12px;
}

.suggestion-icon {
    color: #6b7280;
}

.suggestion-text {
    color: #374151;
    font-size: 14px;
}
`;

// 動態添加額外樣式
if (!document.getElementById('additional-price-comparison-styles')) {
    const styleSheet = document.createElement('style');
    styleSheet.id = 'additional-price-comparison-styles';
    styleSheet.textContent = additionalStyles;
    document.head.appendChild(styleSheet);
}