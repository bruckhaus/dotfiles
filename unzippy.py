#!/usr/bin/env python3

import os
import sys
import zipfile
import argparse
from collections import defaultdict
import humanize
from tabulate import tabulate
import shutil
import hashlib
import magic
import logging
from tqdm import tqdm

def setup_logging(zip_path):
    log_file = f"{os.path.splitext(zip_path)[0]}.log"
    logging.basicConfig(filename=log_file, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

def unzip_file(zip_path, target_dir, max_info_lines, test_mode=False):
    setup_logging(zip_path)
    logging.info(f"Starting to process: {zip_path}")
    print(f"\nProcessing: {zip_path}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            total_size = sum(file.file_size for file in zip_ref.infolist())
            with tqdm(total=total_size, unit='B', unit_scale=True, desc="Extracting") as pbar:
                for file in zip_ref.infolist():
                    zip_ref.extract(file, target_dir)
                    pbar.update(file.file_size)
    except zipfile.BadZipFile:
        logging.error(f"Error: {zip_path} is not a valid zip file.")
        print(f"Error: {zip_path} is not a valid zip file.")
        return
    except Exception as e:
        logging.error(f"Error extracting {zip_path}: {str(e)}")
        print(f"Error extracting {zip_path}: {str(e)}")
        return
    
    extracted_info = analyze_extracted_content(target_dir, zip_path)
    display_info(extracted_info, max_info_lines)
    
    if all(extracted_info['success_indicators']):
        if not test_mode and input("Zip file successfully extracted. Delete the original zip file? (y/n): ").lower() == 'y':
            os.remove(zip_path)
            print(f"Deleted: {zip_path}")
            logging.info(f"Deleted original zip file: {zip_path}")
    
    if test_mode:
        print("Test mode: Cleaning up extracted files...")
        shutil.rmtree(target_dir)
        logging.info(f"Test mode: Cleaned up extracted files in {target_dir}")

def analyze_extracted_content(target_dir, zip_path):
    info = {
        'total_files': 0,
        'total_folders': 0,
        'file_types': defaultdict(int),
        'total_size': 0,
        'largest_file': ('', 0),
        'success_indicators': [True, True, True],  # [files_extracted, no_errors, size_match]
        'checksums': {}
    }
    
    for root, dirs, files in os.walk(target_dir):
        info['total_folders'] += len(dirs)
        for file in tqdm(files, desc="Analyzing files", unit="file"):
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            file_type = magic.from_file(file_path, mime=True)
            
            info['total_files'] += 1
            info['file_types'][file_type] += 1
            info['total_size'] += file_size
            
            if file_size > info['largest_file'][1]:
                info['largest_file'] = (file, file_size)
            
            # Calculate checksum
            with open(file_path, "rb") as f:
                file_hash = hashlib.md5()
                for chunk in iter(lambda: f.read(4096), b""):
                    file_hash.update(chunk)
            info['checksums'][file] = file_hash.hexdigest()
    
    # Check success indicators
    info['success_indicators'][0] = info['total_files'] > 0
    info['success_indicators'][1] = True  # Assume no errors unless we implement error checking
    
    zip_size = os.path.getsize(zip_path)
    info['success_indicators'][2] = abs(zip_size - info['total_size']) / zip_size < 0.1  # Allow 10% difference
    
    # Calculate compression ratio
    info['compression_ratio'] = zip_size / info['total_size'] if info['total_size'] > 0 else 0
    
    return info

def display_info(info, max_info_lines):
    print("\nExtracted Content Summary:")
    print(f"Total Files: {info['total_files']}")
    print(f"Total Folders: {info['total_folders']}")
    print(f"Total Size: {humanize.naturalsize(info['total_size'])}")
    print(f"Largest File: {info['largest_file'][0]} ({humanize.naturalsize(info['largest_file'][1])})")
    print(f"Compression Ratio: {info['compression_ratio']:.2f}x ({humanize.naturalsize(info['total_size'])} -> {humanize.naturalsize(info['total_size']/info['compression_ratio'])})")
    
    file_type_info = [(type, count) for type, count in info['file_types'].items()]
    file_type_info.sort(key=lambda x: x[1], reverse=True)
    
    if len(file_type_info) + 5 <= max_info_lines:  # +5 for the summary lines above
        print("\nFile Types:")
        print(tabulate(file_type_info, headers=['Type', 'Count'], tablefmt='pretty'))
    else:
        print(f"\nTop {max_info_lines - 5} File Types:")
        print(tabulate(file_type_info[:max_info_lines - 5], headers=['Type', 'Count'], tablefmt='pretty'))
    
    print("\nChecksums:")
    for file, checksum in list(info['checksums'].items())[:5]:  # Show first 5 checksums
        print(f"{file}: {checksum}")
    if len(info['checksums']) > 5:
        print(f"... and {len(info['checksums']) - 5} more")

def main():
    parser = argparse.ArgumentParser(description="Unzip helper for macOS")
    parser.add_argument('-m', '--max_lines', type=int, default=40, help='Maximum number of info lines to display')
    parser.add_argument('-t', '--target', default=os.getcwd(), help='Target directory for extraction')
    parser.add_argument('-f', '--file', help='Specific zip file to process')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no deletion, cleanup after extraction)')
    args = parser.parse_args()

    if args.file:
        if not os.path.exists(args.file) or not args.file.endswith('.zip'):
            print(f"Error: {args.file} is not a valid zip file.")
            sys.exit(1)
        zip_files = [args.file]
    else:
        zip_files = [f for f in os.listdir() if f.endswith('.zip')]
    
    if not zip_files:
        print("No zip files found to process.")
        sys.exit(0)
    
    for zip_file in zip_files:
        unzip_file(zip_file, args.target, args.max_lines, args.test)
    
    print("\nAll zip files processed.")

if __name__ == "__main__":
    main()

