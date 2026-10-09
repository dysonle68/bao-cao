import pandas as pd
import json
import os
import glob
from datetime import datetime
import argparse

def format_money(val):
    try:
        if pd.isna(val): return 0
        return int(float(val))
    except:
        return 0

def format_money_str(val):
    return f"{format_money(val):,}"

def get_badge(status):
    status = str(status).upper()
    if 'CLOSE' in status:
        return f'<span class="badge badge-closed">{status}</span>'
    elif 'OPEN' in status:
        return f'<span class="badge badge-open">{status}</span>'
    return f'<span class="badge badge-other">{status}</span>'

def generate_report(month=8, year=2026, output_file='BAO-CAO-T8.HTML'):
    data_dir = 'data'
    
    try:
        excel_files = glob.glob(os.path.join(data_dir, '*.xlsx'))
        if not excel_files:
            print(f"No Excel files found in {data_dir}")
            return
            
        excel_files.sort(key=os.path.getmtime, reverse=True)
        
        df = None
        header_row_idx = None
        used_file = None
        
        for file_path in excel_files:
            print(f"Checking file: {file_path}")
            try:
                all_sheets = pd.read_excel(file_path, sheet_name=None, header=None)
                
                for sheet_name, temp_df in all_sheets.items():
                    for idx, row in temp_df.iterrows():
                        if 'Số đơn hàng' in row.values or 'Mã Mặt Hàng' in row.values:
                            header_row_idx = idx
                            df = temp_df
                            used_file = f"{file_path} (Sheet: {sheet_name})"
                            break
                    if header_row_idx is not None:
                        break
            except Exception as e:
                print(f"Failed to read {file_path}: {e}")
                
            if header_row_idx is not None:
                break
                
        if header_row_idx is not None:
            print(f"Found valid Sales data in: {used_file}")
            df.columns = df.iloc[header_row_idx]
            df = df.iloc[header_row_idx+1:].reset_index(drop=True)
        else:
            print("Cannot find Sales Data header row in any Excel files")
            return

        # Clean column names
        df.columns = [str(c).strip() if pd.notnull(c) else f"Unnamed_{i}" for i, c in enumerate(df.columns)]
        
        # Ensure correct column names
        required_cols = {
            'Thành Tiền (+VAT) Amount': 'revenue',
            'Số đơn hàng': 'order_id',
            'Số Khối Lượng Chuẩn': 'weight',
            'Trạng thái đơn hàng': 'status',
            'Trạng thái Line': 'line_status',
            'Nhóm Hàng': 'category',
            'Vùng miền': 'region',
            'Mã Mặt Hàng': 'product_code',
            'Tên Mặt Hàng': 'product_name',
            'Số Lượng': 'qty',
            'Đơn Giá': 'unit_price',
            'Ngày Xuất Hàng': 'date',
            'Tên KH': 'customer',
            'Công ty': 'company',
            'Nhóm KH': 'customer_group'
        }
        
        for col, new_col in required_cols.items():
            if col in df.columns:
                df.rename(columns={col: new_col}, inplace=True)
            else:
                df[new_col] = 0 if new_col in ['revenue', 'weight', 'qty', 'unit_price'] else ""
                
        df['revenue'] = pd.to_numeric(df['revenue'], errors='coerce').fillna(0)
        df['weight'] = pd.to_numeric(df['weight'], errors='coerce').fillna(0)
        df['qty'] = pd.to_numeric(df['qty'], errors='coerce').fillna(0)
        df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce').fillna(0)
        df['order_id'] = df['order_id'].astype(str)
        df['company'] = df['company'].astype(str).str.strip()
        df['customer_group'] = df['customer_group'].astype(str).str.strip()
        
        # Calculate success rate BEFORE filtering out OPEN orders
        df['date_dt'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
        if year:
            df = df[df['date_dt'].dt.year == year]
        if month:
            df = df[df['date_dt'].dt.month == month]
            
        total_orders_all = df['order_id'].nunique()
        closed_mask = df['line_status'].astype(str).str.upper() == 'CLOSED'
        closed_orders_all = df[closed_mask]['order_id'].nunique()
        success_rate = round((closed_orders_all / total_orders_all * 100) if total_orders_all > 0 else 0, 1)

        # ONLY KEEP CLOSED ORDERS
        df = df[closed_mask].copy()
        
        # Fetch dynamic VCB exchange rates
        import requests
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        vcb_rates = {}
        def get_vcb_rate(date_obj):
            if pd.isnull(date_obj):
                return 25400
            date_str = date_obj.strftime('%Y-%m-%d')
            if date_str in vcb_rates:
                return vcb_rates[date_str]
            try:
                url = f'https://www.vietcombank.com.vn/api/exchangerates?date={date_str}'
                res = requests.get(url, verify=False, timeout=10)
                data = res.json()
                for item in data.get('Data', []):
                    if item.get('currencyCode') == 'USD':
                        rate = float(item.get('transfer', 25400))
                        vcb_rates[date_str] = rate
                        return rate
            except Exception:
                pass
            vcb_rates[date_str] = 25400
            return 25400

        # Convert USD to VND for specific export orders
        mask = (df['customer_group'] == 'Xuat Khau') & (df['unit_price'] < 1000)
        
        for idx in df[mask].index:
            rate = get_vcb_rate(df.loc[idx, 'date_dt'])
            df.loc[idx, 'revenue'] = df.loc[idx, 'qty'] * df.loc[idx, 'unit_price'] * rate
        
        df_all = df.copy()

        # Define internal mask
        internal_mask = df_all['customer'].astype(str).str.contains('SIAM', case=False, na=False) | \
                        (df_all['customer_group'].astype(str).str.strip() == 'Noi Bo')

        # Gross metrics
        gross_rev = df_all['revenue'].sum()
        gross_lines = len(df_all)

        # Internal metrics
        internal_rev = df_all[internal_mask]['revenue'].sum()

        # Net metrics (Thực tế ngoài)
        df_net = df_all[~internal_mask].copy()
        
        # Override df with df_net so charts use Net metrics
        df = df_net
        
        net_rev = df['revenue'].sum()
        net_lines = len(df)
        net_customers = df['customer'].nunique()
        net_skus = df['product_code'].nunique()
        
        if df.empty:
            print(f"No data found for {month}/{year}")
            
        total_revenue = net_rev
        total_weight = df['weight'].sum()
        total_orders = df['order_id'].nunique()
            
        cat_rev = df.groupby('category')['revenue'].sum().sort_values(ascending=False).head(10)
        region_rev = df.groupby('region')['revenue'].sum().sort_values(ascending=False)
        
        chart_data = {
            'category': {
                'labels': list(cat_rev.index.astype(str)),
                'data': list(float(v) for v in cat_rev.values)
            },
            'region': {
                'labels': list(region_rev.index.astype(str)),
                'data': list(float(v) for v in region_rev.values)
            }
        }
        
        top_products = df.groupby(['product_code', 'product_name'])[['qty', 'revenue']].sum().reset_index()
        top_products = top_products.sort_values('revenue', ascending=False).head(10)
        
        top_products_tbody = ""
        for _, row in top_products.iterrows():
            top_products_tbody += f"<tr><td><strong>{row['product_code']}</strong></td><td>{row['product_name']}</td><td class='text-right'>{format_money_str(row['qty'])}</td><td class='text-right font-semibold' style='color:var(--primary)'>{format_money_str(row['revenue'])}</td></tr>\n"
            
        recent_orders = df.sort_values('date_dt', ascending=False).drop_duplicates(subset=['order_id']).head(10)
            
        recent_orders_tbody = ""
        for _, row in recent_orders.iterrows():
            date_str = str(row['date'])
            if len(date_str) > 10: date_str = date_str[:10]
            
            recent_orders_tbody += f"<tr><td>{date_str}</td><td><strong>{row['order_id']}</strong></td><td>{row['customer']}</td><td>{get_badge(row['status'])}</td><td class='text-right font-semibold'>{format_money_str(row['revenue'])}</td></tr>\n"

        current_time = datetime.now().strftime('%d/%m/%Y %H:%M')
        
    except Exception as e:
        print(f"Error processing data: {e}")
        return

    try:
        class NpEncoder(json.JSONEncoder):
            def default(self, obj):
                import numpy as np
                if isinstance(obj, np.integer):
                    return int(obj)
                if isinstance(obj, np.floating):
                    return float(obj)
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                return super(NpEncoder, self).default(obj)

        with open('template.html', 'r', encoding='utf-8') as f:
            template = f.read()
            
        # Update Title to show specific month
        if month:
            template = template.replace('Sales Dashboard (Đơn Hàng)', f'Báo Cáo Doanh Thu Tháng {month}/{year}')
        else:
            template = template.replace('Sales Dashboard (Đơn Hàng)', f'Báo Cáo Tổng Doanh Thu Năm {year}')
        
        template = template.replace('{{NET_REVENUE}}', format_money_str(net_rev))
        template = template.replace('{{TOTAL_ORDERS}}', format_money_str(total_orders))
        template = template.replace('{{TOTAL_WEIGHT}}', format_money_str(total_weight))
        template = template.replace('{{SUCCESS_RATE}}', str(success_rate))
        
        template = template.replace('{{GROSS_REVENUE}}', format_money_str(gross_rev))
        template = template.replace('{{INTERNAL_REVENUE}}', format_money_str(internal_rev))
        template = template.replace('{{GROSS_LINES}}', format_money_str(gross_lines))
        template = template.replace('{{NET_LINES}}', format_money_str(net_lines))
        template = template.replace('{{NET_CUSTOMERS}}', format_money_str(net_customers))
        template = template.replace('{{NET_SKUS}}', format_money_str(net_skus))
        
        template = template.replace('{{DATE_TIME}}', current_time)
        template = template.replace('{{TOP_PRODUCTS_TBODY}}', top_products_tbody)
        template = template.replace('{{RECENT_ORDERS_TBODY}}', recent_orders_tbody)
        
        template = template.replace('{{CHART_DATA_JSON}}', json.dumps(chart_data, ensure_ascii=False, cls=NpEncoder))
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(template)
            
        print(f"Successfully generated Sales Dashboard {output_file} from template!")
    except Exception as e:
        print(f"Error writing template: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate Monthly Sales Report')
    parser.add_argument('--month', type=int, default=8, help='Month to filter (e.g. 8)')
    parser.add_argument('--year', type=int, default=2026, help='Year to filter (e.g. 2026)')
    parser.add_argument('--output', type=str, default='BAO-CAO-T8.HTML', help='Output file name')
    
    args = parser.parse_args()
    generate_report(month=args.month, year=args.year, output_file=args.output)
