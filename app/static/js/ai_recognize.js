/**
 * AI 单据识别组件
 *
 * 使用方法：
 *   const ai = new AIRecognize({
 *       docType: 'purchase',        // 单据类型
 *       onResult: function(data) {  // 识别结果回调
 *           // 自动填写表单
 *       }
 *   });
 *   ai.mount('#ai-button-container');  // 挂载到指定容器
 *
 * 依赖：jQuery, Bootstrap 5
 */

class AIRecognize {
    constructor(options) {
        this.docType = options.docType || 'purchase';
        this.onResult = options.onResult || function() {};
        this.maxWidth = options.maxWidth || 1024;
        this.maxSizeKB = options.maxSizeKB || 1024;
        this.quality = options.quality || 0.8;
        this.container = null;
        this.fileInput = null;
        this.isLoading = false;
    }

    /**
     * 挂载到指定容器
     */
    mount(selector) {
        this.container = $(selector);
        if (this.container.length === 0) {
            console.warn('AIRecognize: 容器不存在', selector);
            return;
        }
        this._render();
        this._bindEvents();
    }

    /**
     * 渲染按钮和隐藏的文件输入
     */
    _render() {
        const html = `
            <div class="ai-recognize-wrapper mb-3">
                <div class="ai-recognize-btn" id="ai-recognize-trigger-${this.docType}"
                     style="border: 2px dashed #0d6efd; border-radius: 8px; padding: 20px;
                            text-align: center; cursor: pointer; background: #f8f9fa;
                            transition: all 0.3s;">
                    <i class="bi bi-camera" style="font-size: 2rem; color: #0d6efd;"></i>
                    <p class="mb-0 mt-2 text-primary fw-bold">拍照识别单据</p>
                    <small class="text-muted">支持拍照或选择图片文件</small>
                </div>
                <input type="file" accept="image/*" capture="camera"
                       id="ai-file-input-${this.docType}" style="display: none;">
                <div id="ai-preview-${this.docType}" style="display: none;" class="mt-2">
                    <div style="position: relative; display: inline-block;">
                        <img id="ai-preview-img-${this.docType}" style="max-width: 100%; max-height: 200px; border-radius: 8px;">
                        <button type="button" class="btn btn-sm btn-danger" id="ai-clear-${this.docType}"
                                style="position: absolute; top: 5px; right: 5px;">
                            <i class="bi bi-x"></i>
                        </button>
                    </div>
                </div>
                <div id="ai-loading-${this.docType}" style="display: none;" class="mt-2 text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">识别中...</span>
                    </div>
                    <p class="mt-2 text-primary">正在识别单据...</p>
                </div>
            </div>
        `;
        this.container.html(html);
    }

    /**
     * 绑定事件
     */
    _bindEvents() {
        const trigger = $(`#ai-recognize-trigger-${this.docType}`);
        const fileInput = $(`#ai-file-input-${this.docType}`);
        const clearBtn = $(`#ai-clear-${this.docType}`);

        // 点击触发文件选择
        trigger.on('click', () => {
            if (!this.isLoading) {
                fileInput.click();
            }
        });

        // 悬停效果
        trigger.on('mouseenter', function() {
            $(this).css('background', '#e7f1ff');
        }).on('mouseleave', function() {
            $(this).css('background', '#f8f9fa');
        });

        // 文件选择
        fileInput.on('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                this._handleFile(file);
            }
        });

        // 清除
        clearBtn.on('click', (e) => {
            e.stopPropagation();
            this._clear();
        });
    }

    /**
     * 处理选择的文件
     */
    async _handleFile(file) {
        if (!file.type.startsWith('image/')) {
            this._showError('请选择图片文件');
            return;
        }

        try {
            // 显示预览
            const previewUrl = URL.createObjectURL(file);
            $(`#ai-preview-img-${this.docType}`).attr('src', previewUrl);
            $(`#ai-preview-${this.docType}`).show();

            // 压缩图片
            const base64 = await this._compressImage(file);

            // 调用识别
            await this._recognize(base64);
        } catch (err) {
            this._showError(err.message || '处理图片失败');
        }
    }

    /**
     * 压缩图片
     */
    _compressImage(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const img = new Image();
                img.onload = () => {
                    const canvas = document.createElement('canvas');
                    let width = img.width;
                    let height = img.height;

                    // 缩放
                    if (width > this.maxWidth) {
                        height = Math.round(height * this.maxWidth / width);
                        width = this.maxWidth;
                    }

                    canvas.width = width;
                    canvas.height = height;

                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0, width, height);

                    // 转为 base64
                    let quality = this.quality;
                    let result = canvas.toDataURL('image/jpeg', quality);

                    // 如果还是太大，继续压缩
                    while (result.length > this.maxSizeKB * 1024 * 4 / 3 && quality > 0.3) {
                        quality -= 0.1;
                        result = canvas.toDataURL('image/jpeg', quality);
                    }

                    resolve(result);
                };
                img.onerror = () => reject(new Error('加载图片失败'));
                img.src = e.target.result;
            };
            reader.onerror = () => reject(new Error('读取文件失败'));
            reader.readAsDataURL(file);
        });
    }

    /**
     * 调用 AI 识别 API
     */
    async _recognize(imageBase64) {
        this._setLoading(true);

        try {
            const formData = new FormData();
            formData.append('image_base64', imageBase64);
            formData.append('doc_type', this.docType);

            const response = await fetch('/api/ai/recognize', {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (result.success) {
                this._showConfirmDialog(result.data);
            } else {
                this._showError(result.message || '识别失败');
            }
        } catch (err) {
            if (err.name === 'TypeError' && err.message.includes('fetch')) {
                this._showError('网络错误，请检查网络连接');
            } else {
                this._showError(err.message || '识别失败，请重试');
            }
        } finally {
            this._setLoading(false);
        }
    }

    /**
     * 显示确认对话框
     */
    _showConfirmDialog(data) {
        const summary = this._buildSummary(data);
        const modalId = 'ai-confirm-modal-' + this.docType;

        // 移除旧的模态框
        $(`#${modalId}`).remove();

        const modalHtml = `
            <div class="modal fade" id="${modalId}" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="bi bi-robot"></i> AI 识别结果
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-info">
                                <i class="bi bi-info-circle"></i> 请确认以下识别结果，确认后将自动填写表单。
                            </div>
                            <div id="ai-result-summary-${this.docType}">
                                ${summary}
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                            <button type="button" class="btn btn-primary" id="ai-confirm-btn-${this.docType}">
                                <i class="bi bi-check-circle"></i> 确认填写
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        $('body').append(modalHtml);

        const modal = new bootstrap.Modal(document.getElementById(modalId));
        modal.show();

        // 确认按钮
        $(`#ai-confirm-btn-${this.docType}`).on('click', () => {
            modal.hide();
            this.onResult(data);
            this._clear();
        });

        // 模态框关闭后清理
        $(`#${modalId}`).on('hidden.bs.modal', function() {
            $(this).remove();
        });
    }

    /**
     * 构建识别结果摘要
     */
    _buildSummary(data) {
        let html = '<div class="table-responsive"><table class="table table-sm table-bordered">';

        // 根据单据类型显示不同字段
        const fieldMap = {
            purchase: [
                ['supplier_name', '供应商'],
                ['order_date', '订单日期'],
            ],
            sales: [
                ['customer_name', '客户'],
                ['order_date', '订单日期'],
            ],
            stock_in: [
                ['receipt_date', '入库日期'],
            ],
            stock_out: [
                ['delivery_date', '出库日期'],
            ],
            receipt: [
                ['amount', '金额'],
                ['receipt_date', '收款日期'],
                ['payment_method', '支付方式'],
            ],
            payment: [
                ['amount', '金额'],
                ['payment_date', '付款日期'],
                ['payment_method', '支付方式'],
            ],
            expense: [
                ['category', '费用类别'],
                ['amount', '金额'],
                ['expense_date', '费用日期'],
                ['payee', '收款方'],
            ],
            return: [
                ['return_date', '退货日期'],
            ],
        };

        const fields = fieldMap[this.docType] || [];
        for (const [key, label] of fields) {
            if (data[key] != null) {
                html += `<tr><th style="width: 30%">${label}</th><td>${data[key]}</td></tr>`;
            }
        }

        // 商品明细
        if (data.items && data.items.length > 0) {
            html += `<tr><th>商品明细</th><td>`;
            html += `<table class="table table-sm mb-0">`;
            html += `<thead><tr><th>名称</th><th>数量</th><th>单价</th></tr></thead><tbody>`;
            for (const item of data.items) {
                html += `<tr>
                    <td>${item.name || '-'}</td>
                    <td>${item.quantity || '-'}</td>
                    <td>${item.unit_price || '-'}</td>
                </tr>`;
            }
            html += `</tbody></table></td></tr>`;
        }

        // 备注
        if (data.notes) {
            html += `<tr><th>备注</th><td>${data.notes}</td></tr>`;
        }

        html += '</table></div>';
        return html;
    }

    /**
     * 设置加载状态
     */
    _setLoading(loading) {
        this.isLoading = loading;
        if (loading) {
            $(`#ai-loading-${this.docType}`).show();
            $(`#ai-recognize-trigger-${this.docType}`).css('opacity', '0.6');
        } else {
            $(`#ai-loading-${this.docType}`).hide();
            $(`#ai-recognize-trigger-${this.docType}`).css('opacity', '1');
        }
    }

    /**
     * 显示错误提示
     */
    _showError(message) {
        const errorId = 'ai-error-' + this.docType;
        $(`#${errorId}`).remove();

        const html = `
            <div id="${errorId}" class="alert alert-danger alert-dismissible fade show mt-2" role="alert">
                <i class="bi bi-exclamation-triangle"></i> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        this.container.append(html);

        // 3秒后自动消失
        setTimeout(() => {
            $(`#${errorId}`).fadeOut(function() {
                $(this).remove();
            });
        }, 5000);
    }

    /**
     * 清除预览和状态
     */
    _clear() {
        $(`#ai-preview-${this.docType}`).hide();
        $(`#ai-preview-img-${this.docType}`).attr('src', '');
        $(`#ai-file-input-${this.docType}`).val('');
    }
}

// 导出到全局
window.AIRecognize = AIRecognize;
