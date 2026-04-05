// 进销存管理系统主JavaScript文件

// ============================================
// 通用搜索选择器类 - 支持模糊搜索和键盘导航
// ============================================
class EntitySearcher {
    constructor(options) {
        this.items = options.items || [];
        this.onSelect = options.onSelect || function() {};
        this.containerClass = options.containerClass || 'entity-search-container';
        this.fieldCode = options.fieldCode || 'code';
        this.fieldName = options.fieldName || 'name';
        this.placeholder = options.placeholder || '输入名称或编码搜索...';
        this.selectedId = options.selectedId || null;
        this.hiddenName = options.hiddenName || 'id[]';
        this.itemClass = options.itemClass || 'entity-search-item';
        this.dropdownClass = options.dropdownClass || 'entity-dropdown';
        
        this.init();
    }
    
    init() {
        // 创建容器
        this.container = $(`
            <div class="${this.containerClass}" style="position: relative;">
                <input type="text" class="form-control entity-search-input" 
                       placeholder="${this.placeholder}" autocomplete="off"
                       value="${this.getSelectedText()}">
                <input type="hidden" class="entity-id-input" name="${this.hiddenName}" value="${this.selectedId || ''}">
                <div class="${this.dropdownClass}" style="
                    position: absolute;
                    top: 100%;
                    left: 0;
                    right: 0;
                    max-height: 250px;
                    overflow-y: auto;
                    background: white;
                    border: 1px solid #dee2e6;
                    border-top: none;
                    border-radius: 0 0 0.25rem 0.25rem;
                    z-index: 1000;
                    display: none;
                    box-shadow: 0 0.5rem 1rem rgba(0,0,0,0.15);
                "></div>
            </div>
        `);
        
        this.input = this.container.find('.entity-search-input');
        this.dropdown = this.container.find('.' + this.dropdownClass);
        this.hiddenInput = this.container.find('.entity-id-input');
        this.selectedIndex = -1;
        this.currentResults = [];
        
        this.bindEvents();
    }
    
    getSelectedText() {
        if (this.selectedId) {
            const item = this.items.find(p => String(p.id) === String(this.selectedId));
            if (item) {
                return `${item[this.fieldCode]} - ${item[this.fieldName]}`;
            }
        }
        return '';
    }
    
    bindEvents() {
        const self = this;
        
        // 输入事件 - 实时搜索
        this.input.on('input', function() {
            const keyword = $(this).val().trim();
            if (keyword.length > 0) {
                self.search(keyword);
            } else {
                self.hideDropdown();
            }
        });
        
        // 聚焦事件
        this.input.on('focus', function() {
            const keyword = $(this).val().trim();
            if (keyword.length > 0) {
                self.search(keyword);
            }
        });
        
        // 键盘事件
        this.input.on('keydown', function(e) {
            if (!self.dropdown.is(':visible')) {
                if (e.key === 'ArrowDown' || e.key === 'Enter') {
                    const keyword = $(this).val().trim();
                    if (keyword.length > 0) {
                        self.search(keyword);
                        e.preventDefault();
                    }
                }
                return;
            }
            
            switch(e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    self.selectNext();
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    self.selectPrev();
                    break;
                case 'Enter':
                    e.preventDefault();
                    self.confirmSelection();
                    break;
                case 'Escape':
                    self.hideDropdown();
                    break;
            }
        });
        
        // 点击其他地方关闭下拉框
        $(document).on('click', function(e) {
            if (!self.container.is(e.target) && self.container.has(e.target).length === 0) {
                self.hideDropdown();
            }
        });
    }
    
    // 模糊匹配搜索 - 支持不连续的字符匹配
    fuzzyMatch(text, keyword) {
        text = (text || '').toLowerCase();
        keyword = keyword.toLowerCase();
        return this.matchDiscontinuousChars(text, keyword);
    }
    
    // 不连续字符匹配算法
    matchDiscontinuousChars(text, keyword) {
        let textIndex = 0;
        let keywordIndex = 0;
        
        while (textIndex < text.length && keywordIndex < keyword.length) {
            if (text[textIndex] === keyword[keywordIndex]) {
                keywordIndex++;
            }
            textIndex++;
        }
        
        return keywordIndex === keyword.length;
    }
    
    search(keyword) {
        const self = this;
        this.currentResults = this.items.filter(item => {
            return this.fuzzyMatch(item[this.fieldName], keyword) || 
                   this.fuzzyMatch(item[this.fieldCode], keyword);
        }).slice(0, 20); // 限制最多显示20条
        
        this.selectedIndex = -1;
        this.renderDropdown();
    }
    
    renderDropdown() {
        const self = this;
        if (this.currentResults.length === 0) {
            this.dropdown.html('<div class="p-2 text-muted">未找到匹配的结果</div>');
        } else {
            const items = this.currentResults.map((item, index) => {
                return `<div class="${this.itemClass} p-2 border-bottom" 
                            data-index="${index}" 
                            data-id="${item.id}"
                            style="cursor: pointer;">
                            <strong>${item[self.fieldCode]}</strong> - ${item[self.fieldName]}
                        </div>`;
            }).join('');
            this.dropdown.html(items);
            
            // 绑定点击事件
            this.dropdown.find('.' + this.itemClass).on('click', function() {
                self.selectItem($(this).data('index'));
            });
            
            // 悬停效果
            this.dropdown.find('.' + this.itemClass).hover(function() {
                self.selectedIndex = $(this).data('index');
                self.updateSelection();
            });
        }
        
        this.showDropdown();
    }
    
    selectNext() {
        if (this.currentResults.length === 0) return;
        this.selectedIndex = (this.selectedIndex + 1) % this.currentResults.length;
        this.updateSelection();
    }
    
    selectPrev() {
        if (this.currentResults.length === 0) return;
        this.selectedIndex = this.selectedIndex <= 0 ? this.currentResults.length - 1 : this.selectedIndex - 1;
        this.updateSelection();
    }
    
    updateSelection() {
        this.dropdown.find('.' + this.itemClass).removeClass('bg-primary text-white');
        this.dropdown.find('.' + this.itemClass).eq(this.selectedIndex).addClass('bg-primary text-white');
        
        // 滚动到可见区域
        const selectedItem = this.dropdown.find('.' + this.itemClass).eq(this.selectedIndex);
        this.dropdown.scrollTop(selectedItem.position().top + this.dropdown.scrollTop());
    }
    
    selectItem(index) {
        if (index < 0 || index >= this.currentResults.length) return;
        
        const item = this.currentResults[index];
        this.selectedId = item.id;
        this.hiddenInput.val(item.id);
        this.input.val(`${item[this.fieldCode]} - ${item[this.fieldName]}`);
        
        this.hideDropdown();
        this.onSelect(item);
    }
    
    confirmSelection() {
        if (this.selectedIndex >= 0 && this.selectedIndex < this.currentResults.length) {
            this.selectItem(this.selectedIndex);
        } else if (this.currentResults.length === 1) {
            // 如果只有一个结果，直接选中
            this.selectItem(0);
        }
    }
    
    showDropdown() {
        this.dropdown.show();
    }
    
    hideDropdown() {
        this.dropdown.hide();
        this.selectedIndex = -1;
    }
    
    getContainer() {
        return this.container;
    }
    
    getValue() {
        return this.hiddenInput.val();
    }
    
    setValue(id) {
        this.selectedId = id;
        this.hiddenInput.val(id);
        if (id) {
            const item = this.items.find(p => String(p.id) === String(id));
            if (item) {
                this.input.val(`${item[this.fieldCode]} - ${item[this.fieldName]}`);
            }
        } else {
            this.input.val('');
        }
    }
}

// ============================================
// 商品搜索选择器类 - 支持模糊搜索和键盘导航
// ============================================
class ProductSearcher {
    constructor(options) {
        this.products = options.products || [];
        this.onSelect = options.onSelect || function() {};
        this.containerClass = options.containerClass || 'product-search-container';
        this.rowId = options.rowId || 0;
        this.placeholder = options.placeholder || '输入商品名称或编码搜索...';
        this.selectedProductId = options.selectedProductId || null;
        
        this.init();
    }
    
    init() {
        // 创建容器
        this.container = $(`
            <div class="${this.containerClass}" style="position: relative;">
                <input type="text" class="form-control product-search-input" 
                       placeholder="${this.placeholder}" autocomplete="off"
                       value="${this.getSelectedProductText()}">
                <input type="hidden" class="product-id-input" name="product_id[]" value="${this.selectedProductId || ''}">
                <div class="product-dropdown" style="
                    position: absolute;
                    top: 100%;
                    left: 0;
                    right: 0;
                    max-height: 250px;
                    overflow-y: auto;
                    background: white;
                    border: 1px solid #dee2e6;
                    border-top: none;
                    border-radius: 0 0 0.25rem 0.25rem;
                    z-index: 1000;
                    display: none;
                    box-shadow: 0 0.5rem 1rem rgba(0,0,0,0.15);
                "></div>
            </div>
        `);
        
        this.input = this.container.find('.product-search-input');
        this.dropdown = this.container.find('.product-dropdown');
        this.hiddenInput = this.container.find('.product-id-input');
        this.selectedIndex = -1;
        this.currentResults = [];
        
        this.bindEvents();
    }
    
    getSelectedProductText() {
        if (this.selectedProductId) {
            const product = this.products.find(p => String(p.id) === String(this.selectedProductId));
            if (product) {
                return `${product.code} - ${product.name}`;
            }
        }
        return '';
    }
    
    bindEvents() {
        const self = this;
        
        // 输入事件 - 实时搜索
        this.input.on('input', function() {
            const keyword = $(this).val().trim();
            if (keyword.length > 0) {
                self.search(keyword);
            } else {
                self.hideDropdown();
            }
        });
        
        // 聚焦事件
        this.input.on('focus', function() {
            const keyword = $(this).val().trim();
            if (keyword.length > 0) {
                self.search(keyword);
            }
        });
        
        // 键盘事件
        this.input.on('keydown', function(e) {
            if (!self.dropdown.is(':visible')) {
                if (e.key === 'ArrowDown' || e.key === 'Enter') {
                    const keyword = $(this).val().trim();
                    if (keyword.length > 0) {
                        self.search(keyword);
                        e.preventDefault();
                    }
                }
                return;
            }
            
            switch(e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    self.selectNext();
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    self.selectPrev();
                    break;
                case 'Enter':
                    e.preventDefault();
                    self.confirmSelection();
                    break;
                case 'Escape':
                    self.hideDropdown();
                    break;
            }
        });
        
        // 点击其他地方关闭下拉框
        $(document).on('click', function(e) {
            if (!self.container.is(e.target) && self.container.has(e.target).length === 0) {
                self.hideDropdown();
            }
        });
    }
    
    // 模糊匹配搜索 - 支持不连续的字符匹配
    fuzzyMatch(text, keyword) {
        text = text.toLowerCase();
        keyword = keyword.toLowerCase();
        return this.matchDiscontinuousChars(text, keyword);
    }
    
    // 不连续字符匹配算法
    matchDiscontinuousChars(text, keyword) {
        let textIndex = 0;
        let keywordIndex = 0;
        
        while (textIndex < text.length && keywordIndex < keyword.length) {
            if (text[textIndex] === keyword[keywordIndex]) {
                keywordIndex++;
            }
            textIndex++;
        }
        
        return keywordIndex === keyword.length;
    }
    
    search(keyword) {
        const self = this;
        this.currentResults = this.products.filter(product => {
            return this.fuzzyMatch(product.name, keyword) || 
                   this.fuzzyMatch(product.code, keyword) ||
                   this.fuzzyMatch(product.specification || '', keyword);
        }).slice(0, 20); // 限制最多显示20条
        
        this.selectedIndex = -1;
        this.renderDropdown();
    }
    
    renderDropdown() {
        if (this.currentResults.length === 0) {
            this.dropdown.html('<div class="p-2 text-muted">未找到匹配的商品</div>');
        } else {
            const items = this.currentResults.map((product, index) => {
                const stockInfo = product.stock_quantity !== undefined ? ` - 库存: ${product.stock_quantity}${product.unit || ''}` : '';
                return `<div class="product-search-item p-2 border-bottom" 
                            data-index="${index}" 
                            data-id="${product.id}"
                            style="cursor: pointer;">
                            <strong>${product.code}</strong> - ${product.name}
                            <small class="text-muted">${product.specification || '无规格'}${stockInfo}</small>
                        </div>`;
            }).join('');
            this.dropdown.html(items);
            
            // 绑定点击事件
            const self = this;
            this.dropdown.find('.product-search-item').on('click', function() {
                self.selectItem($(this).data('index'));
            });
            
            // 悬停效果
            this.dropdown.find('.product-search-item').hover(function() {
                self.selectedIndex = $(this).data('index');
                self.updateSelection();
            });
        }
        
        this.showDropdown();
    }
    
    selectNext() {
        if (this.currentResults.length === 0) return;
        this.selectedIndex = (this.selectedIndex + 1) % this.currentResults.length;
        this.updateSelection();
    }
    
    selectPrev() {
        if (this.currentResults.length === 0) return;
        this.selectedIndex = this.selectedIndex <= 0 ? this.currentResults.length - 1 : this.selectedIndex - 1;
        this.updateSelection();
    }
    
    updateSelection() {
        this.dropdown.find('.product-search-item').removeClass('bg-primary text-white');
        this.dropdown.find('.product-search-item').eq(this.selectedIndex).addClass('bg-primary text-white');
        
        // 滚动到可见区域
        const selectedItem = this.dropdown.find('.product-search-item').eq(this.selectedIndex);
        this.dropdown.scrollTop(selectedItem.position().top + this.dropdown.scrollTop());
    }
    
    selectItem(index) {
        if (index < 0 || index >= this.currentResults.length) return;
        
        const product = this.currentResults[index];
        this.selectedProductId = product.id;
        this.hiddenInput.val(product.id);
        this.input.val(`${product.code} - ${product.name}`);
        
        this.hideDropdown();
        this.onSelect(product);
    }
    
    confirmSelection() {
        if (this.selectedIndex >= 0 && this.selectedIndex < this.currentResults.length) {
            this.selectItem(this.selectedIndex);
        } else if (this.currentResults.length === 1) {
            // 如果只有一个结果，直接选中
            this.selectItem(0);
        }
    }
    
    showDropdown() {
        this.dropdown.show();
    }
    
    hideDropdown() {
        this.dropdown.hide();
        this.selectedIndex = -1;
    }
    
    getContainer() {
        return this.container;
    }
    
    getValue() {
        return this.hiddenInput.val();
    }
    
    setValue(productId) {
        this.selectedProductId = productId;
        this.hiddenInput.val(productId);
        if (productId) {
            const product = this.products.find(p => String(p.id) === String(productId));
            if (product) {
                this.input.val(`${product.code} - ${product.name}`);
            }
        } else {
            this.input.val('');
        }
    }
}

// 初始化商品搜索选择器的工厂函数
function initProductSearch(containerSelector, products, onSelect, rowId) {
    const searcher = new ProductSearcher({
        products: products,
        onSelect: onSelect,
        containerClass: `product-search-${rowId}`,
        rowId: rowId,
        placeholder: '输入商品名称或编码搜索...'
    });
    $(containerSelector).append(searcher.getContainer());
    return searcher;
}

// 初始化通用实体搜索选择器的工厂函数
function initEntitySearch(containerSelector, items, onSelect, options) {
    const searcher = new EntitySearcher({
        items: items,
        onSelect: onSelect,
        containerClass: options.containerClass || 'entity-search',
        fieldCode: options.fieldCode || 'code',
        fieldName: options.fieldName || 'name',
        placeholder: options.placeholder || '输入名称或编码搜索...',
        selectedId: options.selectedId || null,
        hiddenName: options.hiddenName || 'entity_id'
    });
    $(containerSelector).append(searcher.getContainer());
    return searcher;
}

$(document).ready(function() {
    // 自动关闭警告框
    setTimeout(function() {
        $('.alert').alert('close');
    }, 5000);
    
    // 确认删除对话框
    $('.confirm-delete').on('click', function(e) {
        e.preventDefault();
        const url = $(this).attr('href');
        const itemName = $(this).data('name') || '此项';
        
        if (confirm(`确定要删除 ${itemName} 吗？此操作不可撤销。`)) {
            window.location.href = url;
        }
    });
    
    // 表单验证增强
    $('form').on('submit', function() {
        $(this).find('button[type="submit"]').prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 处理中...');
    });
    
    // 数字输入框格式化
    $('.number-input').on('blur', function() {
        let value = parseFloat($(this).val());
        if (!isNaN(value)) {
            $(this).val(value.toFixed(2));
        }
    });
    
    // 表格行悬停效果
    $('.table-hover tbody tr').hover(
        function() {
            $(this).addClass('table-active');
        },
        function() {
            $(this).removeClass('table-active');
        }
    );
    
    // 日期选择器初始化
    if ($.fn.datepicker) {
        $('.datepicker').datepicker({
            format: 'yyyy-mm-dd',
            autoclose: true,
            todayHighlight: true,
            language: 'zh-CN'
        });
    }
    
    // 搜索框自动聚焦
    $('.search-box input[type="search"]').focus();
    
    // 打印功能
    $('.btn-print').on('click', function() {
        window.print();
    });
    
    // 导出功能占位
    $('.btn-export').on('click', function() {
        alert('导出功能正在开发中...');
    });
    
    // 动态计算金额
    $('.calc-amount').on('input', function() {
        const row = $(this).closest('tr');
        const quantity = parseFloat(row.find('.quantity').val()) || 0;
        const price = parseFloat(row.find('.price').val()) || 0;
        const amount = quantity * price;
        row.find('.amount').val(amount.toFixed(2));
        
        // 更新总计
        updateTotal();
    });
    
    // 更新总计
    function updateTotal() {
        let total = 0;
        $('.amount').each(function() {
            total += parseFloat($(this).val()) || 0;
        });
        $('#total-amount').text(total.toFixed(2));
    }
    
    // 添加行到动态表格
    $('.add-row').on('click', function() {
        const template = $('#row-template').html();
        const $tbody = $(this).closest('table').find('tbody');
        const newRow = $(template);
        newRow.find('.row-index').text($tbody.find('tr').length + 1);
        $tbody.append(newRow);
        
        // 重新绑定事件
        newRow.find('.calc-amount').on('input', function() {
            const row = $(this).closest('tr');
            const quantity = parseFloat(row.find('.quantity').val()) || 0;
            const price = parseFloat(row.find('.price').val()) || 0;
            const amount = quantity * price;
            row.find('.amount').val(amount.toFixed(2));
            updateTotal();
        });
        
        newRow.find('.remove-row').on('click', function() {
            $(this).closest('tr').remove();
            updateTotal();
            updateRowIndexes();
        });
    });
    
    // 更新行号
    function updateRowIndexes() {
        $('tbody tr').each(function(index) {
            $(this).find('.row-index').text(index + 1);
        });
    }
    
    // 移除行
    $('.remove-row').on('click', function() {
        $(this).closest('tr').remove();
        updateTotal();
        updateRowIndexes();
    });
    
    // 库存预警检查
    function checkStockWarning() {
        $('.stock-warning').each(function() {
            const stock = parseFloat($(this).data('stock')) || 0;
            const safety = parseFloat($(this).data('safety')) || 0;
            
            if (stock <= safety) {
                $(this).addClass('text-danger fw-bold');
                $(this).append('<i class="bi bi-exclamation-triangle ms-1"></i>');
            }
        });
    }
    
    checkStockWarning();
    
    // 响应式表格调整
    function adjustTableResponsive() {
        if ($(window).width() < 768) {
            $('.table').addClass('table-responsive');
        } else {
            $('.table').removeClass('table-responsive');
        }
    }
    
    adjustTableResponsive();
    $(window).resize(adjustTableResponsive);
    
    // 主题切换
    $('#theme-toggle').on('click', function() {
        const currentTheme = $('html').attr('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        $('html').attr('data-bs-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        $(this).find('i').toggleClass('bi-moon bi-sun');
    });
    
    // 加载保存的主题
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        $('html').attr('data-bs-theme', savedTheme);
        if (savedTheme === 'dark') {
            $('#theme-toggle i').removeClass('bi-moon').addClass('bi-sun');
        }
    }
});
