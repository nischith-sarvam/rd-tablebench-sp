import os
import hashlib
from collections import defaultdict
import argparse

def get_file_hash(filepath, blocksize=65536):
    """
    Calculate the SHA-256 hash of a file by reading it in chunks to handle large files efficiently.
    """
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as file:
        buffer = file.read(blocksize)
        while buffer:
            hasher.update(buffer)
            buffer = file.read(blocksize)
    return hasher.hexdigest()

def find_duplicates(directory):
    """
    Find duplicate files in the given directory.
    Returns a dictionary where keys are hash values and values are lists of files with that hash.
    """
    # First, group files by size as a quick filter (files with different sizes can't be identical)
    size_dict = defaultdict(list)
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(root, filename)
            try:
                file_size = os.path.getsize(filepath)
                size_dict[file_size].append(filepath)
            except (OSError, IOError) as e:
                print(f"Error accessing {filepath}: {e}")
    
    # Then, for files with the same size, calculate hashes
    hash_dict = defaultdict(list)
    for size, size_matches in size_dict.items():
        if len(size_matches) > 1:  # Only process files with the same size
            for filepath in size_matches:
                try:
                    file_hash = get_file_hash(filepath)
                    hash_dict[file_hash].append(filepath)
                except (OSError, IOError) as e:
                    print(f"Error hashing {filepath}: {e}")
    
    # Filter out unique files
    duplicate_groups = {file_hash: paths for file_hash, paths in hash_dict.items() if len(paths) > 1}
    return duplicate_groups

def delete_duplicates(duplicates):
    """
    Delete all files in duplicate groups.
    Returns the number of files deleted.
    """
    files_deleted = 0
    for file_hash, filepaths in duplicates.items():
        for filepath in filepaths:  # Delete all files in the group
            try:
                os.remove(filepath)
                files_deleted += 1
                print(f"Deleted: {filepath}")
            except OSError as e:
                print(f"Error deleting {filepath}: {e}")
    
    return files_deleted

def main():
    parser = argparse.ArgumentParser(description='Find duplicate files in a directory')
    parser.add_argument('directory', help='Directory to scan for duplicates')
    parser.add_argument('--output', '-o', help='Output file for results (default: print to console)')
    parser.add_argument('--delete', '-d', action='store_true', help='Delete duplicate files, keeping the newest version')
    parser.add_argument('--force', '-f', action='store_true', help='Delete without confirmation')
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a valid directory")
        return
    
    print(f"Scanning {args.directory} for duplicate files...")
    duplicates = find_duplicates(args.directory)
    
    if not duplicates:
        print("No duplicate files found.")
        return
    
    output_text = []
    total_groups = 0
    total_dupes = 0
    
    for file_hash, filepaths in duplicates.items():
        total_groups += 1
        total_dupes += len(filepaths) - 1
        
        # output_text.append(f"\nDuplicate group #{total_groups} (hash: {file_hash}):")
        for filepath in filepaths:
            output_text.append(f"  {filepath}")
    
    summary = f"\n\nSummary: Found {total_dupes} duplicate files in {total_groups} groups."
    output_text.append(summary)
    output_text = "\n".join(output_text)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_text)
        print(f"Results written to {args.output}")
    else:
        print(output_text)
    
    if args.delete:
        if not args.force:
            confirm = input(f"\nAre you sure you want to delete {total_dupes} duplicate files? (y/N): ")
            if confirm.lower() != 'y':
                print("Deletion cancelled.")
                return
        
        deleted = delete_duplicates(duplicates)
        print(f"\nSuccessfully deleted {deleted} duplicate files.")
    else:
        print(f"To save disk space, you can delete {total_dupes} duplicate files using the --delete option.")

if __name__ == "__main__":
    main()