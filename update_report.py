import pandas as pd
import json
import os
import glob
from datetime import datetime

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

def generate_report():
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
                # Read all sheets in the Excel file
                all_sheets = pd.read_excel(file_path, sheet_name=None, header=None)
                
                # Check each sheet for 'Số đơn hàng' or 'Mã Mặt Hàng' indicating Sales data
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
            'Nhóm Hàng': 'category',
            'Vùng miền': 'region',
            'Mã Mặt Hàng': 'product_code',
            'Tên Mặt Hàng': 'product_name',
            'Số Lượng': 'qty',
            'Ngày đặt hàng': 'date',
            'Tên KH': 'customer'
        }
        
        # Rename columns that exist
        for col, new_col in required_cols.items():
            if col in df.columns:
                df.rename(columns={col: new_col}, inplace=True)
            else:
                # Add missing columns with empty/0 to prevent crashes
                df[new_col] = 0 if new_col in ['revenue', 'weight', 'qty'] else ""
                
        # Clean data types
        df['revenue'] = pd.to_numeric(df['revenue'], errors='coerce').fillna(0)
        df['weight'] = pd.to_numeric(df['weight'], errors='coerce').fillna(0)
        df['qty'] = pd.to_numeric(df['qty'], errors='coerce').fillna(0)
        df['order_id'] = df['order_id'].astype(str)
        
        # Calculate KPIs
        total_revenue = df['revenue'].sum()
        total_weight = df['weight'].sum()
        total_orders = df['order_id'].nunique()
        
        # Success rate (orders closed)
        order_status = df.groupby('order_id')['status'].first()
        closed_orders = len(order_status[order_status.str.upper().str.contains('CLOSE', na=False)])
        success_rate = round((closed_orders / total_orders * 100) if total_orders > 0 else 0, 1)
        
        # Chart data - Category
        cat_rev = df.groupby('category')['revenue'].sum().sort_values(ascending=False).head(10)
        
        # Chart data - Region
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
        
        # Top Products Table
        top_products = df.groupby(['product_code', 'product_name'])[['qty', 'revenue']].sum().reset_index()
        top_products = top_products.sort_values('revenue', ascending=False).head(10)
        
        top_products_tbody = ""
        for _, row in top_products.iterrows():
            top_products_tbody += f"<tr><td><strong>{row['product_code']}</strong></td><td>{row['product_name']}</td><td class='text-right'>{format_money_str(row['qty'])}</td><td class='text-right font-semibold' style='color:var(--primary)'>{format_money_str(row['revenue'])}</td></tr>\n"
            
        # Recent Orders Table
        try:
            df['date_dt'] = pd.to_datetime(df['date'], errors='coerce')
            recent_orders = df.sort_values('date_dt', ascending=False).drop_duplicates(subset=['order_id']).head(10)
        except:
            recent_orders = df.drop_duplicates(subset=['order_id']).tail(10).iloc[::-1]
            
        recent_orders_tbody = ""
        for _, row in recent_orders.iterrows():
            date_str = str(row['date'])
            if len(date_str) > 10: date_str = date_str[:10]
            
            recent_orders_tbody += f"<tr><td>{date_str}</td><td><strong>{row['order_id']}</strong></td><td>{row['customer']}</td><td>{get_badge(row['status'])}</td><td class='text-right font-semibold'>{format_money_str(row['revenue'])}</td></tr>\n"

        current_time = datetime.now().strftime('%d/%m/%Y %H:%M')
        
    except Exception as e:
        print(f"Error processing data: {e}")
        return

    # Read template and replace
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
            
        template = template.replace('{{TOTAL_REVENUE}}', format_money_str(total_revenue))
        template = template.replace('{{TOTAL_ORDERS}}', format_money_str(total_orders))
        template = template.replace('{{TOTAL_WEIGHT}}', format_money_str(total_weight))
        template = template.replace('{{SUCCESS_RATE}}', str(success_rate))
        
        template = template.replace('{{DATE_TIME}}', current_time)
        template = template.replace('{{TOP_PRODUCTS_TBODY}}', top_products_tbody)
        template = template.replace('{{RECENT_ORDERS_TBODY}}', recent_orders_tbody)
        
        template = template.replace('{{CHART_DATA_JSON}}', json.dumps(chart_data, ensure_ascii=False, cls=NpEncoder))
        
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(template)
            
        print("Successfully generated Sales Dashboard index.html from template!")
    except Exception as e:
        print(f"Error writing template: {e}")

if __name__ == "__main__":
    generate_report()
