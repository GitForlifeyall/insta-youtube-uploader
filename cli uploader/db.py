#!/usr/bin/env python3
"""
SQLite Database Manager for Brands & Redroid Containers
========================================================
Manages brands, container names, ADB host ports, and designated brand content
folders in a SQLite database (`data/brands.db`).

Automatically creates and tracks the physical content folder inside `brand folders/`
for every registered brand.

CLI Usage:
    # Initialize / reset database with default brands and create brand folders:
    python db.py init

    # List all registered brands and folders:
    python db.py list

    # Add a new brand (automatically creates 'brand folders/Brand Delta'):
    python db.py add --id 04 --name "Brand Delta" --container "redroid-04" --port 5804

    # Add with a custom folder path:
    python db.py add --id 05 --name "E-Commerce" --container "redroid-05" --port 5805 --folder "C:/Custom/Videos"

    # Get details for a specific brand:
    python db.py get 01

    # Remove a brand:
    python db.py remove 04
"""

import os
import sys
import sqlite3
import argparse
import re
from pathlib import Path
from typing import Optional, List, Dict, Any

CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent
DATA_DIR = REPO_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BRAND_FOLDERS_ROOT = REPO_ROOT / "brand folders"
BRAND_FOLDERS_ROOT.mkdir(parents=True, exist_ok=True)

DEFAULT_DB_PATH = DATA_DIR / "brands.db"


def sanitize_folder_name(name: str) -> str:
    """Sanitizes brand name to be safe for directory naming across OSes."""
    clean = re.sub(r'[<>:"/\\|?*]', '_', name.strip())
    return clean or "Unnamed_Brand"


def resolve_brand_folder(name: str, brand_id: Optional[str] = None, custom_folder: Optional[str] = None) -> str:
    """Ensures a brand content folder exists on disk and returns its path."""
    if custom_folder:
        folder_path = Path(custom_folder).resolve()
    else:
        folder_name = sanitize_folder_name(name)
        folder_path = BRAND_FOLDERS_ROOT / folder_name

    folder_path.mkdir(parents=True, exist_ok=True)
    return str(folder_path)


def get_db_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_database(db_path: Path = DEFAULT_DB_PATH, seed_defaults: bool = True) -> str:
    """Creates the brands table and schema in SQLite, ensuring folder_path exists."""
    BRAND_FOLDERS_ROOT.mkdir(parents=True, exist_ok=True)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS brands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        container_name TEXT NOT NULL,
        host_port INTEGER NOT NULL,
        adb_target TEXT NOT NULL,
        volume_name TEXT,
        folder_path TEXT,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Auto-migration check: ensure folder_path column exists
    cursor.execute("PRAGMA table_info(brands);")
    columns = [row[1] for row in cursor.fetchall()]
    if "folder_path" not in columns:
        cursor.execute("ALTER TABLE brands ADD COLUMN folder_path TEXT;")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_brand_id ON brands(brand_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_brand_name ON brands(name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_host_port ON brands(host_port);")

    conn.commit()

    if seed_defaults:
        seed_data = [
            ("01", "Account 01", "redroid-01", 5801, "127.0.0.1:5801", "redroid-account-01-data"),
            ("02", "Account 02", "redroid-02", 5802, "127.0.0.1:5802", "redroid-account-02-data"),
            ("03", "Account 03", "redroid-03", 5803, "127.0.0.1:5803", "redroid-account-03-data"),
            ("brand_01", "Brand Alpha", "redroid-brand-01", 5555, "127.0.0.1:5555", "redroid-brand-01-data"),
            ("dffds_3", "dffds", "redroid-dffds-3", 5560, "127.0.0.1:5560", "redroid-dffds-3-data"),
        ]

        for b_id, name, container, port, target, volume in seed_data:
            folder_dir = resolve_brand_folder(name, b_id)
            cursor.execute("""
            INSERT INTO brands (brand_id, name, container_name, host_port, adb_target, volume_name, folder_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(brand_id) DO UPDATE SET
                folder_path = excluded.folder_path
            WHERE folder_path IS NULL OR folder_path = '';
            """, (b_id, name, container, port, target, volume, folder_dir))

        conn.commit()

    # Ensure any rows with empty folder_path have a folder created
    cursor.execute("SELECT brand_id, name, folder_path FROM brands;")
    for row in cursor.fetchall():
        if not row["folder_path"] or not Path(row["folder_path"]).exists():
            f_path = resolve_brand_folder(row["name"], row["brand_id"], row["folder_path"])
            cursor.execute("UPDATE brands SET folder_path = ? WHERE brand_id = ?;", (f_path, row["brand_id"]))

    conn.commit()
    conn.close()
    return str(db_path)


def get_all_brands(db_path: Path = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Returns a list of all registered brands as dictionaries."""
    init_database(db_path, seed_defaults=True)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM brands ORDER BY host_port ASC;")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_brand_by_identifier(identifier: str, db_path: Path = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Finds a brand by brand_id, name, container_name, or host_port."""
    init_database(db_path, seed_defaults=True)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    ident_str = str(identifier).strip()
    ident_clean = ident_str.lower().replace(" ", "").replace("-", "_")

    # 1. Exact match
    cursor.execute("""
    SELECT * FROM brands
    WHERE LOWER(brand_id) = LOWER(?)
       OR LOWER(name) = LOWER(?)
       OR LOWER(container_name) = LOWER(?)
       OR host_port = ?
    """, (ident_str, ident_str, ident_str, int(ident_str) if ident_str.isdigit() else -1))
    row = cursor.fetchone()

    # 2. Fuzzy match
    if not row:
        cursor.execute("SELECT * FROM brands;")
        all_brands = cursor.fetchall()
        for b in all_brands:
            b_dict = dict(b)
            cand_id = b_dict["brand_id"].lower().replace("-", "_")
            cand_name = b_dict["name"].lower().replace(" ", "").replace("-", "_")
            cand_cont = b_dict["container_name"].lower().replace("-", "_")
            if ident_clean in (cand_id, cand_name, cand_cont) or ident_clean in cand_cont or ident_clean in cand_name:
                row = b
                break

    conn.close()
    return dict(row) if row else None


def add_or_update_brand(
    brand_id: str,
    name: str,
    container_name: str,
    host_port: int,
    volume_name: Optional[str] = None,
    folder_path: Optional[str] = None,
    db_path: Path = DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """Adds a new brand or updates existing brand by brand_id and provisions brand folder."""
    init_database(db_path, seed_defaults=False)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    adb_target = f"127.0.0.1:{host_port}"
    vol = volume_name or f"{container_name}-data"
    final_folder = resolve_brand_folder(name, brand_id, folder_path)

    cursor.execute("""
    INSERT INTO brands (brand_id, name, container_name, host_port, adb_target, volume_name, folder_path, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(brand_id) DO UPDATE SET
        name = excluded.name,
        container_name = excluded.container_name,
        host_port = excluded.host_port,
        adb_target = excluded.adb_target,
        volume_name = excluded.volume_name,
        folder_path = excluded.folder_path,
        updated_at = CURRENT_TIMESTAMP;
    """, (brand_id, name, container_name, host_port, adb_target, vol, final_folder))

    conn.commit()
    conn.close()
    return get_brand_by_identifier(brand_id, db_path)


def delete_brand(brand_id: str, db_path: Path = DEFAULT_DB_PATH) -> bool:
    """Deletes a brand by brand_id or name."""
    init_database(db_path, seed_defaults=False)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM brands WHERE brand_id = ? OR name = ?;", (brand_id, brand_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def update_brand_folder(identifier: str, folder_path: str, db_path: Path = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Updates the assigned content folder path for an existing brand."""
    brand = get_brand_by_identifier(identifier, db_path)
    if not brand:
        return None

    resolved_path = Path(folder_path).resolve()
    resolved_path.mkdir(parents=True, exist_ok=True)

    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE brands
    SET folder_path = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?;
    """, (str(resolved_path), brand["id"]))
    conn.commit()
    conn.close()
    return get_brand_by_identifier(identifier, db_path)


def format_brands_table(brands: List[Dict[str, Any]]) -> str:
    """Formats brands list into a clean terminal table with folder paths."""
    if not brands:
        return "No brands registered in database."

    header = f"{'ID':<10} | {'BRAND NAME':<16} | {'CONTAINER':<18} | {'PORT':<5} | {'ADB TARGET':<15} | {'BRAND FOLDER'}"
    sep = "-" * 110
    rows = [header, sep]
    for b in brands:
        f_display = b.get('folder_path') or 'None'
        # Relative to REPO_ROOT for shorter display
        try:
            p_rel = Path(f_display).relative_to(REPO_ROOT)
            f_display = str(p_rel)
        except Exception:
            pass

        rows.append(
            f"{b['brand_id']:<10} | {b['name']:<16} | {b['container_name']:<18} | {b['host_port']:<5} | {b['adb_target']:<15} | {f_display}"
        )
    return "\n".join(rows)


def main():
    parser = argparse.ArgumentParser(description="SQLite Brand & Container Manager for Redroid")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # init
    subparsers.add_parser("init", help="Initialize database, seed default brands, and provision brand folders")

    # list
    subparsers.add_parser("list", help="List all brands, containers, and folder mappings")

    # get
    get_p = subparsers.add_parser("get", help="Get details for a specific brand")
    get_p.add_argument("identifier", help="Brand ID, name, or port number")

    # add
    add_p = subparsers.add_parser("add", help="Add or update a brand container and content folder")
    add_p.add_argument("--id", required=True, help="Brand identifier (e.g. '04', 'brand_04')")
    add_p.add_argument("--name", required=True, help="Display brand name (e.g. 'Brand Delta')")
    add_p.add_argument("--container", required=True, help="Docker container name (e.g. 'redroid-04')")
    add_p.add_argument("--port", type=int, required=True, help="Host ADB port (e.g. 5804)")
    add_p.add_argument("--volume", default=None, help="Docker volume name for persistent data")
    add_p.add_argument("--folder", default=None, help="Custom folder path (defaults to 'brand folders/<brand_name>')")

    # set-folder
    sf_p = subparsers.add_parser("set-folder", help="Set or update the content folder path for a brand")
    sf_p.add_argument("identifier", help="Brand ID or name")
    sf_p.add_argument("folder", help="Path to brand content folder")

    # remove
    rem_p = subparsers.add_parser("remove", help="Remove a brand from the database")
    rem_p.add_argument("brand_id", help="Brand ID or name to remove")

    args = parser.parse_args()

    if args.command == "init" or not args.command:
        path = init_database(seed_defaults=True)
        print(f"[+] SQLite Database initialized at: {path}")
        print(f"[+] Brand folders directory: {BRAND_FOLDERS_ROOT}")
        print("\n" + format_brands_table(get_all_brands()))

    elif args.command == "list":
        brands = get_all_brands()
        print("\n" + format_brands_table(brands))

    elif args.command == "get":
        brand = get_brand_by_identifier(args.identifier)
        if brand:
            print(f"\n[+] Brand Found:")
            for k, v in brand.items():
                print(f"    {k:<15}: {v}")
        else:
            print(f"[!] No brand found matching '{args.identifier}'")
            sys.exit(1)

    elif args.command == "add":
        b = add_or_update_brand(
            brand_id=args.id,
            name=args.name,
            container_name=args.container,
            host_port=args.port,
            volume_name=args.volume,
            folder_path=args.folder
        )
        print(f"[+] Successfully registered brand '{b['name']}' ({b['brand_id']}):")
        print("\n" + format_brands_table(get_all_brands()))

    elif args.command == "set-folder":
        b = update_brand_folder(args.identifier, args.folder)
        if b:
            print(f"[+] Successfully updated content folder for '{b['name']}' ({b['brand_id']}):\n    -> {b['folder_path']}")
            print("\n" + format_brands_table(get_all_brands()))
        else:
            print(f"[!] No brand found matching '{args.identifier}'")
            sys.exit(1)

    elif args.command == "remove":
        ok = delete_brand(args.brand_id)
        if ok:
            print(f"[+] Successfully removed brand '{args.brand_id}'")
            print("\n" + format_brands_table(get_all_brands()))
        else:
            print(f"[!] No brand found matching '{args.brand_id}'")
            sys.exit(1)


if __name__ == "__main__":
    main()
