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
import tempfile
from pathlib import Path
import zlib
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from rich.tree import Tree

console = Console()

def setup_logging(zip_path):
    log_file = f"{os.path.splitext(zip_path)[0]}.log"
    logging.basicConfig(filename=log_file, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

def safe_delete_file(file_path):
    try:
        file_path = Path(file_path).resolve()
        if not file_path.is_file():
            print(f"Warning: {file_path} is not a file. Skipping deletion.")
            return False
        
        os.remove(file_path)
        print(f"Deleted: {file_path}")
        logging.info(f"Deleted file: {file_path}")
        return True
    except Exception as e:
        print(f"Error deleting {file_path}: {str(e)}")
        logging.error(f"Error deleting {file_path}: {str(e)}")
        return False

def display_info(info, max_info_lines, test_mode=False):
    summary = Table(title="Extracted Content Summary", show_header=False, expand=False)
    summary.add_column("Attribute", style="cyan")
    summary.add_column("Value", style="magenta")
    
    summary.add_row("Total Files", str(info['total_files']))
    summary.add_row("Total Folders", str(info['total_folders']))
    summary.add_row("Total Size", humanize.naturalsize(info['total_size']))
    summary.add_row("Largest File", f"{info['largest_file'][0]} ({humanize.naturalsize(info['largest_file'][1])})")
    
    compression_ratio = info['zip_size'] / info['total_size'] if info['total_size'] > 0 else 1
    summary.add_row("Compression Ratio", f"{compression_ratio:.2f}x ({humanize.naturalsize(info['total_size'])} -> {humanize.naturalsize(info['zip_size'])})")
    
    console.print(summary)
    
    file_type_info = [(type, count) for type, count in info['file_types'].items()]
    file_type_info.sort(key=lambda x: x[1], reverse=True)
    
    if len(file_type_info) + 5 <= max_info_lines:
        file_types_table = Table(title="File Types", show_header=True, expand=False)
        file_types_table.add_column("Type", style="cyan")
        file_types_table.add_column("Count", style="magenta", justify="right")
        for file_type, count in file_type_info:
            file_types_table.add_row(file_type, str(count))
        console.print(file_types_table)
    else:
        file_types_table = Table(title=f"Top {max_info_lines - 5} File Types", show_header=True, expand=False)
        file_types_table.add_column("Type", style="cyan")
        file_types_table.add_column("Count", style="magenta", justify="right")
        for file_type, count in file_type_info[:max_info_lines - 5]:
            file_types_table.add_row(file_type, str(count))
        console.print(file_types_table)
    
    checksum_info = list(info['checksums'].items())
    matching_checksums = sum(1 for _, checksums in checksum_info if checksums['zip'] == checksums['extracted'])
    mismatched_checksums = len(checksum_info) - matching_checksums
    
    checksum_panel = Panel(
        f"Total files checked: {len(checksum_info)}\n"
        f"Matching checksums: [green]{matching_checksums}[/green]\n"
        f"Mismatched checksums: [red]{mismatched_checksums}[/red]",
        title="Checksum Comparison",
        expand=False
    )
    console.print(checksum_panel)
    
    if mismatched_checksums > 0:
        mismatch_tree = Tree("Mismatched files:")
        for file, checksums in checksum_info:
            if checksums['zip'] != checksums['extracted']:
                file_node = mismatch_tree.add(file)
                file_node.add(f"Zip CRC-32:       {checksums['zip']:08X}")
                file_node.add(f"Extracted CRC-32: {checksums['extracted']:08X}")
        console.print(mismatch_tree)
    
    success_panel = Panel(
        "\n".join(f"{indicator.replace('_', ' ').capitalize()}: {'[green]✓[/green]' if status else '[red]✗[/red]'}" 
                  for indicator, status in info['success_indicators'].items()),
        title="Success Indicators",
        expand=False
    )
    console.print(success_panel)
    
    if test_mode:
        console.print(f"\n[yellow]Test mode:[/yellow] Extracted content is in {info['extraction_dir']}")
        console.print("You can inspect the contents and then delete this directory manually.")

def show_deletion_summary(zip_path, extraction_dir):
    summary = Table(title="Deletion Summary", show_header=False, expand=False)
    summary.add_column("Item", style="cyan")
    summary.add_column("Details", style="magenta")
    
    summary.add_row("Original zip file to be deleted", str(zip_path))
    summary.add_row("Extracted content location", str(extraction_dir))
    
    file_count = sum(len(files) for _, _, files in os.walk(extraction_dir))
    dir_count = sum(len(dirs) for _, dirs, _ in os.walk(extraction_dir))
    
    summary.add_row("Files to be kept", str(file_count))
    summary.add_row("Directories to be kept", str(dir_count))
    
    console.print(Panel(summary, title="Deletion Summary", expand=False))

def unzip_file(zip_path, target_dir, max_info_lines, test_mode=False):
    zip_name = Path(zip_path).stem  # Get the zip file name without extension
    
    if test_mode:
        # Create a 'unzippy_test' directory in the current working directory
        test_dir = Path.cwd() / "unzippy_test"
        test_dir.mkdir(exist_ok=True)
        
        # Create a subdirectory for this specific zip file
        extraction_dir = test_dir / zip_name
        console.print(f"Test mode: Extracting to {extraction_dir}")
    else:
        extraction_dir = Path(target_dir) / zip_name
    
    extraction_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            total_size = sum(file.file_size for file in zip_ref.infolist())
            with tqdm(total=total_size, unit='B', unit_scale=True, desc="Extracting") as pbar:
                for file in zip_ref.infolist():
                    zip_ref.extract(file, extraction_dir)
                    pbar.update(file.file_size)
    except zipfile.BadZipFile:
        logging.error(f"Error: {zip_path} is not a valid zip file.")
        print(f"Error: {zip_path} is not a valid zip file.")
        return
    except Exception as e:
        logging.error(f"Error extracting {zip_path}: {str(e)}")
        print(f"Error extracting {zip_path}: {str(e)}")
        return
    
    extracted_info = analyze_extracted_content(extraction_dir, zip_path)
    extracted_info['extraction_dir'] = extraction_dir
    display_info(extracted_info, max_info_lines, test_mode)
    
    if all(extracted_info['success_indicators'].values()):
        show_deletion_summary(zip_path, extraction_dir)
        
        if not test_mode:
            confirmation = console.input("\nDo you want to proceed with deleting the original zip file? (yes/no): ").strip().lower()
            if confirmation == 'yes':
                safe_delete_file(zip_path)
            else:
                console.print("[yellow]Deletion cancelled.[/yellow]")
        else:
            console.print("\n[yellow]Test mode: Simulated deletion:[/yellow]")
            console.print(f"  Would delete zip file: [cyan]{zip_path}[/cyan]")
            console.print(f"  Extracted content would remain in: [cyan]{extraction_dir}[/cyan]")
    else:
        console.print("\n[red]Extraction was not fully successful. Deletion skipped.[/red]")
        console.print("Reasons:")
        if not extracted_info['success_indicators']['files_extracted']:
            console.print("- No files were extracted")
        if not extracted_info['success_indicators']['no_errors']:
            console.print("- Errors occurred during extraction")
    
    return extraction_dir

def _process_zip(zip_path, target_dir, max_info_lines, test_mode=False):
    temp_dir = None
    try:
        if test_mode:
            temp_dir = tempfile.mkdtemp()
            print(f"Test mode: Using temporary directory {temp_dir}")
            extraction_dir = os.path.join(temp_dir, os.path.splitext(os.path.basename(zip_path))[0])
        else:
            extraction_dir = os.path.join(target_dir, os.path.splitext(os.path.basename(zip_path))[0])
        
        os.makedirs(extraction_dir, exist_ok=True)
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                total_size = sum(file.file_size for file in zip_ref.infolist())
                with tqdm(total=total_size, unit='B', unit_scale=True, desc="Extracting") as pbar:
                    for file in zip_ref.infolist():
                        zip_ref.extract(file, extraction_dir)
                        pbar.update(file.file_size)
        except zipfile.BadZipFile:
            logging.error(f"Error: {zip_path} is not a valid zip file.")
            print(f"Error: {zip_path} is not a valid zip file.")
            return
        except Exception as e:
            logging.error(f"Error extracting {zip_path}: {str(e)}")
            print(f"Error extracting {zip_path}: {str(e)}")
            return
        
        extracted_info = analyze_extracted_content(extraction_dir, zip_path)
        display_info(extracted_info, max_info_lines)
        
        print(f"Debug: Success indicators: {extracted_info['success_indicators']}")
        
        logging.info(f"Extraction completed. Success indicators: {extracted_info['success_indicators']}")
        
        if all(extracted_info['success_indicators']):
            show_deletion_summary(zip_path, extraction_dir)
            logging.info("Deletion summary displayed")
            
            if not test_mode:
                confirmation = input("\nDo you want to proceed with the deletion? (yes/no): ").strip().lower()
                if confirmation == 'yes':
                    safe_delete_file(zip_path)
                    shutil.rmtree(extraction_dir)
                    print(f"Deleted extracted content in: {extraction_dir}")
                    logging.info(f"Deleted extracted content in: {extraction_dir}")
                else:
                    print("Deletion cancelled.")
            else:
                print("\nTest mode: Simulated deletion:")
                print(f"  Would delete zip file: {zip_path}")
                print(f"  Would delete extracted content in: {extraction_dir}")
                logging.info("Test mode: Simulated deletion")
        else:
            print("\nExtraction was not fully successful. Deletion skipped.")
            print("Reasons:")
            if not extracted_info['success_indicators']['files_extracted']:
                print("- No files were extracted")
            if not extracted_info['success_indicators']['no_errors']:
                print("- Errors occurred during extraction")
            if not extracted_info['success_indicators']['size_match']:
                print("- Extracted size doesn't match the original zip file size (within tolerance)")
            logging.warning("Extraction was not fully successful. Deletion skipped.")
        
        if test_mode:
            print("\nTest mode: Simulated cleanup completed.")
            logging.info("Test mode: Simulated cleanup completed")
    
    finally:
        if test_mode and temp_dir:
            print(f"Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir, ignore_errors=True)

def calculate_file_checksum(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def analyze_extracted_content(target_dir, zip_path):
    info = {
        'total_files': 0,
        'total_folders': 0,
        'file_types': defaultdict(int),
        'total_size': 0,
        'largest_file': ('', 0),
        'success_indicators': {
            'files_extracted': False,
            'no_errors': True
        },
        'checksums': {}
    }
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for file in zip_ref.infolist():
            if not file.is_dir():
                info['checksums'][file.filename] = {
                    'zip': file.CRC,  # This is the CRC-32 checksum stored in the zip
                    'extracted': None
                }
    
    for root, dirs, files in os.walk(target_dir):
        info['total_folders'] += len(dirs)
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, target_dir)
            file_size = os.path.getsize(file_path)
            file_type = magic.from_file(file_path, mime=True)
            
            info['total_files'] += 1
            info['file_types'][file_type] += 1
            info['total_size'] += file_size
            
            if file_size > info['largest_file'][1]:
                info['largest_file'] = (file, file_size)
            
            # Calculate CRC-32 for extracted file
            with open(file_path, 'rb') as f:
                extracted_crc = zlib.crc32(f.read()) & 0xFFFFFFFF
            
            if relative_path in info['checksums']:
                info['checksums'][relative_path]['extracted'] = extracted_crc
            else:
                info['checksums'][relative_path] = {
                    'zip': None,
                    'extracted': extracted_crc
                }
    
    # Check success indicators
    info['success_indicators']['files_extracted'] = info['total_files'] > 0
    
    zip_size = os.path.getsize(zip_path)
    info['zip_size'] = zip_size
    
    print(f"Debug: Zip size: {zip_size}, Extracted size: {info['total_size']}")
    print(f"Debug: Compression ratio: {zip_size / info['total_size']:.2f}")
    
    return info

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
    
    console.print("\n[green]All zip files processed.[/green]")

    if args.test:
        test_dir = Path.cwd() / "unzippy_test"
        if test_dir.exists():
            console.print(f"\nTo delete all test extractions, run: [cyan]rm -rf {test_dir}[/cyan]")

if __name__ == "__main__":
    main()