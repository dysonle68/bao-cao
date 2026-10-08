import re

with open('bao_cao_bang_gia.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Make KPIs dynamic by injecting Jinja-like variables
html = html.replace('383 <span style="font-size:16px; font-weight:600; color:var(--text-secondary);">SKU</span>', '{{TOTAL_SKU}} <span style="font-size:16px; font-weight:600; color:var(--text-secondary);">SKU</span>')
html = html.replace('56,089 <span style="font-size:14px; font-weight:600; color:var(--text-secondary);">VNĐ</span>', '{{AVG_PRICE}} <span style="font-size:14px; font-weight:600; color:var(--text-secondary);">VNĐ</span>')
html = html.replace('20,000 - 295,400 VNĐ', '{{PRICE_RANGE}} VNĐ')
html = html.replace('262 <span style="font-size:15px; font-weight:600;">(8%)</span> / 73 <span style="font-size:15px; font-weight:600;">(5%)</span>', '{{VAT_COUNTS}}')
html = html.replace('68.4% áp dụng VAT 8%', '{{VAT_PERCENT}}')
html = html.replace('92 <span style="font-size:16px; font-weight:600; color:var(--text-secondary);">QĐ</span>', '{{TOTAL_QD}} <span style="font-size:16px; font-weight:600; color:var(--text-secondary);">QĐ</span>')
html = html.replace('QĐ 0829-03/2025 lớn nhất (65 SKU)', '{{TOP_QD_TEXT}}')
html = html.replace('07/10/2026 15:52', '{{DATE_TIME}}')

# Replace Tab Badges
html = html.replace('<span class="tab-badge">383</span>', '<span class="tab-badge">{{TOTAL_SKU}}</span>')
html = html.replace('<span class="tab-badge">13</span>', '<span class="tab-badge">{{CN2_COUNT}}</span>')
html = html.replace('<span class="tab-badge">20</span>', '<span class="tab-badge">{{CTY_COUNT}}</span>')
html = html.replace('<span class="tab-badge">92</span>', '<span class="tab-badge">{{TOTAL_QD}}</span>')
html = html.replace('<span class="tab-badge">8</span>', '<span class="tab-badge">{{TOTAL_CAT}}</span>')

# Wipe out the hardcoded options in the select for Cat
html = re.sub(r'<select class="filter-select" id="catFilter" onchange="filterTable()">.*?</select>', '<select class="filter-select" id="catFilter" onchange="filterTable()">\\n                        <option value="">-- Tất cả Chủng loại --</option>\\n                        {{CAT_OPTIONS}}\\n                    </select>', html, flags=re.DOTALL)


# Replace static tbodys with placeholders
html = re.sub(r'<div id="tab-cn2" class="tab-panel">.*?<tbody>(.*?)</tbody>', '<div id="tab-cn2" class="tab-panel">\\n        <div class="table-card">\\n            <h3 style="margin-bottom: 16px; font-size:18px; font-weight:700;"><i class="fa-solid fa-code-branch" style="color:var(--accent-primary);"></i> Danh Mục Bảng Giá Chi Nhánh 2 (CN2)</h3>\\n            <div class="table-responsive">\\n                <table>\\n                    <thead>\\n                        <tr>\\n                            <th>STT</th>\\n                            <th>Mã Hàng</th>\\n                            <th>Tên Sản Phẩm</th>\\n                            <th>ĐVT</th>\\n                            <th>Giá Bán (VNĐ)</th>\\n                            <th>VAT</th>\\n                            <th>Quyết Định</th>\\n                            <th>Ngày Áp Dụng</th>\\n                        </tr>\\n                    </thead>\\n                    <tbody>\\n                        {{CN2_TBODY}}\\n                    </tbody>', html, flags=re.DOTALL)

html = re.sub(r'<div id="tab-cty" class="tab-panel">.*?<tbody>(.*?)</tbody>', '<div id="tab-cty" class="tab-panel">\\n        <div class="table-card">\\n            <h3 style="margin-bottom: 16px; font-size:18px; font-weight:700;"><i class="fa-solid fa-city" style="color:var(--accent-primary);"></i> Danh Mục Bảng Giá Khối Công Ty (CTY)</h3>\\n            <div class="table-responsive">\\n                <table>\\n                    <thead>\\n                        <tr>\\n                            <th>STT</th>\\n                            <th>Mã Hàng</th>\\n                            <th>Tên Sản Phẩm</th>\\n                            <th>ĐVT</th>\\n                            <th>Giá Bán (VNĐ)</th>\\n                            <th>VAT</th>\\n                            <th>Quyết Định</th>\\n                            <th>Ngày Áp Dụng</th>\\n                        </tr>\\n                    </thead>\\n                    <tbody>\\n                        {{CTY_TBODY}}\\n                    </tbody>', html, flags=re.DOTALL)

html = re.sub(r'<div id="tab-qd" class="tab-panel">.*?<tbody>(.*?)</tbody>', '<div id="tab-qd" class="tab-panel">\\n        <div class="table-card">\\n            <h3 style="margin-bottom: 16px; font-size:18px; font-weight:700;"><i class="fa-solid fa-file-invoice" style="color:var(--accent-primary);"></i> Tổng Hợp Các Quyết Định Áp Giá</h3>\\n            <div class="table-responsive">\\n                <table>\\n                    <thead>\\n                        <tr>\\n                            <th>STT</th>\\n                            <th>Số Quyết Định</th>\\n                            <th>Ngày Ban Hành</th>\\n                            <th>Số Sản Phẩm (SKU)</th>\\n                            <th>Giá Bán Thấp Nhất</th>\\n                            <th>Giá Bán Cao Nhất</th>\\n                            <th>Giá Bán Trung Bình</th>\\n                        </tr>\\n                    </thead>\\n                    <tbody>\\n                        {{QD_TBODY}}\\n                    </tbody>', html, flags=re.DOTALL)

html = re.sub(r'<div id="tab-cat" class="tab-panel">.*?<tbody>(.*?)</tbody>', '<div id="tab-cat" class="tab-panel">\\n        <div class="table-card">\\n            <h3 style="margin-bottom: 16px; font-size:18px; font-weight:700;"><i class="fa-solid fa-layer-group" style="color:#f59e0b;"></i> Phân Tích Cơ Cấu Chủng Loại Vật Liệu</h3>\\n            <div class="table-responsive">\\n                <table>\\n                    <thead>\\n                        <tr>\\n                            <th>STT</th>\\n                            <th>Chủng Loại Vật Liệu</th>\\n                            <th>Số Sản Phẩm (SKU)</th>\\n                            <th>Tỉ Trọng (%)</th>\\n                            <th>Giá Bán Thấp Nhất</th>\\n                            <th>Giá Bán Cao Nhất</th>\\n                            <th>Giá Bán Trung Bình</th>\\n                        </tr>\\n                    </thead>\\n                    <tbody>\\n                        {{CAT_TBODY}}\\n                    </tbody>', html, flags=re.DOTALL)

# Replace static dataset
html = re.sub(r'const dataset = \[.*?\];', 'const dataset = {{DATASET_JSON}};\\n\\n        // Set JS variables for dynamic charts\\n        const chartData = {{CHART_DATA_JSON}};', html, flags=re.DOTALL)

# Inject JS for charts data replacing the hardcoded ones
html = re.sub(r'labels: \["DAy PP".*?\],', 'labels: chartData.cat.labels,', html, flags=re.DOTALL)
html = re.sub(r'data: \[163, 127.*?\]', 'data: chartData.cat.data', html, flags=re.DOTALL)

html = re.sub(r'labels: \["D>i 30k".*?\],', 'labels: chartData.price.labels,', html, flags=re.DOTALL)
html = re.sub(r'data: \[7, 80.*?\]', 'data: chartData.price.data', html, flags=re.DOTALL)

html = re.sub(r'labels: \["8%", "5%", "0% / KhAc"\],', 'labels: chartData.vat.labels,', html, flags=re.DOTALL)
html = re.sub(r'data: \[262, 73, 48\]', 'data: chartData.vat.data', html, flags=re.DOTALL)

html = re.sub(r'labels: \["0829-03/2025".*?\],', 'labels: chartData.top_qd.labels,', html, flags=re.DOTALL)
html = re.sub(r'data: \[65, 61.*?\]', 'data: chartData.top_qd.data', html, flags=re.DOTALL)

html = re.sub(r'labels: \["BTH5782".*?\],', 'labels: chartData.top_price.labels,', html, flags=re.DOTALL)
html = re.sub(r'data: \[295400\.0, 238600\.0.*?\]', 'data: chartData.top_price.data', html, flags=re.DOTALL)

# Remove the BOM from CSV export string
html = html.replace("let csv = ''; // UTF-8 BOM", "let csv = '\\uFEFF'; // UTF-8 BOM")

with open('template.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Created template.html")
