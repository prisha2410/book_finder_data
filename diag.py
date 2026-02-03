"""
CSV Diagnostic Tool - Helps identify column misalignment issues
Run this to see what's actually in your CSV files
"""

import pandas as pd
import sys
import fire 

def diagnose_csv(csv_path):
    """Diagnose CSV file structure and content."""
    print("\n" + "="*70)
    print(f"DIAGNOSING: {csv_path}")
    print("="*70)
    
    try:
        # Read the CSV
        df = pd.read_csv(csv_path)
        
        print(f"\n✓ File loaded successfully")
        print(f"  Total rows: {len(df)}")
        print(f"  Total columns: {len(df.columns)}")
        
        # Show all column names
        print(f"\n📋 Column Names ({len(df.columns)} total):")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i:2d}. '{col}'")
        
        # Show first few rows for each column
        print(f"\n🔍 First 3 Rows Sample:")
        print("-" * 70)
        
        for col in df.columns:
            print(f"\nColumn: '{col}'")
            print(f"Data type: {df[col].dtype}")
            print(f"Non-null count: {df[col].notna().sum()} / {len(df)}")
            
            # Show first 3 non-null values
            non_null_values = df[col].dropna().head(3).tolist()
            for i, val in enumerate(non_null_values, 1):
                # Truncate long values
                val_str = str(val)
                if len(val_str) > 100:
                    val_str = val_str[:97] + "..."
                print(f"  Row {i}: {val_str}")
        
        # Check specifically for genre/genres columns
        print(f"\n🎯 Genre Column Analysis:")
        print("-" * 70)
        
        genre_columns = [col for col in df.columns if 'genre' in col.lower()]
        if genre_columns:
            for col in genre_columns:
                print(f"\nFound column: '{col}'")
                non_null = df[col].notna().sum()
                print(f"  Non-null values: {non_null} / {len(df)} ({non_null/len(df)*100:.1f}%)")
                
                # Show sample values
                samples = df[col].dropna().head(5).tolist()
                for i, val in enumerate(samples, 1):
                    val_str = str(val)[:150]
                    print(f"  Sample {i}: {val_str}")
        else:
            print("  ⚠ No 'genre' or 'genres' column found!")
            print("\n  Columns that might contain genre data:")
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ['category', 'categories', 'subject', 'subjects', 'tag', 'tags']):
                    print(f"    - '{col}'")
        
        # Check for description column
        print(f"\n📝 Description Column Analysis:")
        print("-" * 70)
        
        desc_columns = [col for col in df.columns if 'desc' in col.lower()]
        if desc_columns:
            for col in desc_columns:
                print(f"\nFound column: '{col}'")
                non_null = df[col].notna().sum()
                print(f"  Non-null values: {non_null} / {len(df)} ({non_null/len(df)*100:.1f}%)")
                
                # Show one sample
                sample = df[col].dropna().head(1).tolist()
                if sample:
                    val_str = str(sample[0])[:200]
                    print(f"  Sample: {val_str}")
        
    except FileNotFoundError:
        print(f"\n✗ ERROR: File not found: {csv_path}")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" CSV DIAGNOSTIC TOOL ".center(70, "="))
    print("="*70)
    
    # Diagnose both CSV files
    files_to_check = [
        "data/books_data.csv",
        "data/enriched_books.csv",
        "data/books data.csv"  # Alternative name with space
    ]
    
    for csv_file in files_to_check:
        diagnose_csv(csv_file)
    
    print("\n" + "="*70)
    print(" DIAGNOSTIC COMPLETE ".center(70, "="))
    print("="*70)
    print("\nNext steps:")
    print("  1. Check which columns actually contain genre data")
    print("  2. Update your ingestion code to use the correct column name")
    print("  3. If columns are misaligned, you may need to fix the CSV file itself")
    print()

    fire.Fire({"diagnose_csv": diagnose_csv})