/**
 * AI 单据识别组件
 *
 * 使用方法：
 *   const ai = new AIRecognize({
 *       docType: 'purchase',
 *       onResult: function(data) { // 填写表单 }
 *   });
 *   ai.mount('#ai-recognize-container');
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
        this.isLoading = false;
    }

    mount(selector) {
        this.container = $(selector);
        if (this.container.length === 0) return;
        this._render();
    }

    _render() {
        const self = this;
        const dt = this.docType;

        const html = `
            <div class="mb-3" style="border: 2px dashed #0d6efd; border-radius: 8px; padding: 16px; text-align: center; background: #f8f9fa;">
                <i class="bi bi-robot" style="font-size: 1.5rem; color: #0d6efd;"></i>
                <p class="mb-2 mt-1 text-primary fw-bold">AI 智能识别</p>
                <div class="d-flex justify-content-center gap-2">
                    <button type="button" class="btn btn-primary btn-sm"
                            onclick="window._ai_${dt}.openCamera()">
                        <i class="bi bi-camera"></i> 拍照
                    </button>
                    <button type="button" class="btn btn-outline-primary btn-sm"
                            onclick="window._ai_${dt}.openFile()">
                        <i class="bi bi-upload"></i> 选择图片
                    </button>
                </div>
                <small class="text-muted d-block mt-1">拍照或上传单据图片，自动识别填写</small>
            </div>
            <input type="file" accept="image/*" capture="environment"
                   id="ai-camera-${dt}" style="display:none;"
                   onchange="window._ai_${dt}.onFile(this)">
            <input type="file" accept="image/*"
                   id="ai-file-${dt}" style="display:none;"
                   onchange="window._ai_${dt}.onFile(this)">
            <div id="ai-preview-${dt}" style="display:none;" class="mt-2 mb-2">
                <div style="position:relative; display:inline-block;">
                    <img id="ai-preview-img-${dt}" style="max-width:100%; max-height:200px; border-radius:8px;">
                    <button type="button" class="btn btn-sm btn-danger"
                            onclick="window._ai_${dt}.clear()"
                            style="position:absolute; top:5px; right:5px;">
                        <i class="bi bi-x"></i>
                    </button>
                </div>
            </div>
            <div id="ai-loading-${dt}" style="display:none;" class="mt-2 text-center">
                <div class="spinner-border text-primary" role="status"></div>
                <p class="mt-2 text-primary">正在识别...</p>
            </div>
            <div id="ai-error-${dt}" style="display:none;" class="mt-2"></div>
        `;

        this.container.html(html);

        // 暴露到全局供 onclick 使用
        window[`_ai_${dt}`] = {
            openCamera: function() { self.openCamera(); },
            openFile: function() { self.openFile(); },
            onFile: function(input) { self.onFile(input); },
            clear: function() { self.clear(); }
        };
    }

    openCamera() {
        if (this.isLoading) return;
        document.getElementById(`ai-camera-${this.docType}`).click();
    }

    openFile() {
        if (this.isLoading) return;
        document.getElementById(`ai-file-${this.docType}`).click();
    }

    onFile(input) {
        const file = input.files[0];
        if (!file) return;

        if (!file.type.startsWith('image/')) {
            this.showError('请选择图片文件');
            return;
        }

        // 显示预览
        const url = URL.createObjectURL(file);
        $(`#ai-preview-img-${this.docType}`).attr('src', url);
        $(`#ai-preview-${this.docType}`).show();

        // 压缩后识别
        const self = this;
        this._compressImage(file).then(function(base64) {
            self._recognize(base64);
        }).catch(function(err) {
            self.showError(err.message || '处理图片失败');
        });
    }

    _compressImage(file) {
        const self = this;
        return new Promise(function(resolve, reject) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = new Image();
                img.onload = function() {
                    const canvas = document.createElement('canvas');
                    let w = img.width, h = img.height;
                    if (w > self.maxWidth) {
                        h = Math.round(h * self.maxWidth / w);
                        w = self.maxWidth;
                    }
                    canvas.width = w;
                    canvas.height = h;
                    canvas.getContext('2d').drawImage(img, 0, 0, w, h);

                    let q = self.quality;
                    let result = canvas.toDataURL('image/jpeg', q);
                    while (result.length > self.maxSizeKB * 1024 * 4 / 3 && q > 0.3) {
                        q -= 0.1;
                        result = canvas.toDataURL('image/jpeg', q);
                    }
                    resolve(result);
                };
                img.onerror = function() { reject(new Error('加载图片失败')); };
                img.src = e.target.result;
            };
            reader.onerror = function() { reject(new Error('读取文件失败')); };
            reader.readAsDataURL(file);
        });
    }

    async _recognize(imageBase64) {
        const dt = this.docType;
        this.isLoading = true;
        $(`#ai-loading-${dt}`).show();
        $(`#ai-error-${dt}`).hide();

        try {
            const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
            const body = new FormData();
            body.append('image_base64', imageBase64);
            body.append('doc_type', dt);

            const resp = await fetch('/api/ai/recognize', {
                method: 'POST',
                body: body,
                headers: { 'X-CSRFToken': csrf }
            });

            const result = await resp.json();

            if (result.success) {
                this._showConfirm(result.data);
            } else {
                this.showError(result.message || '识别失败');
            }
        } catch (err) {
            this.showError(err.message || '网络错误，请重试');
        } finally {
            this.isLoading = false;
            $(`#ai-loading-${dt}`).hide();
        }
    }

    _showConfirm(data) {
        const dt = this.docType;
        const self = this;
        const summary = this._buildSummary(data);
        const modalId = 'ai-modal-' + dt;

        $('#' + modalId).remove();

        $('body').append(`
            <div class="modal fade" id="${modalId}" tabindex="-1">
              <div class="modal-dialog">
                <div class="modal-content">
                  <div class="modal-header">
                    <h5 class="modal-title"><i class="bi bi-robot"></i> AI 识别结果</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                  </div>
                  <div class="modal-body">
                    <div class="alert alert-info"><i class="bi bi-info-circle"></i> 请确认识别结果，确认后自动填写表单。</div>
                    ${summary}
                  </div>
                  <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                    <button type="button" class="btn btn-primary" id="ai-confirm-${dt}">
                      <i class="bi bi-check-circle"></i> 确认填写
                    </button>
                  </div>
                </div>
              </div>
            </div>
        `);

        const modal = new bootstrap.Modal(document.getElementById(modalId));
        modal.show();

        $(`#ai-confirm-${dt}`).on('click', function() {
            modal.hide();
            self.onResult(data);
            self.clear();
        });

        $(`#${modalId}`).on('hidden.bs.modal', function() { $(this).remove(); });
    }

    _buildSummary(data) {
        let h = '<table class="table table-sm table-bordered">';
        const fields = {
            purchase: [['supplier_name','供应商'],['order_date','订单日期']],
            sales: [['customer_name','客户'],['order_date','订单日期']],
            stock_in: [['receipt_date','入库日期']],
            stock_out: [['delivery_date','出库日期']],
            receipt: [['amount','金额'],['receipt_date','收款日期'],['payment_method','支付方式']],
            payment: [['amount','金额'],['payment_date','付款日期'],['payment_method','支付方式']],
            expense: [['category','费用类别'],['amount','金额'],['expense_date','费用日期'],['payee','收款方']],
            return: [['return_date','退货日期']]
        };

        for (const [k, l] of (fields[this.docType] || [])) {
            if (data[k] != null) h += `<tr><th style="width:30%">${l}</th><td>${data[k]}</td></tr>`;
        }

        if (data.items && data.items.length > 0) {
            h += '<tr><th>商品</th><td><table class="table table-sm mb-0"><thead><tr><th>名称</th><th>数量</th><th>单价</th></tr></thead><tbody>';
            for (const i of data.items) {
                h += `<tr><td>${i.name||'-'}</td><td>${i.quantity||'-'}</td><td>${i.unit_price||'-'}</td></tr>`;
            }
            h += '</tbody></table></td></tr>';
        }

        if (data.notes) h += `<tr><th>备注</th><td>${data.notes}</td></tr>`;
        return h + '</table>';
    }

    showError(msg) {
        const dt = this.docType;
        $(`#ai-error-${dt}`).html(
            `<div class="alert alert-danger alert-dismissible fade show" role="alert">
                <i class="bi bi-exclamation-triangle"></i> ${msg}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>`
        ).show();
        setTimeout(function() { $(`#ai-error-${dt}`).fadeOut(); }, 5000);
    }

    clear() {
        const dt = this.docType;
        $(`#ai-preview-${dt}`).hide();
        $(`#ai-preview-img-${dt}`).attr('src', '');
        $(`#ai-camera-${dt}`).val('');
        $(`#ai-file-${dt}`).val('');
    }
}

window.AIRecognize = AIRecognize;
