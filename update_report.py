import pandas as pd
import json
import os
from datetime import datetime

def generate_report():
    # URL of the Google Sheet (Excel download format)
    sheet_url = 'https://docs.google.com/uc?export=download&id=1YK0xnK83tIvlbdCzLIUbUbe_tYSwzoy6'
    
    try:
        # Read the Excel file without header
        df = pd.read_excel(sheet_url, sheet_name='DATA', header=None)
        
        # Find the row that contains 'Mã hàng'
        header_row_idx = None
        for idx, row in df.iterrows():
            if 'Mã hàng' in row.values:
                header_row_idx = idx
                break
                
        if header_row_idx is not None:
            # Set the columns
            df.columns = df.iloc[header_row_idx]
            # Drop the header row and any rows above it
            df = df.iloc[header_row_idx+1:].reset_index(drop=True)
        else:
            print("Cannot find header row with 'Mã hàng'")
            return

        # Clean up column names in case of trailing spaces
        df.columns = [str(c).strip() if pd.notnull(c) else f"Unnamed_{i}" for i, c in enumerate(df.columns)]
        
        # Keep relevant columns and drop rows with empty 'Mã hàng'
        cols = ['Mã hàng', 'tên hàng', 'ĐVT', 'Giá bán', 'Quyết định', 'ngày']
        available_cols = [c for c in cols if c in df.columns]
        df = df[available_cols].dropna(subset=['Mã hàng'])
        
        # Convert date to string if available
        if 'ngày' in df.columns:
            df['ngày'] = pd.to_datetime(df['ngày'], errors='coerce').dt.strftime('%d/%m/%Y').fillna('')
            
        # Ensure Giá bán is numeric
        if 'Giá bán' in df.columns:
            df['Giá bán'] = pd.to_numeric(df['Giá bán'], errors='coerce').fillna(0)
            
        # Basic metrics
        total_items = len(df)
        avg_price = df['Giá bán'].mean() if 'Giá bán' in df.columns and total_items > 0 else 0
        total_decisions = df['Quyết định'].nunique() if 'Quyết định' in df.columns else 0
        
        # Convert to records for JSON
        records = df.to_dict(orient='records')
        
        last_updated = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
    except Exception as e:
        print(f"Error reading Google Sheet: {e}")
        records = []
        total_items = 0
        avg_price = 0
        total_decisions = 0
        last_updated = datetime.now().strftime('%d/%m/%Y %H:%M:%S') + " (Error)"

    # Create HTML
    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Báo Cáo Dữ Liệu Bảng Giá - Tự Động Cập Nhật</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/dataTables.bootstrap5.min.css">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root {{
            --primary: #4361ee;
            --secondary: #3f37c9;
            --success: #4cc9f0;
            --info: #4895ef;
            --warning: #f72585;
            --bg-color: #f8f9fa;
            --card-bg: #ffffff;
        }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: #333;
        }}
        .header {{
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            padding: 3rem 0;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}
        .metric-card {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            transition: transform 0.3s ease;
            border-left: 5px solid var(--primary);
            height: 100%;
        }}
        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.1);
        }}
        .metric-card.success {{ border-color: var(--success); }}
        .metric-card.info {{ border-color: var(--info); }}
        .metric-title {{
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #6c757d;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }}
        .metric-value {{
            font-size: 2rem;
            font-weight: 700;
            color: #212529;
        }}
        .data-container {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 3rem;
        }}
        .table thead th {{
            background-color: #f1f3f5;
            color: #495057;
            font-weight: 600;
            border-bottom: 2px solid #dee2e6;
        }}
        .badge-update {{
            background: rgba(255,255,255,0.2);
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
            display: inline-block;
            margin-top: 10px;
        }}
        .footer {{
            text-align: center;
            padding: 2rem 0;
            color: #6c757d;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>

    <div class="header">
        <div class="container text-center">
            <h1><i class="fa-solid fa-chart-line me-2"></i> Báo Cáo Bảng Giá Trực Tuyến</h1>
            <p class="lead">Dữ liệu được đồng bộ tự động từ Google Sheets</p>
            <div class="badge-update"><i class="fa-regular fa-clock me-1"></i> Cập nhật lần cuối: {last_updated}</div>
        </div>
    </div>

    <div class="container">
        <!-- Metrics -->
        <div class="row g-4 mb-4">
            <div class="col-md-4">
                <div class="metric-card">
                    <div class="metric-title">Tổng Sản Phẩm</div>
                    <div class="metric-value">{total_items:,}</div>
                    <div class="text-muted small mt-2"><i class="fa-solid fa-box text-primary"></i> mã hàng trong hệ thống</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="metric-card success">
                    <div class="metric-title">Giá Trung Bình</div>
                    <div class="metric-value">{int(avg_price):,} ₫</div>
                    <div class="text-muted small mt-2"><i class="fa-solid fa-coins text-success"></i> trên mỗi sản phẩm</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="metric-card info">
                    <div class="metric-title">Số Quyết Định</div>
                    <div class="metric-value">{total_decisions:,}</div>
                    <div class="text-muted small mt-2"><i class="fa-solid fa-file-contract text-info"></i> văn bản áp dụng</div>
                </div>
            </div>
        </div>

        <!-- Data Table -->
        <div class="data-container">
            <h4 class="mb-4"><i class="fa-solid fa-table-list me-2 text-primary"></i> Chi tiết bảng giá</h4>
            <div class="table-responsive">
                <table id="dataTable" class="table table-hover align-middle">
                    <thead>
                        <tr>
                            <th>Mã Hàng</th>
                            <th>Tên Hàng</th>
                            <th>ĐVT</th>
                            <th>Giá Bán</th>
                            <th>Quyết Định</th>
                            <th>Ngày Áp Dụng</th>
                        </tr>
                    </thead>
                    <tbody>"""

    for row in records:
        ma = row.get('Mã hàng', '')
        ten = row.get('tên hàng', '')
        dvt = row.get('ĐVT', '')
        gia = row.get('Giá bán', 0)
        qd = row.get('Quyết định', '')
        ngay = row.get('ngày', '')
        
        gia_fmt = f"{int(gia):,}" if pd.notnull(gia) and gia != '' else '0'
        
        html_content += f"""
                        <tr>
                            <td><strong>{ma}</strong></td>
                            <td>{ten}</td>
                            <td><span class="badge bg-light text-dark border">{dvt}</span></td>
                            <td class="text-danger fw-bold">{gia_fmt} ₫</td>
                            <td><span class="badge bg-info text-dark bg-opacity-10 border border-info">{qd}</span></td>
                            <td>{ngay}</td>
                        </tr>"""

    html_content += """
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="footer">
        <div class="container">
            <p>Hệ thống báo cáo tự động tích hợp GitHub Actions & Google Sheets.<br>
            Cập nhật tự động mỗi khi có thay đổi.</p>
        </div>
    </div>

    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/dataTables.bootstrap5.min.js"></script>
    <script>
        $(document).ready(function() {
            $('#dataTable').DataTable({
                "language": {
                    "url": "//cdn.datatables.net/plug-ins/1.13.6/i18n/vi.json"
                },
                "pageLength": 15,
                "order": [[ 5, "desc" ]]
            });
        });
    </script>
</body>
</html>"""

    # Write the file
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("Report generated successfully as index.html")

if __name__ == "__main__":
    generate_report()
