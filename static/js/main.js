// static/js/main.js

document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('search-form');
    const keywordInput = document.getElementById('keyword-input');
    const loadingMessage = document.getElementById('loading-message');
    const errorMessage = document.getElementById('error-message');
    const productListContainer = document.getElementById('product-list-container');
    const noResultsMessage = document.getElementById('no-results-message');

    searchForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // 阻止表單預設提交行為 (刷新頁面)
        const keyword = keywordInput.value.trim();

        if (!keyword) {
            displayError('請輸入搜尋關鍵字！');
            return;
        }

        // 清除之前的結果和訊息
        productListContainer.innerHTML = '';
        hideElement(noResultsMessage);
        hideElement(errorMessage);
        showElement(loadingMessage);

        try {
            // 發送 API 請求到您的 Flask 後端
            const response = await fetch(`/search?keyword=${encodeURIComponent(keyword)}`);

            if (!response.ok) {
                // 如果 HTTP 狀態碼不是 2xx
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP 錯誤！狀態碼：${response.status}`);
            }

            const products = await response.json(); // 解析 JSON 響應

            hideElement(loadingMessage); // 隱藏載入訊息

            if (products && products.length > 0) {
                renderProductList(products);
            } else {
                showElement(noResultsMessage); // 顯示無結果訊息
            }

        } catch (error) {
            console.error('搜尋失敗:', error);
            hideElement(loadingMessage);
            displayError(`搜尋商品失敗：${error.message}`);
        }
    });

    // 輔助函數：顯示元素
    function showElement(element) {
        element.classList.remove('hidden');
    }

    // 輔助函數：隱藏元素
    function hideElement(element) {
        element.classList.add('hidden');
    }

    // 輔助函數：顯示錯誤訊息
    function displayError(message) {
        errorMessage.textContent = message;
        showElement(errorMessage);
    }

    // 渲染商品列表的函數
    function renderProductList(products) {
        productListContainer.innerHTML = ''; // 清空舊的結果

        products.forEach(product => {
            const productCard = document.createElement('div');
            productCard.classList.add('product-card');

            // 圖片
            const img = document.createElement('img');
            img.src = product.image || '/static/images/placeholder.png'; // 如果沒有圖片，使用預設圖片
            img.alt = product.name;
            productCard.appendChild(img);

            const cardBody = document.createElement('div');
            cardBody.classList.add('product-card-body');

            // 名稱
            const name = document.createElement('h3');
            name.textContent = product.name;
            cardBody.appendChild(name);

            // 平台價格列表
            const platformPrices = document.createElement('div');
            platformPrices.classList.add('platform-prices');

            // 預設最低價格為無限大，以便進行比較
            let minPrice = Infinity;
            let minPricePlatform = null;

            // 找出最低價格
            product.platforms.forEach(platform => {
                if (platform.is_available && platform.price < minPrice) {
                    minPrice = platform.price;
                    minPricePlatform = platform.name; // 這裡可能需要 'platform' 屬性
                }
            });


            product.platforms.forEach(platform => {
                const platformItem = document.createElement('div');
                platformItem.classList.add('platform-item');

                const platformNameSpan = document.createElement('span');
                platformNameSpan.classList.add('platform-name');
                platformNameSpan.textContent = platform.platform; // 這是我們從後端接收的平台名稱

                const priceSpan = document.createElement('span');
                priceSpan.classList.add('platform-price');
                priceSpan.textContent = `$${platform.price.toLocaleString()}`; // 格式化價格

                const urlLink = document.createElement('span');
                urlLink.classList.add('platform-url');
                const a = document.createElement('a');
                a.href = platform.url;
                a.target = '_blank'; // 在新分頁打開
                a.textContent = '前往購買';
                urlLink.appendChild(a);

                platformItem.appendChild(platformNameSpan);
                platformItem.appendChild(priceSpan);
                platformItem.appendChild(urlLink);

                // 如果是最低價格的平台，可以添加一個特別的樣式
                if (platform.is_available && platform.price === minPrice) {
                     platformItem.style.backgroundColor = '#e6ffe6'; /* 淺綠色背景 */
                     platformItem.style.fontWeight = 'bold';
                }

                platformPrices.appendChild(platformItem);
            });

            cardBody.appendChild(platformPrices);
            productCard.appendChild(cardBody);
            productListContainer.appendChild(productCard);
        });

        // 確保無結果訊息隱藏
        hideElement(noResultsMessage);
    }
});