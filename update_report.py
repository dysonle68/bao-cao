import pandas as pd
import json
import os
from datetime import datetime
import math

def generate_report():
    # URL of the Google Sheet (Excel format)
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
            df.columns = df.iloc[header_row_idx]
            df = df.iloc[header_row_idx+1:].reset_index(drop=True)
        else:
            print("Cannot find header row with 'Mã hàng'")
            return

        # Clean up column names
        df.columns = [str(c).strip() if pd.notnull(c) else f"Unnamed_{i}" for i, c in enumerate(df.columns)]
        
        # Keep relevant columns and drop rows with empty 'Mã hàng'
        cols_map = {
            'Mã hàng': 'code',
            'tên hàng': 'name',
            'ĐVT': 'dvt',
            'Giá bán': 'price',
            'VAT': 'vat',
            'Quyết định': 'qd',
            'ngày': 'date',
            'BU BÁN': 'bu_ban',
            'BU MUA': 'bu_mua'
        }
        
        available_cols = [c for c in cols_map.keys() if c in df.columns]
        df = df[available_cols].dropna(subset=['Mã hàng']).copy()
        
        # Rename columns to standardized keys
        df.rename(columns=cols_map, inplace=True)
        
        # Clean up columns
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.strftime('%d/%m/%Y').fillna('')
            
        if 'price' in df.columns:
            df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
            
        if 'vat' in df.columns:
            df['vat'] = pd.to_numeric(df['vat'], errors='coerce').fillna(0)
            
        # Extract categories (example heuristic, can be customized)
        def get_category(name):
            name_lower = str(name).lower()
            if 'pp' in name_lower: return 'Dây PP'
            if 'pe' in name_lower: return 'Dây PE'
            if 'polyester' in name_lower: return 'Polyester'
            if 'multi' in name_lower: return 'Multi'
            if 'nylon' in name_lower: return 'Nylon'
            if 'sisal' in name_lower: return 'Sisal'
            if 'jute' in name_lower or 'đay' in name_lower: return 'Dây Đay (Jute)'
            return 'Khác'
            
        df['cat'] = df['name'].apply(get_category)
        
        # Calculate KPIs
        total_sku = len(df)
        avg_price = df['price'].mean() if total_sku > 0 else 0
        min_price = df['price'].min() if total_sku > 0 else 0
        max_price = df['price'].max() if total_sku > 0 else 0
        
        vat_8 = len(df[abs(df['vat'] - 0.08) < 0.001])
        vat_5 = len(df[abs(df['vat'] - 0.05) < 0.001])
        vat_0 = len(df[df['vat'] < 0.01])
        vat_percent = (vat_8 / total_sku * 100) if total_sku > 0 else 0
        
        df['qd_str'] = df['qd'].fillna('Chưa có QĐ').astype(str)
        qd_counts = df['qd_str'].value_counts()
        total_qd = len(qd_counts)
        top_qd = qd_counts.index[0] if len(qd_counts) > 0 else 'N/A'
        top_qd_count = qd_counts.values[0] if len(qd_counts) > 0 else 0
        
        cn2_df = df[df['bu_ban'].astype(str).str.contains('CN2', na=False, case=False)]
        cty_df = df[df['bu_mua'].astype(str).str.contains('CTY', na=False, case=False)]
        cn2_count = len(cn2_df)
        cty_count = len(cty_df)
        
        cat_counts = df['cat'].value_counts()
        total_cat = len(cat_counts)
        
        # Prepare datasets
        dataset = df.to_dict(orient='records')
        for i, row in enumerate(dataset):
            row['id'] = i + 1
            for k, v in row.items():
                if isinstance(v, float) and math.isnan(v):
                    row[k] = ""
                    
        # Charts Data
        chart_data = {
            'cat': {
                'labels': list(cat_counts.index),
                'data': list(cat_counts.values)
            },
            'price': {
                'labels': ['Dưới 30k', '30k - 40k', '40k - 50k', '50k - 70k', '70k - 100k', 'Trên 100k'],
                'data': [
                    len(df[df['price'] < 30000]),
                    len(df[(df['price'] >= 30000) & (df['price'] < 40000)]),
                    len(df[(df['price'] >= 40000) & (df['price'] < 50000)]),
                    len(df[(df['price'] >= 50000) & (df['price'] < 70000)]),
                    len(df[(df['price'] >= 70000) & (df['price'] < 100000)]),
                    len(df[df['price'] >= 100000])
                ]
            },
            'vat': {
                'labels': ['8%', '5%', '0% / Khác'],
                'data': [vat_8, vat_5, vat_0]
            },
            'top_qd': {
                'labels': list(qd_counts.head(8).index),
                'data': list(int(v) for v in qd_counts.head(8).values)
            },
            'top_price': {
                'labels': list(df.nlargest(8, 'price')['code'].values),
                'data': list(float(v) for v in df.nlargest(8, 'price')['price'].values)
            }
        }
        
        # Generate HTML rows
        def get_vat_badge(v):
            if abs(v - 0.08) < 0.001: return '<span class="badge badge-vat-8">8%</span>'
            if abs(v - 0.05) < 0.001: return '<span class="badge badge-vat-5">5%</span>'
            return '<span class="badge badge-vat-0">0%</span>'

        cn2_tbody = ""
        for i, row in enumerate(cn2_df.itertuples()):
            cn2_tbody += f'<tr><td>{i+1}</td><td><strong>{getattr(row, "code", "")}</strong></td><td>{getattr(row, "name", "")}</td><td><span class="badge" style="background:var(--bg-body);">{getattr(row, "dvt", "")}</span></td><td class="price-text">{int(getattr(row, "price", 0)):,} VNĐ</td><td>{get_vat_badge(getattr(row, "vat", 0))}</td><td>{getattr(row, "qd", "")}</td><td>{getattr(row, "date", "")}</td></tr>\n'

        cty_tbody = ""
        for i, row in enumerate(cty_df.itertuples()):
            cty_tbody += f'<tr><td>{i+1}</td><td><strong>{getattr(row, "code", "")}</strong></td><td>{getattr(row, "name", "")}</td><td><span class="badge" style="background:var(--bg-body);">{getattr(row, "dvt", "")}</span></td><td class="price-text">{int(getattr(row, "price", 0)):,} VNĐ</td><td>{get_vat_badge(getattr(row, "vat", 0))}</td><td>{getattr(row, "qd", "")}</td><td>{getattr(row, "date", "")}</td></tr>\n'

        qd_tbody = ""
        for i, (qd_name, count) in enumerate(qd_counts.items()):
            qd_df = df[df['qd_str'] == qd_name]
            qd_tbody += f'<tr><td>{i+1}</td><td><strong>{qd_name}</strong></td><td>-</td><td><span class="badge badge-cat">{count} SKU</span></td><td>{int(qd_df["price"].min()):,} VNĐ</td><td>{int(qd_df["price"].max()):,} VNĐ</td><td class="price-text">{int(qd_df["price"].mean()):,} VNĐ</td></tr>\n'

        cat_tbody = ""
        cat_options = ""
        for i, (cat_name, count) in enumerate(cat_counts.items()):
            cat_df = df[df['cat'] == cat_name]
            cat_options += f'<option value="{cat_name}">{cat_name} ({count})</option>\n'
            cat_tbody += f'<tr><td>{i+1}</td><td><strong>{cat_name}</strong></td><td><span class="badge badge-cat">{count} SKU</span></td><td><strong>{count/total_sku*100:.1f}%</strong></td><td>{int(cat_df["price"].min()):,} VNĐ</td><td>{int(cat_df["price"].max()):,} VNĐ</td><td class="price-text">{int(cat_df["price"].mean()):,} VNĐ</td></tr>\n'
            
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
            
        template = template.replace('{{TOTAL_SKU}}', f'{total_sku}')
        template = template.replace('{{AVG_PRICE}}', f'{int(avg_price):,}')
        template = template.replace('{{PRICE_RANGE}}', f'{int(min_price):,} - {int(max_price):,}')
        template = template.replace('{{VAT_COUNTS}}', f'{vat_8} <span style="font-size:15px; font-weight:600;">(8%)</span> / {vat_5} <span style="font-size:15px; font-weight:600;">(5%)</span>')
        template = template.replace('{{VAT_PERCENT}}', f'{vat_percent:.1f}% áp dụng VAT 8%')
        template = template.replace('{{TOTAL_QD}}', f'{total_qd}')
        template = template.replace('{{TOP_QD_TEXT}}', f'QĐ {top_qd} lớn nhất ({top_qd_count} SKU)')
        template = template.replace('{{DATE_TIME}}', current_time)
        
        template = template.replace('{{CN2_COUNT}}', f'{cn2_count}')
        template = template.replace('{{CTY_COUNT}}', f'{cty_count}')
        template = template.replace('{{TOTAL_CAT}}', f'{total_cat}')
        
        template = template.replace('{{CAT_OPTIONS}}', cat_options)
        
        template = template.replace('{{CN2_TBODY}}', cn2_tbody)
        template = template.replace('{{CTY_TBODY}}', cty_tbody)
        template = template.replace('{{QD_TBODY}}', qd_tbody)
        template = template.replace('{{CAT_TBODY}}', cat_tbody)
        
        template = template.replace('{{DATASET_JSON}}', json.dumps(dataset, ensure_ascii=False, cls=NpEncoder))
        template = template.replace('{{CHART_DATA_JSON}}', json.dumps(chart_data, ensure_ascii=False, cls=NpEncoder))
        
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(template)
            
        print("Successfully generated index.html from template!")
    except Exception as e:
        print(f"Error writing template: {e}")

if __name__ == "__main__":
    generate_report()
