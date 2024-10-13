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
from abc import ABC, abstractmethod
from rich.text import Text
import glob
from rich.rule import Rule
from rich import box

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

def create_summary_table(info):
    summary = Table(title="Extracted Content Summary", show_header=False, expand=False)
    summary.add_column("Attribute", style="cyan")
    summary.add_column("Value", style="magenta")
    
    summary.add_row("Total Files", str(info['total_files']))
    summary.add_row("Total Folders", str(info['total_folders']))
    summary.add_row("Total Size", humanize.naturalsize(info['total_size']))
    summary.add_row("Largest File", f"{info['largest_file'][0]} ({humanize.naturalsize(info['largest_file'][1])})")
    
    compression_ratio = info['zip_size'] / info['total_size'] if info['total_size'] > 0 else 1
    summary.add_row("Compression Ratio", f"{compression_ratio:.2f}x ({humanize.naturalsize(info['total_size'])} -> {humanize.naturalsize(info['zip_size'])})")
    
    return summary

def create_file_types_table(info):
    file_type_info = [(type, count) for type, count in info['file_types'].items()]
    file_type_info.sort(key=lambda x: x[1], reverse=True)
    
    top_types = file_type_info[:10]
    other_count = sum(count for _, count in file_type_info[10:])
    
    table = Table(title="File Types", show_header=True, expand=False)
    table.add_column("Type", style="cyan")
    table.add_column("Count", style="magenta", justify="right")
    
    for file_type, count in top_types:
        table.add_row(file_type, str(count))
    
    if other_count > 0:
        table.add_row("Other", str(other_count))
    
    return table

def create_checksum_panel(info):
    checksum_info = list(info['checksums'].items())
    matching_checksums = sum(1 for _, checksums in checksum_info if checksums['zip'] == checksums['extracted'])
    mismatched_checksums = len(checksum_info) - matching_checksums
    
    return Panel(
        f"Total files checked: {len(checksum_info)}\n"
        f"Matching checksums: [green]{matching_checksums}[/green]\n"
        f"Mismatched checksums: [red]{mismatched_checksums}[/red]",
        title="Checksum Comparison",
        expand=False
    )

def create_mismatch_tree(info):
    mismatch_tree = Tree("Mismatched files:")
    for file, checksums in info['checksums'].items():
        if checksums['zip'] != checksums['extracted']:
            file_node = mismatch_tree.add(file)
            file_node.add(f"Zip CRC-32:       {checksums['zip']:08X}")
            file_node.add(f"Extracted CRC-32: {checksums['extracted']:08X}")
    return mismatch_tree

def create_success_panel(info):
    content = Text()
    content.append("Original zip file to be deleted: ", style="cyan")
    content.append(f"{info['zip_path']}\n", style="magenta")
    content.append("Extracted content location: ", style="cyan")
    content.append(f"{info['extraction_dir']}\n", style="magenta")
    content.append("Files to be kept: ", style="cyan")
    content.append(f"{info['total_files']}\n", style="magenta")
    content.append("Directories to be kept: ", style="cyan")
    content.append(f"{info['total_folders']}", style="magenta")

    return Panel(content, title="Deletion Summary", expand=False, border_style="bold")

def display_info(info, test_mode=False):
    console.print(create_summary_table(info))
    console.print(create_file_types_table(info))
    console.print(create_checksum_panel(info))
    
    if any(checksums['zip'] != checksums['extracted'] for checksums in info['checksums'].values()):
        console.print(create_mismatch_tree(info))

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

class UnzipCommand(ABC):
    def __init__(self, zip_path, target_dir):
        self.zip_path = Path(zip_path)
        self.target_dir = Path(target_dir)
        self.extraction_dir = None

    @abstractmethod
    def execute(self):
        pass

    def unzip(self):
        self.extraction_dir = self.target_dir / self.zip_path.stem
        self.extraction_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                total_size = sum(file.file_size for file in zip_ref.infolist())
                with tqdm(total=total_size, unit='B', unit_scale=True, desc="Extracting") as pbar:
                    for file in zip_ref.infolist():
                        zip_ref.extract(file, self.extraction_dir)
                        pbar.update(file.file_size)
        except zipfile.BadZipFile:
            console.print(f"[red]Error: {self.zip_path} is not a valid zip file.[/red]")
            return False
        except Exception as e:
            console.print(f"[red]Error extracting {self.zip_path}: {str(e)}[/red]")
            return False
        
        return True

    def analyze_and_display(self):
        extracted_info = analyze_extracted_content(self.extraction_dir, self.zip_path)
        display_info(extracted_info, isinstance(self, TestUnzipCommand))
        return extracted_info

    def show_deletion_summary(self):
        summary = Table(title="Deletion Summary", show_header=False, expand=False)
        summary.add_column("Item", style="cyan")
        summary.add_column("Details", style="magenta")
        
        summary.add_row("Original zip file to be deleted", str(self.zip_path))
        summary.add_row("Extracted content location", str(self.extraction_dir))
        
        file_count = sum(len(files) for _, _, files in os.walk(self.extraction_dir))
        dir_count = sum(len(dirs) for _, dirs, _ in os.walk(self.extraction_dir))
        
        summary.add_row("Files to be kept", str(file_count))
        summary.add_row("Directories to be kept", str(dir_count))
        
        console.print(Panel(summary, title="Deletion Summary", expand=False))

class ProductionUnzipCommand(UnzipCommand):
    def execute(self):
        if not self.unzip():
            return

        extracted_info = self.analyze_and_display()
        
        if all(extracted_info['success_indicators'].values()):
            self.show_deletion_summary()
            try:
                confirmation = console.input("\nDo you want to proceed with deleting the original zip file? (yes/no): ").strip().lower()
                if confirmation == 'yes':
                    safe_delete_file(self.zip_path)
                else:
                    console.print("[yellow]Deletion cancelled.[/yellow]")
            except KeyboardInterrupt:
                console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        else:
            console.print("\n[red]Extraction was not fully successful. Deletion skipped.[/red]")
            console.print("Reasons:")
            if not extracted_info['success_indicators']['files_extracted']:
                console.print("- No files were extracted")
            if not extracted_info['success_indicators']['no_errors']:
                console.print("- Errors occurred during extraction")

class TestUnzipCommand(UnzipCommand):
    def execute(self):
        extraction_dir = self.target_dir / self.zip_path.stem
        console.print(f"[yellow]Test mode: Extracting to {extraction_dir}[/yellow]")
        
        if not self.unzip():
            return

        extracted_info = self.analyze_and_display()
        
        if all(extracted_info['success_indicators'].values()):
            console.print(create_success_panel(extracted_info))
            
            test_summary = Table(title="Test Mode Summary", show_header=False, expand=False, box=box.ROUNDED)
            test_summary.add_column("Item", style="cyan")
            test_summary.add_column("Details", style="magenta")
            
            test_summary.add_row("Production behavior", "Original zip file would be deleted")
            test_summary.add_row("Extracted content", "Would remain in the location shown above")
            test_summary.add_row("Next steps", "Inspect the extracted contents")
            test_summary.add_row("Clean up test files", f"Run: rm -rf {self.extraction_dir}")
            
            console.print(test_summary)
        else:
            console.print("\n[red]Extraction was not fully successful. Deletion would be skipped.[/red]")
            console.print("Reasons:")
            if not extracted_info['success_indicators']['files_extracted']:
                console.print("- No files were extracted")
            if not extracted_info['success_indicators']['no_errors']:
                console.print("- Errors occurred during extraction")

def get_zip_checksums(zip_path):
    checksums = {}
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for file in zip_ref.infolist():
            if not file.is_dir():
                checksums[file.filename] = {
                    'zip': file.CRC,
                    'extracted': None
                }
    return checksums

def calculate_file_checksum(file_path):
    with open(file_path, 'rb') as f:
        return zlib.crc32(f.read()) & 0xFFFFFFFF

def analyze_file(file_path, relative_path, info):
    file_size = os.path.getsize(file_path)
    file_type = magic.from_file(file_path, mime=True)
    
    info['total_files'] += 1
    info['file_types'][file_type] += 1
    info['total_size'] += file_size
    
    if file_size > info['largest_file'][1]:
        info['largest_file'] = (relative_path, file_size)
    
    extracted_checksum = calculate_file_checksum(file_path)
    if relative_path in info['checksums']:
        info['checksums'][relative_path]['extracted'] = extracted_checksum
    else:
        info['checksums'][relative_path] = {
            'zip': None,
            'extracted': extracted_checksum
        }

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
        'checksums': {},
        'zip_path': zip_path,
        'extraction_dir': target_dir
    }
    
    for root, dirs, files in os.walk(target_dir):
        info['total_folders'] += len(dirs)
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, target_dir)
            analyze_file(file_path, relative_path, info)
            
            zip_checksum = get_zip_checksum(zip_path, relative_path)
            extracted_checksum = calculate_file_checksum(file_path)
            
            if zip_checksum is not None:
                info['checksums'][relative_path] = {
                    'zip': zip_checksum,
                    'extracted': extracted_checksum
                }
    
    # Check success indicators
    info['success_indicators']['files_extracted'] = info['total_files'] > 0
    
    zip_size = os.path.getsize(zip_path)
    info['zip_size'] = zip_size
    
    return info

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Unzip helper for macOS",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('files', nargs='*', help='Zip file(s) to process')
    parser.add_argument('-t', '--target', default=None,
                        help='Target directory for extraction')
    parser.add_argument('--test', action='store_true',
                        help='Run in test mode (no deletion, cleanup after extraction)')
    
    return parser.parse_args()

def get_zip_checksum(zip_path, file_path):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            try:
                info = zip_ref.getinfo(file_path)
                return info.CRC
            except KeyError:
                print(f"Warning: File {file_path} not found in zip archive.")
                return None
    except zipfile.BadZipFile:
        print(f"Error: {zip_path} is not a valid zip file.")
        return None

def main():
    args = parse_arguments()

    working_dir = Path.cwd()
    print(f"Working directory: {working_dir}")

    zip_files = args.files

    # If no files are specified, process all zip files in the working directory
    if not zip_files:
        zip_files = list(working_dir.glob('*.zip'))
        if not zip_files:
            print(f"No zip files found in {working_dir}. Use 'unzippy --help' for usage information.")
            return

    for i, zip_file in enumerate(zip_files):
        if i > 0:
            # Add a separator between files
            console.print(Rule(f"Processing next file ({i+1}/{len(zip_files)})", style="cyan"))
        
        zip_path = Path(zip_file)
        if not zip_path.is_absolute():
            zip_path = working_dir / zip_path

        if not zip_path.exists():
            print(f"Error: {zip_path} does not exist.")
            continue

        if not zip_path.is_file() or zip_path.suffix.lower() != '.zip':
            print(f"Error: {zip_path} is not a valid zip file.")
            continue

        print(f"\nProcessing zip file: {zip_path}")
        print(f"Test mode: {'Yes' if args.test else 'No'}")

        if args.test:
            command = TestUnzipCommand(str(zip_path), str(args.target or working_dir))
        else:
            command = ProductionUnzipCommand(str(zip_path), str(args.target or working_dir))
        command.execute()

    if args.test:
        test_dir = working_dir / "unzippy_test"
        if test_dir.exists():
            print(f"\nTo delete all test extractions, run: rm -rf {test_dir}")

if __name__ == "__main__":
    main()