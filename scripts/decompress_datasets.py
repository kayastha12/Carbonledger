# Script to decompress dataset zip files for CarbonLedger
import os
import zipfile
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def decompress_directory(src_subpath, dest_subpath):
    src_dir = os.path.join(ROOT, src_subpath)
    dest_dir = os.path.join(ROOT, dest_subpath)
    
    if not os.path.exists(src_dir):
        print(f"Compressed directory {src_subpath} not found!")
        return
        
    os.makedirs(dest_dir, exist_ok=True)
    
    for f in os.listdir(src_dir):
        if f.endswith(".zip"):
            zip_file = os.path.join(src_dir, f)
            print(f"Decompressing {f} to {dest_subpath}...")
            try:
                with zipfile.ZipFile(zip_file, 'r') as z:
                    z.extractall(dest_dir)
            except Exception as e:
                print(f"[!] Error decompressing {f}: {e}")
                sys.exit(1)

def decompress_all():
    print("=" * 60)
    print("CarbonLedger Dataset Decompressor")
    print("=" * 60)
    
    print("\n[+] Decompressing master datasets...")
    decompress_directory("datasets/compressed/master", "datasets/output/master")
    
    print("\n[+] Decompressing transactional datasets...")
    decompress_directory("datasets/compressed/transactional", "datasets/output/transactional")
    
    print("\n" + "=" * 60)
    print("All datasets successfully decompressed.")
    print("=" * 60)

if __name__ == "__main__":
    decompress_all()
