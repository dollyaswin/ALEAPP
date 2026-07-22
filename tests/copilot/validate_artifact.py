import os
import csv
import sys

# Tambahkan path root ALEAPP agar bisa import dari scripts.artifacts
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from scripts.artifacts.copilot import (
    copilot_account,
    copilot_sessions,
    copilot_sessions_conversation
)

def validate(ground_truth_csv, data_base_dir):
    print(f"{'Document':<40} | {'Expected':<10} | {'Actual':<10} | {'Status'}")
    print("-" * 75)
    
    total_tests = 0
    passed_tests = 0

    with open(ground_truth_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row.get('Dockument', '').strip()
            category = row.get('Category', '').strip()
            
            try:
                expected_count = int(row.get('Number of Artefact', 0))
            except ValueError:
                expected_count = 0

            # Cari path file (karena struktur mungkin berbeda, kita asumsikan 
            # file ada di suatu tempat di bawah data_base_dir)
            file_path = None
            for root, _, files in os.walk(data_base_dir):
                if filename in files:
                    file_path = os.path.join(root, filename)
                    break
            
            if not file_path:
                print(f"{filename:<40} | {expected_count:<10} | {'-':<10} | ERROR (File Not Found)")
                continue

            # Pilih fungsi yang sesuai berdasarkan kategori atau nama file
            func = None
            if category == 'Copilot Account' or 'accounts.xml' in filename:
                func = copilot_account
            elif category == 'Copilot Sessions' or 'offline_sessions.json' in filename:
                func = copilot_sessions
            elif category == 'Copilot Message' or 'offline_conv_' in filename:
                func = copilot_sessions_conversation
            else:
                print(f"{filename:<40} | {expected_count:<10} | {'-':<10} | ERROR (Unknown Category)")
                continue

            try:
                # Karena fungsi didekorasi dengan @artifact_processor, 
                # kita gunakan __wrapped__ agar langsung memanggil fungsi aslinya tanpa generate HTML report ALEAPP.
                original_func = getattr(func, '__wrapped__', func)
                
                # Fungsi asli mengharapkan (files_found, report_folder, seeker, wrap_text)
                headers, data_list, source_path = original_func([file_path], None, None, None)
                actual_count = len(data_list)
                
                if actual_count == expected_count:
                    status = "✅ PASS"
                    passed_tests += 1
                else:
                    status = "❌ FAIL"
                
                print(f"{filename:<40} | {expected_count:<10} | {actual_count:<10} | {status}")
            except Exception as e:
                print(f"{filename:<40} | {expected_count:<10} | {'-':<10} | ERROR ({str(e)})")
            
            total_tests += 1

    print("-" * 75)
    print(f"Total Tests: {total_tests}, Passed: {passed_tests}, Failed: {total_tests - passed_tests}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python validate_copilot.py <path_to_extracted_data_dir>")
        print("Example: python validate_copilot.py /data/data/com.microsoft.copilot")
        sys.exit(1)
        
    base_dir = sys.argv[1]
    csv_path = os.path.join(os.path.dirname(__file__), 'ground-truth', 'artifact.csv')
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV ground-truth tidak ditemukan di {csv_path}")
        sys.exit(1)
        
    validate(csv_path, base_dir)
