// 进销存管理系统主JavaScript文件

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