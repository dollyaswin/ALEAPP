import os
import csv
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from scripts.artifacts.copilot import copilot_account
from scripts.ilapfuncs import convert_unix_ts_to_utc

def validate_account_fields(ground_truth_csv, data_base_dir):
    # Dictionary untuk memetakan key dari CSV ke indeks kolom di hasil fungsi copilot_account
    # Headers asli: 
    # 0: Account ID, 1: Display Name, 2: First Name, 3: Last Name, 4: Email, 5: Login Name, 
    # 6: Account Type, 7: Birthday, 8: Location, 9: Realm Name, 10: Sovereignty, 11: Token Issued, 12: Token Expired
    field_mapping = {
        'id': 0,
        'display_name': 1,
        'first_name': 2,
        'last_name': 3,
        'email': 4,
        'login_name': 5,
        'account_type': 6,
        'birthday': 7,
        'location': 8,
        'realm_name': 9,
        'sovereignty': 10,
        'token_issued': 11,
        'token_expired': 12
    }

    expected_values = {}
    with open(ground_truth_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader) # Skip header (Field,Value)
        for row in reader:
            if not row: continue
            
            field = row[0].strip()
            # Memperbaiki typo di CSV ('birthday: 2007-09-01')
            if ':' in field and len(row) > 1 and row[1].strip() == '':
                parts = field.split(':', 1)
                field = parts[0].strip()
                val = parts[1].strip()
            else:
                val = row[1].strip() if len(row) > 1 else ''
            
            # Jika field adalah token, kita ubah format timestamp unix-nya ke UTC sesuai logika script utama
            if field in ['token_issued', 'token_expired'] and val.isdigit():
                val = str(convert_unix_ts_to_utc(int(val)))
                
            expected_values[field] = val

    # Cari file accounts.xml di base directory
    target_filename = 'com.microsoft.oneauth.accounts.xml'
    file_path = None
    for root, _, files in os.walk(data_base_dir):
        if target_filename in files:
            file_path = os.path.join(root, target_filename)
            break
            
    if not file_path:
        print(f"ERROR: File '{target_filename}' tidak ditemukan di {data_base_dir}")
        sys.exit(1)

    print(f"Memvalidasi fields menggunakan file: {file_path}")
    print("-" * 80)
    print(f"{'Field':<15} | {'Expected':<22} | {'Actual':<22} | {'Status'}")
    print("-" * 80)

    try:
        original_func = getattr(copilot_account, '__wrapped__', copilot_account)
        headers, data_list, source_path = original_func([file_path], None, None, None)
        
        if not data_list:
            print("ERROR: Tidak ada data yang berhasil diekstrak dari XML.")
            sys.exit(1)
            
        actual_row = data_list[0] # Ambil record pertama
        
        passed = 0
        total = len(expected_values)
        
        for field, expected_val in expected_values.items():
            if field not in field_mapping:
                continue
                
            col_idx = field_mapping[field]
            actual_val = str(actual_row[col_idx]).strip()
            
            if actual_val == expected_val:
                status = "✅ PASS"
                passed += 1
            else:
                status = "❌ FAIL"
                
            print(f"{field:<15} | {expected_val:<22} | {actual_val:<22} | {status}")
            
        print("-" * 80)
        print(f"Total Fields Validated: {total}, Passed: {passed}, Failed: {total - passed}")
        
    except Exception as e:
        print(f"ERROR saat menjalankan script: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python validate_account_fields.py <path_to_extracted_data_dir>")
        sys.exit(1)
        
    base_dir = sys.argv[1]
    csv_path = os.path.join(os.path.dirname(__file__), 'ground-truth', 'fields-account.csv')
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV ground-truth tidak ditemukan di {csv_path}")
        sys.exit(1)
        
    validate_account_fields(csv_path, base_dir)
