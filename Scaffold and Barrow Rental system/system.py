from tkinter import ttk, messagebox, filedialog
import tkinter as tk  # This should be first
from datetime import datetime, timedelta
import sqlite3
import random
import os
import tempfile
import platform
import re
import bcrypt
from typing import List, Dict, Any, Optional, Tuple
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
import traceback
import shutil
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from PIL import Image, ImageTk


# Constants
def get_desktop_path() -> str:
    """Get the desktop path for the current user."""
    return os.path.expanduser("~/Desktop")


DATABASE_FILENAME = os.path.join(get_desktop_path(), "rental_system_v6.db")
RECEIPTS_FOLDER = os.path.join(get_desktop_path(), "Rental System Receipts")
if not os.path.exists(RECEIPTS_FOLDER):
    os.makedirs(RECEIPTS_FOLDER)

# Admin Configuration
ADMIN_USERNAME = "admin"
ADMIN_DEFAULT_PASSWORD = "admin123"  # Should be changed on first login


class PasswordManager:
    """Handles password hashing and verification."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def check_password(password: str, hashed: str) -> bool:
        """Check if password matches the hash."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False


class DatabaseManager:
    """Manages all database operations with improved error handling."""

    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_FILENAME, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.conn.cursor()
        self.setup_tables()
        self.initialize_admin()
        self.initialize_settings()

    def setup_tables(self):
        """Initialize all database tables with proper schema."""
        tables = [
            '''CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                user_type TEXT NOT NULL CHECK(user_type IN ('admin', 'staff')),
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                created_at TEXT NOT NULL,
                last_login TEXT,
                is_active INTEGER DEFAULT 1,
                transfer_history TEXT DEFAULT ''  -- Store transfer history as JSON string
            )''',
            '''CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                activity_description TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )''',
            '''CREATE TABLE IF NOT EXISTS reference_storage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference_number TEXT UNIQUE NOT NULL,
                customer_name TEXT NOT NULL,
                date_created TEXT NOT NULL,
                status TEXT DEFAULT 'Active',
                date_returned TEXT,
                refund_amount REAL DEFAULT 0.0,
                refund_reason TEXT,
                refund_by INTEGER,
                created_by INTEGER,
                FOREIGN KEY (refund_by) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL
            )''',
            '''CREATE TABLE IF NOT EXISTS rentals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                phone TEXT,
                customer_id TEXT,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                items TEXT NOT NULL,
                rental_charges REAL NOT NULL,
                deposit_paid REAL NOT NULL,
                total_due REAL NOT NULL,
                status TEXT DEFAULT 'Rented',
                created_at TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                receipt_printed INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
            )''',
            '''CREATE TABLE IF NOT EXISTS financial_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE NOT NULL,
                timestamp TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                user_id INTEGER NOT NULL,
                category TEXT,
                reference_number TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
            )''',
            '''CREATE TABLE IF NOT EXISTS rental_out_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference TEXT UNIQUE NOT NULL,
                customer_name TEXT NOT NULL,
                phone TEXT,
                area TEXT,
                item TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                rate_type TEXT NOT NULL,
                date TEXT NOT NULL,
                time_out TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                deposit_paid REAL DEFAULT 0.0,
                status TEXT DEFAULT 'Active',
                days_with_customer INTEGER DEFAULT 0,
                receipt_printed INTEGER DEFAULT 0,
                overdue INTEGER DEFAULT 0,
                overdue_days INTEGER DEFAULT 0,
                refund_processed INTEGER DEFAULT 0,
                refund_amount REAL DEFAULT 0.0,
                refund_reason TEXT,
                refund_by INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY (refund_by) REFERENCES users(user_id) ON DELETE SET NULL
            )''',
            '''CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT NOT NULL
            )''',
            '''CREATE TABLE IF NOT EXISTS session_timeouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                timeout_minutes INTEGER DEFAULT 30,
                last_activity TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )''',
            '''CREATE TABLE IF NOT EXISTS expense_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT UNIQUE NOT NULL,
                description TEXT
            )''',
            '''CREATE TABLE IF NOT EXISTS account_transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER NOT NULL,
                to_user_id INTEGER NOT NULL,
                transferred_by INTEGER NOT NULL,
                transferred_at TEXT NOT NULL,
                reason TEXT,
                FOREIGN KEY (from_user_id) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY (to_user_id) REFERENCES users(user_id) ON DELETE SET NULL,
                FOREIGN KEY (transferred_by) REFERENCES users(user_id) ON DELETE SET NULL
            )'''
        ]

        for table_sql in tables:
            try:
                self.cursor.execute(table_sql)
            except sqlite3.Error as e:
                print(f"Error creating table: {e}")

        self.conn.commit()
        self.add_missing_columns()
        self.initialize_default_categories()

        self.conn.commit()  # Ensure all changes are committed

    def add_missing_columns(self):
        """Add missing columns to existing tables."""
        try:
            # Check columns for users table
            self.cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in self.cursor.fetchall()]

            if 'transfer_history' not in columns:
                self.cursor.execute("ALTER TABLE users ADD COLUMN transfer_history TEXT DEFAULT ''")
                print("Added transfer_history column to users table")

            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error adding columns: {e}")

    def initialize_default_categories(self):
        """Initialize default expense categories."""
        default_categories = [
            ('Utilities', 'Electricity, water, internet bills'),
            ('Maintenance', 'Equipment repair and maintenance'),
            ('Transportation', 'Fuel and vehicle expenses'),
            ('Supplies', 'Office and operational supplies'),
            ('Salaries', 'Staff salaries and wages'),
            ('Rent', 'Office or storage space rent'),
            ('Other', 'Miscellaneous expenses'),
            ('Refunds', 'Customer refunds')
        ]

        for category, description in default_categories:
            try:
                self.cursor.execute(
                    "INSERT OR IGNORE INTO expense_categories (category_name, description) VALUES (?, ?)",
                    (category, description)
                )
            except sqlite3.Error:
                pass
        self.conn.commit()

    def initialize_admin(self):
        """Initialize the admin account if it doesn't exist."""
        try:
            self.cursor.execute("SELECT 1 FROM users WHERE username = ?", (ADMIN_USERNAME,))
            if not self.cursor.fetchone():
                hashed_password = PasswordManager.hash_password(ADMIN_DEFAULT_PASSWORD)
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.cursor.execute('''
                    INSERT INTO users (username, password, user_type, first_name, last_name, created_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (ADMIN_USERNAME, hashed_password, 'admin', 'System', 'Administrator', current_time, 1))
                self.conn.commit()
                print("Admin account created with default password.")
        except sqlite3.Error as e:
            print(f"Error initializing admin: {e}")

    def initialize_settings(self):
        """Initialize system settings."""
        default_settings = [
            ('auto_logout_minutes', '20'),
            ('receipt_footer', 'Developed by Techify Solution\nCall us on 0547607270'),
            ('company_name', 'KOB BARROW & SCAFFOLD RENTALS'),
            ('company_phone', '0244065009/0243450557'),
            ('company_location', 'Assin Foso'),
            ('overdue_days_threshold', '2')
        ]

        for key, value in default_settings:
            try:
                self.cursor.execute(
                    "INSERT OR IGNORE INTO system_settings (setting_key, setting_value) VALUES (?, ?)",
                    (key, value)
                )
            except sqlite3.Error:
                pass
        self.conn.commit()

    def execute_query(self, query: str, params: tuple = ()) -> List[tuple]:
        """Execute a query with transaction handling."""
        try:
            self.cursor.execute("BEGIN IMMEDIATE")
            self.cursor.execute(query, params)
            result = self.cursor.fetchall()
            self.conn.commit()
            return result
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Query error: {e}")
            raise e

    def execute_write(self, query: str, params: tuple = ()) -> bool:
        """Execute a write operation with transaction handling."""
        try:
            self.cursor.execute("BEGIN IMMEDIATE")
            self.cursor.execute(query, params)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Write error: {e}")
            return False

    def log_activity(self, user_id: int, description: str) -> bool:
        """Log an activity for a user."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.execute_write(
            "INSERT INTO activities (timestamp, user_id, activity_description) VALUES (?, ?, ?)",
            (timestamp, user_id, description)
        )

    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate a user and return user info if successful."""
        try:
            result = self.execute_query(
                "SELECT user_id, username, password, user_type, first_name, last_name, is_active FROM users WHERE username = ?",
                (username,)
            )

            if result:
                user_data = result[0]
                if user_data[6] != 1:  # is_active column
                    return None

                if PasswordManager.check_password(password, user_data[2]):
                    user_info = {
                        'user_id': user_data[0],
                        'username': user_data[1],
                        'user_type': user_data[3],
                        'first_name': user_data[4],
                        'last_name': user_data[5],
                        'is_active': user_data[6]
                    }

                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.execute_write(
                        "UPDATE users SET last_login = ? WHERE user_id = ?",
                        (current_time, user_info['user_id'])
                    )

                    self.update_session_timeout(user_info['user_id'])
                    return user_info
        except Exception as e:
            print(f"Authentication error: {e}")

        return None

    def get_staff_by_id(self, staff_id: int) -> Optional[Dict]:
        """Get complete staff information by ID."""
        try:
            result = self.execute_query('''
                SELECT user_id, username, first_name, last_name, phone, email, is_active, created_at, last_login, transfer_history
                FROM users
                WHERE user_id = ? AND user_type = 'staff'
            ''', (staff_id,))

            if result:
                row = result[0]
                return {
                    'user_id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'last_name': row[3],
                    'phone': row[4] or '',
                    'email': row[5] or '',
                    'is_active': row[6],
                    'created_at': row[7],
                    'last_login': row[8] or 'Never',
                    'transfer_history': row[9] or ''
                }
            return None
        except Exception as e:
            print(f"Error getting staff by ID: {e}")
            return None

    def create_staff_account(self, username: str, password: str, first_name: str,
                             last_name: str, phone: str = "", email: str = "") -> Tuple[bool, str]:
        """Create a new staff account with robust email validation."""
        try:
            result = self.execute_query("SELECT 1 FROM users WHERE username = ?", (username,))
            if result:
                return False, "Username already exists."

            if len(username) < 3:
                return False, "Username must be at least 3 characters."
            if len(password) < 8:
                return False, "Password must be at least 8 characters."
            if not first_name or not last_name:
                return False, "First and last name are required."

            if phone and not re.match(r'^[0-9+\- ]+$', phone):
                return False, "Phone number can only contain digits, plus, hyphen, or space."

            if email:
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, email):
                    return False, "Invalid email format. Please enter a valid email address."

                email_result = self.execute_query("SELECT 1 FROM users WHERE email = ?", (email,))
                if email_result:
                    return False, "Email address already exists in the system."

            hashed_password = PasswordManager.hash_password(password)
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            success = self.execute_write('''
                INSERT INTO users (username, password, user_type, first_name, last_name, phone, email, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, hashed_password, 'staff', first_name, last_name, phone, email, current_time, 1))

            if success:
                user_result = self.execute_query("SELECT user_id FROM users WHERE username = ?", (username,))
                if user_result:
                    user_id = user_result[0][0]
                    self.set_session_timeout(user_id, 30)
                return True, "Staff account created successfully."
            else:
                return False, "Failed to create account."

        except sqlite3.Error as e:
            return False, f"Database error: {e}"

    def update_staff_info(self, staff_id: int, username: str, first_name: str,
                          last_name: str, phone: str, email: str) -> Tuple[bool, str]:
        """Update staff basic information."""
        try:
            # Validate inputs
            if len(username) < 3:
                return False, "Username must be at least 3 characters."
            if not first_name or not last_name:
                return False, "First and last name are required."

            if phone and not re.match(r'^[0-9+\- ]+$', phone):
                return False, "Phone number can only contain digits, plus, hyphen, or space."

            if email:
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, email):
                    return False, "Invalid email format. Please enter a valid email address."

            # Check username uniqueness
            result = self.execute_query(
                "SELECT user_id FROM users WHERE username = ? AND user_id != ?",
                (username, staff_id)
            )
            if result:
                return False, "Username already taken by another user."

            if email:
                result = self.execute_query(
                    "SELECT user_id FROM users WHERE email = ? AND user_id != ? AND email != ''",
                    (email, staff_id)
                )
                if result:
                    return False, "Email already used by another user."

            # Update user information
            success = self.execute_write('''
                UPDATE users 
                SET username = ?, first_name = ?, last_name = ?, phone = ?, email = ?
                WHERE user_id = ? AND user_type = 'staff'
            ''', (username, first_name, last_name, phone, email, staff_id))

            if success:
                return True, "Staff information updated successfully."
            else:
                return False, "Failed to update staff information."

        except Exception as e:
            return False, f"Error: {str(e)}"

    def change_staff_password(self, staff_id: int, new_password: str) -> Tuple[bool, str]:
        """Change staff password with strong validation."""
        try:
            # STRONG PASSWORD VALIDATION
            errors = []

            # Length check
            if len(new_password) < 8:
                errors.append("Password must be at least 8 characters long.")

            # Character diversity checks
            if not re.search(r'[A-Z]', new_password):
                errors.append("Password must contain at least one uppercase letter.")

            if not re.search(r'[a-z]', new_password):
                errors.append("Password must contain at least one lowercase letter.")

            if not re.search(r'[0-9]', new_password):
                errors.append("Password must contain at least one number.")

            if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', new_password):
                errors.append("Password must contain at least one special character.")

            # Check for common patterns
            common_passwords = ['password', '123456', 'admin123', 'qwerty', 'letmein']
            if new_password.lower() in common_passwords:
                errors.append("Password is too common. Choose a more unique password.")

            # Check for sequential characters
            if re.search(r'(.)\1{2,}', new_password):
                errors.append("Password cannot contain 3 or more repeating characters.")

            if errors:
                error_message = "Password validation failed:\n\n" + "\n".join(f"• {error}" for error in errors)
                return False, error_message

            # Hash the password
            hashed_password = PasswordManager.hash_password(new_password)

            # Update password in database
            success = self.execute_write(
                "UPDATE users SET password = ? WHERE user_id = ? AND user_type = 'staff'",
                (hashed_password, staff_id)
            )

            if success:
                return True, "Password changed successfully."
            else:
                return False, "Failed to change password due to database error."

        except Exception as e:
            return False, f"System error: {str(e)}"

    def transfer_staff_account(self, from_staff_id: int, to_staff_id: int,
                               transferred_by: int, reason: str = "") -> Tuple[bool, str]:
        """Transfer account from one staff to another."""
        try:
            # Get both staff details
            from_staff = self.get_staff_by_id(from_staff_id)
            to_staff = self.get_staff_by_id(to_staff_id)

            if not from_staff or not to_staff:
                return False, "One or both staff accounts not found."

            if from_staff_id == to_staff_id:
                return False, "Cannot transfer account to the same staff member."

            # Check if target staff is active
            if to_staff['is_active'] != 1:
                return False, "Target staff account is not active. Please activate it first."

            # Start transaction
            self.cursor.execute("BEGIN IMMEDIATE")

            # Update all rentals to point to new staff
            self.cursor.execute('''
                UPDATE rentals SET user_id = ? WHERE user_id = ?
            ''', (to_staff_id, from_staff_id))

            # Update rental_out_records
            self.cursor.execute('''
                UPDATE rental_out_records SET user_id = ? WHERE user_id = ?
            ''', (to_staff_id, from_staff_id))

            # Update financial_transactions
            self.cursor.execute('''
                UPDATE financial_transactions SET user_id = ? WHERE user_id = ?
            ''', (to_staff_id, from_staff_id))

            # Update reference_storage created_by
            self.cursor.execute('''
                UPDATE reference_storage SET created_by = ? WHERE created_by = ?
            ''', (to_staff_id, from_staff_id))

            # Update reference_storage refund_by
            self.cursor.execute('''
                UPDATE reference_storage SET refund_by = ? WHERE refund_by = ?
            ''', (to_staff_id, from_staff_id))

            # Update session_timeouts
            self.cursor.execute('''
                UPDATE session_timeouts SET user_id = ? WHERE user_id = ?
            ''', (to_staff_id, from_staff_id))

            # Log the transfer in account_transfers table
            transfer_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute('''
                INSERT INTO account_transfers (from_user_id, to_user_id, transferred_by, transferred_at, reason)
                VALUES (?, ?, ?, ?, ?)
            ''', (from_staff_id, to_staff_id, transferred_by, transfer_time, reason))

            # Update transfer history in users table
            history_entry = f"Transferred to {to_staff['username']} on {transfer_time}: {reason}"
            self.cursor.execute('''
                UPDATE users SET transfer_history = transfer_history || ? || '\n' WHERE user_id = ?
            ''', (history_entry, from_staff_id))

            self.cursor.execute('''
                UPDATE users SET transfer_history = transfer_history || ? || '\n' WHERE user_id = ?
            ''', (f"Received transfer from {from_staff['username']} on {transfer_time}", to_staff_id))

            # Deactivate the old staff account
            self.cursor.execute('''
                UPDATE users SET is_active = 0 WHERE user_id = ?
            ''', (from_staff_id,))

            self.conn.commit()

            return True, f"Account successfully transferred from {from_staff['username']} to {to_staff['username']}."

        except Exception as e:
            self.conn.rollback()
            print(f"Transfer error: {traceback.format_exc()}")
            return False, f"Transfer failed: {str(e)}"

    def get_all_active_staff(self) -> List[Dict]:
        """Get all active staff members."""
        try:
            result = self.execute_query('''
                SELECT user_id, username, first_name, last_name, phone, email
                FROM users
                WHERE user_type = 'staff' AND is_active = 1
                ORDER BY first_name, last_name
            ''')

            staff_list = []
            for row in result:
                staff_list.append({
                    'user_id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'last_name': row[3],
                    'full_name': f"{row[2]} {row[3]} ({row[1]})",
                    'phone': row[4] or '',
                    'email': row[5] or ''
                })
            return staff_list
        except Exception as e:
            print(f"Error getting active staff: {e}")
            return []

    def get_all_staff_for_transfer(self, exclude_id: int) -> List[Dict]:
        """Get all active staff members for transfer, excluding the current one."""
        try:
            result = self.execute_query('''
                SELECT user_id, username, first_name, last_name
                FROM users
                WHERE user_type = 'staff' AND is_active = 1 AND user_id != ?
                ORDER BY first_name, last_name
            ''', (exclude_id,))

            staff_list = []
            for row in result:
                staff_list.append({
                    'user_id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'last_name': row[3],
                    'full_name': f"{row[2]} {row[3]} ({row[1]})"
                })
            return staff_list
        except Exception as e:
            print(f"Error getting staff for transfer: {e}")
            return []

    def toggle_staff_status(self, staff_id: int) -> Tuple[bool, str]:
        """Toggle staff account active/inactive status."""
        try:
            result = self.execute_query(
                "SELECT username, is_active FROM users WHERE user_id = ? AND user_type = 'staff'",
                (staff_id,)
            )

            if not result:
                return False, "Staff account not found."

            username = result[0][0]
            current_status = result[0][1]
            new_status = 0 if current_status == 1 else 1

            success = self.execute_write(
                "UPDATE users SET is_active = ? WHERE user_id = ?",
                (new_status, staff_id)
            )

            if success:
                status_text = "activated" if new_status == 1 else "deactivated"
                return True, f"Staff account '{username}' has been {status_text}."
            else:
                return False, "Failed to update staff status."

        except Exception as e:
            return False, f"Error: {str(e)}"

    def set_session_timeout(self, user_id: int, minutes: int) -> bool:
        """Set session timeout for a user."""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result = self.execute_query(
                "SELECT 1 FROM session_timeouts WHERE user_id = ?",
                (user_id,)
            )

            if result:
                return self.execute_write(
                    "UPDATE session_timeouts SET timeout_minutes = ?, last_activity = ? WHERE user_id = ?",
                    (minutes, current_time, user_id)
                )
            else:
                return self.execute_write(
                    "INSERT INTO session_timeouts (user_id, timeout_minutes, last_activity) VALUES (?, ?, ?)",
                    (user_id, minutes, current_time)
                )
        except Exception as e:
            print(f"Error setting session timeout: {e}")
            return False

    def update_session_timeout(self, user_id: int) -> bool:
        """Update last activity time for session timeout."""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return self.execute_write(
                "UPDATE session_timeouts SET last_activity = ? WHERE user_id = ?",
                (current_time, user_id)
            )
        except Exception:
            return self.set_session_timeout(user_id, 30)

    def check_session_timeout(self, user_id: int) -> bool:
        """Check if user session has timed out."""
        try:
            result = self.execute_query(
                "SELECT timeout_minutes, last_activity FROM session_timeouts WHERE user_id = ?",
                (user_id,)
            )

            if result:
                timeout_minutes, last_activity_str = result[0]
                last_activity = datetime.strptime(last_activity_str, "%Y-%m-%d %H:%M:%S")
                current_time = datetime.now()
                time_diff = (current_time - last_activity).total_seconds() / 60

                return time_diff > timeout_minutes
        except Exception as e:
            print(f"Error checking session timeout: {e}")

        return False

    def clear_all_logs(self) -> bool:
        """Clear all system logs."""
        try:
            return self.execute_write("DELETE FROM activities")
        except Exception as e:
            print(f"Error clearing logs: {e}")
            return False

    def get_weekly_financial_data(self):
        """Get financial data for the current week with improved error handling."""
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_week_str = start_of_week.strftime("%Y-%m-%d")
        end_of_week_str = (start_of_week + timedelta(days=6)).strftime("%Y-%m-%d")

        income_result = self.execute_query(
            "SELECT SUM(amount) FROM financial_transactions WHERE transaction_type = 'income' AND date(timestamp) BETWEEN ? AND ?",
            (start_of_week_str, end_of_week_str)
        )
        weekly_income = income_result[0][0] or 0.0

        expenses_result = self.execute_query(
            "SELECT SUM(amount) FROM financial_transactions WHERE transaction_type = 'expense' AND date(timestamp) BETWEEN ? AND ?",
            (start_of_week_str, end_of_week_str)
        )
        weekly_expenses = expenses_result[0][0] or 0.0

        refunds_result = self.execute_query(
            "SELECT SUM(amount) FROM financial_transactions WHERE transaction_type = 'refund' AND date(timestamp) BETWEEN ? AND ?",
            (start_of_week_str, end_of_week_str)
        )
        weekly_refunds = refunds_result[0][0] or 0.0

        items_result = self.execute_query('''
            SELECT item, SUM(quantity) as total_quantity 
            FROM rental_out_records 
            WHERE date BETWEEN ? AND ? 
            GROUP BY item 
            ORDER BY total_quantity DESC
        ''', (start_of_week_str, end_of_week_str))

        total_income_result = self.execute_query(
            "SELECT SUM(amount) FROM financial_transactions WHERE transaction_type = 'income'"
        )
        total_income = total_income_result[0][0] or 0.0

        total_expenses_result = self.execute_query(
            "SELECT SUM(amount) FROM financial_transactions WHERE transaction_type = 'expense'"
        )
        total_expenses = total_expenses_result[0][0] or 0.0

        total_refunds_result = self.execute_query(
            "SELECT SUM(amount) FROM financial_transactions WHERE transaction_type = 'refund'"
        )
        total_refunds = total_refunds_result[0][0] or 0.0

        available_balance = total_income - total_expenses - total_refunds

        return {
            'weekly_income': weekly_income,
            'weekly_expenses': weekly_expenses,
            'weekly_refunds': weekly_refunds,
            'weekly_items': items_result,
            'start_date': start_of_week_str,
            'end_date': end_of_week_str,
            'available_balance': available_balance,
            'total_refunds': total_refunds
        }

    def get_overdue_rentals(self):
        """Get rentals that are not returned and are overdue with highlighting."""
        try:
            threshold_result = self.execute_query(
                "SELECT setting_value FROM system_settings WHERE setting_key = 'overdue_days_threshold'"
            )
            overdue_threshold = int(threshold_result[0][0]) if threshold_result else 2

            self.update_overdue_status(overdue_threshold)

            result = self.execute_query('''
                SELECT 
                    reference,
                    customer_name,
                    phone,
                    area,
                    item,
                    quantity,
                    date,
                    time_out,
                    CASE 
                        WHEN days_with_customer > 0 THEN days_with_customer
                        ELSE CAST(julianday('now') - julianday(date) AS INTEGER)
                    END as days_with_customer,
                    deposit_paid,
                    overdue,
                    overdue_days,
                    refund_processed,
                    refund_amount
                FROM rental_out_records 
                WHERE status = 'Active' 
                ORDER BY date ASC
            ''')
            return result
        except Exception as e:
            print(f"Error getting overdue rentals: {e}")
            return []

    def update_overdue_status(self, threshold_days: int = 2):
        """Update overdue status for all active rentals."""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")

            self.execute_write('''
                UPDATE rental_out_records 
                SET days_with_customer = CAST(julianday(?) - julianday(date) AS INTEGER)
                WHERE status = 'Active'
            ''', (current_date,))

            self.execute_write('''
                UPDATE rental_out_records 
                SET overdue = 1, overdue_days = CAST(julianday(?) - julianday(date) AS INTEGER) - ?
                WHERE status = 'Active' 
                AND CAST(julianday(?) - julianday(date) AS INTEGER) > ?
            ''', (current_date, threshold_days, current_date, threshold_days))

            self.execute_write('''
                UPDATE rental_out_records 
                SET overdue = 0, overdue_days = 0
                WHERE status = 'Active' 
                AND CAST(julianday(?) - julianday(date) AS INTEGER) <= ?
            ''', (current_date, threshold_days))

        except Exception as e:
            print(f"Error updating overdue status: {e}")

    def get_active_rentals_summary(self):
        """Get summary of active rentals with robust NULL handling."""
        try:
            result = self.execute_query('''
                SELECT 
                    COUNT(*) as total_active,
                    SUM(quantity) as total_items,
                    COALESCE(SUM(deposit_paid), 0.0) as total_deposits,
                    COALESCE(SUM(refund_amount), 0.0) as total_refunds
                FROM rental_out_records 
                WHERE status = 'Active'
            ''')
            if result:
                row = result[0]
                total_active = row[0] if row[0] is not None else 0
                total_items = row[1] if row[1] is not None else 0
                total_deposits = row[2] if row[2] is not None else 0.0
                total_refunds = row[3] if row[3] is not None else 0.0
                return (total_active, total_items, total_deposits, total_refunds)
            return (0, 0, 0.0, 0.0)
        except Exception as e:
            print(f"Error getting active rentals summary: {e}")
            return (0, 0, 0.0, 0.0)

    def get_rental_by_reference(self, reference: str):
        """Get rental data by reference number."""
        try:
            result = self.execute_query('''
                SELECT customer_name, phone, area, item, quantity, rate_type, deposit_paid, date, time_out, receipt_printed, refund_processed, refund_amount
                FROM rental_out_records 
                WHERE reference = ?
            ''', (reference,))
            return result[0] if result else None
        except Exception as e:
            print(f"Error getting rental by reference: {e}")
            return None

    def get_complete_rental_data_by_reference(self, reference: str):
        """Get complete rental data by reference number - ALL FIELDS for printing."""
        try:
            result = self.execute_query('''
                SELECT customer_name, phone, area, item, quantity, rate_type, deposit_paid, 
                       date, time_out, receipt_printed, days_with_customer, refund_processed, refund_amount
                FROM rental_out_records 
                WHERE reference = ?
            ''', (reference,))

            if result:
                row = result[0]
                return {
                    'customer_name': row[0],
                    'phone': row[1],
                    'area': row[2],
                    'item': row[3],
                    'quantity': row[4],
                    'rate_type': row[5],
                    'deposit_paid': row[6],
                    'date': row[7],
                    'time_out': row[8],
                    'receipt_printed': row[9],
                    'days_with_customer': row[10] if len(row) > 10 else 1,
                    'refund_processed': row[11] if len(row) > 11 else 0,
                    'refund_amount': row[12] if len(row) > 12 else 0.0
                }
            return None
        except Exception as e:
            print(f"Error getting complete rental data: {e}")
            return None

    def mark_item_as_returned(self, reference: str, customer_name: str, phone: str, item: str) -> Tuple[bool, str]:
        """Mark an item as returned by reference number with relaxed validation."""
        try:
            rental_data = self.get_rental_by_reference(reference)
            if not rental_data:
                return False, f"Reference '{reference}' not found in database!"

            db_customer_name = rental_data[0].replace('*', '').strip().lower()
            entered_customer_name = customer_name.replace('*', '').strip().lower()

            if db_customer_name != entered_customer_name:
                return False, f"Customer name doesn't match!\n\nEntered: {customer_name}\nDatabase: {rental_data[0]}"

            db_item = str(rental_data[3]).strip().lower()
            entered_item = str(item).strip().lower()
            if db_item != entered_item:
                return False, f"Item doesn't match!\n\nEntered: {item}\nDatabase: {rental_data[3]}"

            current_date = datetime.now().strftime("%Y-%m-%d")
            days_result = self.execute_query(
                "SELECT CAST(julianday(?) - julianday(date) AS INTEGER) FROM rental_out_records WHERE reference = ?",
                (current_date, reference)
            )
            days_with_customer = days_result[0][0] if days_result else 1
            days_with_customer = max(1, days_with_customer)

            success = self.execute_write('''
                UPDATE rental_out_records 
                SET status = 'Returned', overdue = 0, overdue_days = 0, days_with_customer = ?
                WHERE reference = ? AND status = 'Active'
            ''', (days_with_customer, reference))

            if success:
                current_date = datetime.now().strftime("%Y-%m-%d")
                self.execute_write('''
                    UPDATE reference_storage 
                    SET status = 'Returned', date_returned = ?
                    WHERE reference_number = ? AND status = 'Active'
                ''', (current_date, reference))

            return success, f"Item marked as returned successfully. Rental days: {days_with_customer}"
        except Exception as e:
            print(f"Error marking item as returned: {e}")
            return False, f"Error: {str(e)}"

    def process_refund(self, reference, customer_name, deposit_paid, refund_amount, reason, user_id):
        """Process a refund."""
        try:
            transaction_id = f"REF{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Update rental_out_records
            self.execute_write('''
                UPDATE rental_out_records 
                SET refund_processed = 1, refund_amount = ?, refund_reason = ?, refund_by = ?
                WHERE reference = ?
            ''', (refund_amount, reason, user_id, reference))

            # Update reference_storage
            self.execute_write('''
                UPDATE reference_storage 
                SET refund_amount = ?, refund_reason = ?, refund_by = ?
                WHERE reference_number = ?
            ''', (refund_amount, reason, user_id, reference))

            # Record financial transaction
            self.execute_write('''
                INSERT INTO financial_transactions
                (transaction_id, timestamp, transaction_type, amount, description, user_id, category, reference_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (transaction_id, timestamp, 'refund', refund_amount, reason, user_id, 'Refunds', reference))

            return True, f"Refund of GH₵{refund_amount:,.2f} processed successfully."
        except Exception as e:
            return False, f"Error processing refund: {str(e)}"

    def add_to_not_returned(self, reference: str, customer_name: str, phone: str,
                            area: str, item: str, quantity: int, rate_type: str,
                            deposit_paid: float, user_id: int):
        """Add a rental item to not returned list."""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            current_time = datetime.now().strftime("%H:%M")

            success = self.execute_write('''
                INSERT INTO rental_out_records
                (reference, customer_name, phone, area, item, quantity, rate_type, 
                 date, time_out, user_id, deposit_paid, status, overdue)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (reference, customer_name, phone, area, item, quantity, rate_type,
                  current_date, current_time, user_id, deposit_paid, 'Active', 0))

            return success
        except Exception as e:
            print(f"Error adding to not returned list: {e}")
            return False

    def record_expense(self, amount: float, description: str, category: str, user_id: int) -> Tuple[bool, str]:
        """Record an expense transaction with STRICT balance validation."""
        try:
            weekly_data = self.get_weekly_financial_data()
            available_balance = weekly_data['available_balance']

            if amount > available_balance:
                return False, f"❌ EXPENSE REJECTED!\n\nExpense (GH₵{amount:,.2f}) exceeds available balance (GH₵{available_balance:,.2f})\n\nYou cannot add this expense."

            transaction_id = f"EXP{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            success = self.execute_write('''
                INSERT INTO financial_transactions
                (transaction_id, timestamp, transaction_type, amount, description, user_id, category)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (transaction_id, timestamp, 'expense', amount, description, user_id, category))

            if success:
                return True, "Expense recorded successfully."
            else:
                return False, "Failed to record expense."

        except Exception as e:
            print(f"Error recording expense: {e}")
            return False, f"Error: {str(e)}"

    def record_income(self, amount: float, description: str, user_id: int, category: str = "Rental Income") -> Tuple[
        bool, str]:
        """Record an income transaction."""
        try:
            transaction_id = f"INC{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            success = self.execute_write('''
                INSERT INTO financial_transactions
                (transaction_id, timestamp, transaction_type, amount, description, user_id, category)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (transaction_id, timestamp, 'income', amount, description, user_id, category))

            if success:
                return True, "Income recorded successfully."
            else:
                return False, "Failed to record income."

        except Exception as e:
            print(f"Error recording income: {e}")
            return False, f"Error: {str(e)}"

    def get_expense_categories(self):
        """Get all expense categories."""
        try:
            result = self.execute_query("SELECT category_name FROM expense_categories ORDER BY category_name")
            return [row[0] for row in result]
        except Exception as e:
            print(f"Error getting expense categories: {e}")
            return []

    def add_expense_category(self, category_name: str, description: str = "") -> Tuple[bool, str]:
        """Add a new expense category."""
        try:
            success = self.execute_write(
                "INSERT INTO expense_categories (category_name, description) VALUES (?, ?)",
                (category_name, description)
            )
            if success:
                return True, "Category added successfully."
            else:
                return False, "Failed to add category."
        except sqlite3.IntegrityError:
            return False, "Category already exists."
        except Exception as e:
            return False, f"Error: {str(e)}"

    def check_receipt_printed(self, reference: str) -> bool:
        """Check if receipt has been printed for a reference."""
        try:
            result = self.execute_query(
                "SELECT receipt_printed FROM rental_out_records WHERE reference = ?",
                (reference,)
            )
            if result and result[0][0] == 1:
                return True
            return False
        except Exception as e:
            print(f"Error checking receipt status: {e}")
            return False

    def mark_receipt_printed(self, reference: str) -> bool:
        """Mark receipt as printed for a reference."""
        try:
            return self.execute_write(
                "UPDATE rental_out_records SET receipt_printed = 1 WHERE reference = ?",
                (reference,)
            )
        except Exception as e:
            print(f"Error marking receipt as printed: {e}")
            return False

    def change_staff_password_by_admin(self, staff_id: int, new_password: str) -> Tuple[bool, str]:
        """Change staff password by admin with STRONG validation."""
        try:
            # Check if staff exists
            result = self.execute_query(
                "SELECT username, user_type FROM users WHERE user_id = ?",
                (staff_id,)
            )

            if not result:
                return False, "Staff account not found."

            username, user_type = result[0]

            if user_type != 'staff':
                return False, "Only staff account passwords can be changed."

            # STRONG PASSWORD VALIDATION
            errors = []

            # Length check
            if len(new_password) < 8:
                errors.append("Password must be at least 8 characters long.")

            # Character diversity checks
            if not re.search(r'[A-Z]', new_password):
                errors.append("Password must contain at least one uppercase letter.")

            if not re.search(r'[a-z]', new_password):
                errors.append("Password must contain at least one lowercase letter.")

            if not re.search(r'[0-9]', new_password):
                errors.append("Password must contain at least one number.")

            if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', new_password):
                errors.append("Password must contain at least one special character.")

            # Check for common patterns
            common_passwords = ['password', '123456', 'admin123', 'qwerty', 'letmein']
            if new_password.lower() in common_passwords:
                errors.append("Password is too common. Choose a more unique password.")

            # Check for sequential characters
            if re.search(r'(.)\1{2,}', new_password):
                errors.append("Password cannot contain 3 or more repeating characters.")

            # Check for sequential numbers (123, 456, etc.)
            if re.search(r'(012|123|234|345|456|567|678|789|890)', new_password):
                errors.append("Password cannot contain sequential numbers.")

            if errors:
                error_message = "Password validation failed:\n\n" + "\n".join(f"• {error}" for error in errors)
                return False, error_message

            # Hash the password
            hashed_password = PasswordManager.hash_password(new_password)

            # Update password in database
            success = self.execute_write(
                "UPDATE users SET password = ? WHERE user_id = ?",
                (hashed_password, staff_id)
            )

            if success:
                return True, f"Password changed successfully for {username}."
            else:
                return False, "Failed to change password due to database error."

        except Exception as e:
            return False, f"System error: {str(e)}"


class LoginScreen:
    """Main login screen for both admin and staff."""

    def __init__(self, master, main_app_callback):
        self.master = master
        self.master.title("Rental Management System - v6.0")
        self.master.geometry("400x500")
        self.master.configure(bg='#ecf0f1')
        self.master.resizable(False, False)

        self.db = DatabaseManager()
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.main_app_callback = main_app_callback
        self.password_visible = False

        self.create_widgets()
        self.center_window()
        self.master.bind('<Return>', lambda event: self.login())

    def center_window(self):
        """Center the window on screen."""
        self.master.update_idletasks()
        width = self.master.winfo_width()
        height = self.master.winfo_height()
        x = (self.master.winfo_screenwidth() // 2) - (width // 2)
        y = (self.master.winfo_screenheight() // 2) - (height // 2)
        self.master.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        """Create login widgets with black border."""
        main_frame = tk.Frame(
            self.master,
            bg='#ffffff',
            padx=30,
            pady=30,
            relief='solid',
            borderwidth=2,
            highlightbackground='black',
            highlightthickness=2
        )
        main_frame.place(relx=0.5, rely=0.5, anchor='center', width=350, height=450)

        header_frame = tk.Frame(main_frame, bg='#ffffff')
        header_frame.pack(pady=(0, 20))

        title_label = tk.Label(
            header_frame,
            text="WELCOME BACK,",
            font=('Arial', 18, 'bold'),
            bg='#ffffff'
        )
        title_label.pack()

        form_frame = tk.Frame(main_frame, bg='#ffffff')
        form_frame.pack(fill=tk.X, pady=10)

        # Username field
        tk.Label(
            form_frame,
            text="USERNAME",
            bg='#ffffff',
            font=('Arial', 11)
        ).grid(row=0, column=0, sticky=tk.W, pady=8)

        username_entry = tk.Entry(
            form_frame,
            textvariable=self.username_var,
            font=('Arial', 12),
            bd=2,
            relief='solid',
            highlightbackground='black',
            highlightthickness=1
        )
        username_entry.grid(row=0, column=1, sticky=tk.EW, pady=8, padx=(10, 0))
        username_entry.focus_set()

        # Password field with eye icon - WITHOUT BOX
        tk.Label(
            form_frame,
            text="PASSWORD",
            bg='#ffffff',
            font=('Arial', 11)
        ).grid(row=1, column=0, sticky=tk.W, pady=8)

        password_frame = tk.Frame(form_frame, bg='#ffffff')
        password_frame.grid(row=1, column=1, sticky=tk.EW, pady=8, padx=(10, 0))

        self.password_entry = tk.Entry(
            password_frame,
            textvariable=self.password_var,
            show="•",
            font=('Arial', 12),
            bd=2,
            relief='solid',
            width=20,
            highlightbackground='black',
            highlightthickness=1
        )
        self.password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Eye icon for password visibility - FIXED POSITION (no box)
        self.eye_icon = tk.Label(
            password_frame,
            text="👁️",
            cursor="hand2",
            bg='white',
            fg='#7f8c8d',
            font=('Arial', 14)
        )
        self.eye_icon.pack(side=tk.RIGHT, padx=(8, 0))
        self.eye_icon.bind("<Button-1>", lambda e: self.toggle_password_visibility())

        form_frame.columnconfigure(1, weight=1)

        button_frame = tk.Frame(main_frame, bg='#ffffff')
        button_frame.pack(fill=tk.X, pady=(15, 0))

        login_btn = tk.Button(
            button_frame,
            text="LOGIN",
            command=self.login,
            bg='#2980b9',
            fg='white',
            font=('Arial', 11, 'bold'),
            bd=2,
            activebackground='#1a5276',
            activeforeground='white',
            relief='raised',
            highlightbackground='black',
            highlightthickness=1
        )
        login_btn.pack(fill=tk.X, pady=4, ipady=5)

        info_label = tk.Label(
            main_frame,
            text="Login to your account",
            bg='#ffffff',
            font=('Arial', 9, 'italic'),
            fg='#7f8c8d'
        )
        info_label.pack(pady=(10, 0))

    def toggle_password_visibility(self):
        """Toggle password visibility with full eye icon."""
        self.password_visible = not self.password_visible
        if self.password_visible:
            self.password_entry.config(show="")
            self.eye_icon.config(text="👁️", fg='#2980b9')
        else:
            self.password_entry.config(show="•")
            self.eye_icon.config(text="👁️", fg='#7f8c8d')

    def login(self):
        """Handle login attempt."""
        username = self.username_var.get().strip()
        password = self.password_var.get()

        if not username or not password:
            messagebox.showerror("Login Error", "Please enter username and password.")
            return

        user_info = self.db.authenticate_user(username, password)

        if user_info:
            if user_info.get('is_active', 1) != 1:
                messagebox.showerror("Login Error", "This account has been deactivated. Please contact administrator.")
                return

            self.db.log_activity(user_info['user_id'], "Logged in")
            self.master.destroy()

            main_app_window = tk.Toplevel()
            main_app_window.state('zoomed')

            self.main_app_callback(user_info, main_app_window)
        else:
            messagebox.showerror("Login Error", "Invalid username or password.")


class AdminDashboard:
    """Admin dashboard with staff management and system controls."""

    def __init__(self, master, user_info, logout_callback):
        self.master = master
        self.user_info = user_info
        self.logout_callback = logout_callback

        self.master.title(f"Admin Dashboard - {user_info['first_name']} {user_info['last_name']}")
        self.master.configure(bg='#2c3e50')

        self.db = DatabaseManager()

        self.session_check_thread = None
        self.session_running = True

        self.setup_ui()
        self.start_session_check()

    def setup_ui(self):
        """Setup admin dashboard UI."""
        header_frame = tk.Frame(self.master, bg='#8e44ad', height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="ADMIN DASHBOARD",
            font=('Arial', 18, 'bold'),
            bg='#8e44ad',
            fg='white'
        )
        title_label.pack(side=tk.LEFT, padx=20)

        right_frame = tk.Frame(header_frame, bg='#8e44ad')
        right_frame.pack(side=tk.RIGHT, padx=20)

        user_label = tk.Label(
            right_frame,
            text=f"Admin: {self.user_info['first_name']} {self.user_info['last_name']}",
            font=('Arial', 12, 'bold'),
            bg='#8e44ad',
            fg='white'
        )
        user_label.pack(side=tk.LEFT, padx=(0, 15))

        def confirm_logout():
            if messagebox.askyesno("Confirm Logout", "Are you sure you want to log out?"):
                self.logout()

        logout_btn = tk.Button(
            right_frame,
            text="LOGOUT",
            command=confirm_logout,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 10, 'bold'),
            width=10
        )
        logout_btn.pack(side=tk.LEFT)

        main_frame = tk.Frame(self.master, bg='#ecf0f1')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        staff_frame = tk.Frame(self.notebook, bg='#ecf0f1')
        self.notebook.add(staff_frame, text="Staff Management")
        self.setup_staff_management(staff_frame)

        finance_frame = tk.Frame(self.notebook, bg='#ecf0f1')
        self.notebook.add(finance_frame, text="Financial Dashboard")
        self.setup_financial_dashboard(finance_frame)

        logs_frame = tk.Frame(self.notebook, bg='#ecf0f1')
        self.notebook.add(logs_frame, text="System Logs")
        self.setup_system_logs(logs_frame)

        settings_frame = tk.Frame(self.notebook, bg='#ecf0f1')
        self.notebook.add(settings_frame, text="Settings")
        self.setup_settings(settings_frame)

        self.db.log_activity(self.user_info['user_id'], "Accessed admin dashboard")

    def start_session_check(self):
        """Start thread to check for session timeout."""

        def check_session():
            while self.session_running:
                time.sleep(60)
                if self.db.check_session_timeout(self.user_info['user_id']):
                    self.master.after(0, self.session_timeout)
                    break

        self.session_check_thread = threading.Thread(target=check_session, daemon=True)
        self.session_check_thread.start()

    def session_timeout(self):
        """Handle session timeout."""
        if messagebox.askyesno("Session Timeout",
                               "Your session has expired due to inactivity. Would you like to login again?"):
            self.logout()
        else:
            self.logout()

    def setup_staff_management(self, parent):
        """Setup staff management interface with enhanced features."""
        # Control frame for buttons
        control_frame = tk.Frame(parent, bg='#ecf0f1', pady=10)
        control_frame.pack(fill=tk.X)

        create_btn = tk.Button(
            control_frame,
            text="Create New Staff",
            command=self.create_staff_account,
            bg='#27ae60',
            fg='white',
            font=('Arial', 11)
        )
        create_btn.pack(side=tk.LEFT, padx=5)

        edit_btn = tk.Button(
            control_frame,
            text="Edit Selected Staff",
            command=self.edit_staff_account,
            bg='#3498db',
            fg='white',
            font=('Arial', 11)
        )
        edit_btn.pack(side=tk.LEFT, padx=5)

        toggle_btn = tk.Button(
            control_frame,
            text="Activate/Deactivate",
            command=self.toggle_staff_status,
            bg='#f39c12',
            fg='white',
            font=('Arial', 11)
        )
        toggle_btn.pack(side=tk.LEFT, padx=5)

        refresh_btn = tk.Button(
            control_frame,
            text="Refresh",
            command=self.load_staff_list,
            bg='#9b59b6',
            fg='white',
            font=('Arial', 11)
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)

        # Double click binding for editing
        self.staff_tree = None

        # List frame
        list_frame = tk.Frame(parent, bg='#ecf0f1')
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        columns = ("ID", "Username", "First Name", "Last Name", "Phone", "Email", "Type", "Status", "Active", "Last Login")
        self.staff_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)

        col_widths = [50, 100, 100, 100, 100, 150, 80, 80, 80, 150]
        for i, col in enumerate(columns):
            self.staff_tree.heading(col, text=col)
            self.staff_tree.column(col, width=col_widths[i], anchor="center")

        # Bind double click to edit
        self.staff_tree.bind('<Double-Button-1>', lambda e: self.edit_staff_account())

        self.staff_tree.tag_configure('inactive', foreground='gray')

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.staff_tree.yview)
        self.staff_tree.configure(yscrollcommand=scrollbar.set)

        self.staff_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.load_staff_list()

    def edit_staff_account(self):
        """Open dialog to edit selected staff account with tabs for different operations."""
        selected = self.staff_tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a staff member to edit.")
            return

        staff_id = self.staff_tree.item(selected[0])['values'][0]
        self.open_staff_edit_dialog(staff_id)

    def open_staff_edit_dialog(self, staff_id: int):
        """Open comprehensive staff edit dialog with tabs."""
        # Get staff data
        staff_data = self.db.get_staff_by_id(staff_id)
        if not staff_data:
            messagebox.showerror("Error", "Staff data not found.")
            return

        dialog = tk.Toplevel(self.master)
        dialog.title(f"Edit Staff: {staff_data['first_name']} {staff_data['last_name']}")
        dialog.geometry("600x650")
        dialog.configure(bg='#2c3e50')
        dialog.grab_set()
        dialog.resizable(False, False)

        # Main container
        main_frame = tk.Frame(dialog, bg='#2c3e50', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        tk.Label(main_frame, text=f"EDIT STAFF ACCOUNT",
                 font=('Arial', 18, 'bold'), bg='#2c3e50', fg='white'
                 ).pack(pady=(0, 10))

        tk.Label(main_frame, text=f"Editing: {staff_data['first_name']} {staff_data['last_name']} ({staff_data['username']})",
                 font=('Arial', 12), bg='#2c3e50', fg='#f39c12'
                 ).pack(pady=(0, 20))

        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Tab 1: Basic Information
        info_frame = tk.Frame(notebook, bg='#ecf0f1', padx=20, pady=20)
        notebook.add(info_frame, text="Basic Information")

        # Tab 2: Change Password
        password_frame = tk.Frame(notebook, bg='#ecf0f1', padx=20, pady=20)
        notebook.add(password_frame, text="Change Password")

        # Tab 3: Transfer Account
        transfer_frame = tk.Frame(notebook, bg='#ecf0f1', padx=20, pady=20)
        notebook.add(transfer_frame, text="Transfer Assignment")

        # ========== BASIC INFORMATION TAB ==========
        # Username
        tk.Label(info_frame, text="Username Required", bg='#ecf0f1', font=('Arial', 11, 'bold')).grid(row=0, column=0, sticky='w', pady=10)
        username_var = tk.StringVar(value=staff_data['username'])
        username_entry = tk.Entry(info_frame, textvariable=username_var, width=30, font=('Arial', 11), bd=2, relief='solid')
        username_entry.grid(row=0, column=1, pady=10, padx=(10, 0))

        # First Name
        tk.Label(info_frame, text="First Name Required", bg='#ecf0f1', font=('Arial', 11, 'bold')).grid(row=1, column=0, sticky='w', pady=10)
        first_name_var = tk.StringVar(value=staff_data['first_name'])
        first_name_entry = tk.Entry(info_frame, textvariable=first_name_var, width=30, font=('Arial', 11), bd=2, relief='solid')
        first_name_entry.grid(row=1, column=1, pady=10, padx=(10, 0))

        # Last Name
        tk.Label(info_frame, text="Last Name Required", bg='#ecf0f1', font=('Arial', 11, 'bold')).grid(row=2, column=0, sticky='w', pady=10)
        last_name_var = tk.StringVar(value=staff_data['last_name'])
        last_name_entry = tk.Entry(info_frame, textvariable=last_name_var, width=30, font=('Arial', 11), bd=2, relief='solid')
        last_name_entry.grid(row=2, column=1, pady=10, padx=(10, 0))

        # Phone
        tk.Label(info_frame, text="Phone", bg='#ecf0f1', font=('Arial', 11)).grid(row=3, column=0, sticky='w', pady=10)
        phone_var = tk.StringVar(value=staff_data['phone'])
        phone_entry = tk.Entry(info_frame, textvariable=phone_var, width=30, font=('Arial', 11), bd=2, relief='solid')
        phone_entry.grid(row=3, column=1, pady=10, padx=(10, 0))

        # Email
        tk.Label(info_frame, text="Email", bg='#ecf0f1', font=('Arial', 11)).grid(row=4, column=0, sticky='w', pady=10)
        email_var = tk.StringVar(value=staff_data['email'])
        email_entry = tk.Entry(info_frame, textvariable=email_var, width=30, font=('Arial', 11), bd=2, relief='solid')
        email_entry.grid(row=4, column=1, pady=10, padx=(10, 0))

        # Status info
        status_text = "Active" if staff_data['is_active'] == 1 else "Inactive"
        status_color = '#27ae60' if staff_data['is_active'] == 1 else '#e74c3c'
        tk.Label(info_frame, text="Status:", bg='#ecf0f1', font=('Arial', 11, 'bold')).grid(row=5, column=0, sticky='w', pady=10)
        tk.Label(info_frame, text=status_text, bg='#ecf0f1', fg=status_color, font=('Arial', 11, 'bold')).grid(row=5, column=1, sticky='w', pady=10, padx=(10, 0))

        # Created at
        tk.Label(info_frame, text="Created:", bg='#ecf0f1', font=('Arial', 11)).grid(row=6, column=0, sticky='w', pady=10)
        tk.Label(info_frame, text=staff_data['created_at'], bg='#ecf0f1', font=('Arial', 11)).grid(row=6, column=1, sticky='w', pady=10, padx=(10, 0))

        # Last login
        tk.Label(info_frame, text="Last Login:", bg='#ecf0f1', font=('Arial', 11)).grid(row=7, column=0, sticky='w', pady=10)
        tk.Label(info_frame, text=staff_data['last_login'], bg='#ecf0f1', font=('Arial', 11)).grid(row=7, column=1, sticky='w', pady=10, padx=(10, 0))

        # ========== CHANGE PASSWORD TAB ==========
        # New Password with eye icon
        tk.Label(password_frame, text="New Password Required", bg='#ecf0f1', font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        new_pass_frame = tk.Frame(password_frame, bg='#ecf0f1')
        new_pass_frame.pack(fill=tk.X, pady=(0, 15))
        new_pass_var = tk.StringVar()
        new_pass_entry = tk.Entry(new_pass_frame, textvariable=new_pass_var, show="•", width=30, font=('Arial', 11),
                                  bd=2, relief='solid', bg='white')
        new_pass_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        new_pass_eye = tk.Label(new_pass_frame, text="👁️", cursor="hand2",
                               bg='white', fg='#7f8c8d', font=('Arial', 14))
        new_pass_eye.pack(side=tk.RIGHT, padx=(5, 0))
        new_pass_eye.bind("<Button-1>", lambda e: self.toggle_password_visibility(new_pass_entry))

        # Confirm Password with eye icon
        tk.Label(password_frame, text="Confirm New Password Required", bg='#ecf0f1', font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        confirm_pass_frame = tk.Frame(password_frame, bg='#ecf0f1')
        confirm_pass_frame.pack(fill=tk.X, pady=(0, 20))
        confirm_pass_var = tk.StringVar()
        confirm_pass_entry = tk.Entry(confirm_pass_frame, textvariable=confirm_pass_var, show="•", width=30, font=('Arial', 11),
                                      bd=2, relief='solid', bg='white')
        confirm_pass_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        confirm_pass_eye = tk.Label(confirm_pass_frame, text="👁️", cursor="hand2",
                                   bg='white', fg='#7f8c8d', font=('Arial', 14))
        confirm_pass_eye.pack(side=tk.RIGHT, padx=(5, 0))
        confirm_pass_eye.bind("<Button-1>", lambda e: self.toggle_password_visibility(confirm_pass_entry))

        # Password requirements
        requirements_text = """Password Requirements:
• At least 8 characters long
• At least one uppercase letter (A-Z)
• At least one lowercase letter (a-z)
• At least one number (0-9)
• At least one special character (!@#$%^&*)
• No common passwords
• No 3+ repeating characters"""

        req_frame = tk.Frame(password_frame, bg='#f0f0f0', relief='solid', bd=1)
        req_frame.pack(fill=tk.X, pady=10)
        tk.Label(req_frame, text=requirements_text, bg='#f0f0f0', fg='#2c3e50',
                font=('Arial', 10), justify=tk.LEFT, padx=10, pady=10).pack()

        # ========== TRANSFER ACCOUNT TAB ==========
        # Get list of active staff for transfer (excluding current staff)
        transfer_targets = self.db.get_all_staff_for_transfer(staff_id)

        if transfer_targets:
            tk.Label(transfer_frame, text="Transfer Account To:", bg='#ecf0f1', font=('Arial', 12, 'bold')).pack(anchor='w', pady=(0, 10))

            # Target staff selection
            target_frame = tk.Frame(transfer_frame, bg='#ecf0f1')
            target_frame.pack(fill=tk.X, pady=(0, 15))

            tk.Label(target_frame, text="Select Staff Required", bg='#ecf0f1', font=('Arial', 11)).pack(anchor='w', pady=(0, 5))

            target_var = tk.StringVar()
            target_combo = ttk.Combobox(target_frame, textvariable=target_var,
                                       values=[s['full_name'] for s in transfer_targets],
                                       width=40, font=('Arial', 11))
            target_combo.pack(fill=tk.X)

            # Reason for transfer
            tk.Label(transfer_frame, text="Reason for Transfer", bg='#ecf0f1', font=('Arial', 11)).pack(anchor='w', pady=(10, 5))
            reason_text = tk.Text(transfer_frame, height=4, width=40, font=('Arial', 11), bd=2, relief='solid')
            reason_text.pack(fill=tk.X, pady=(0, 10))

            # Transfer warning
            warning_frame = tk.Frame(transfer_frame, bg='#ffe6e6', relief='solid', bd=1)
            warning_frame.pack(fill=tk.X, pady=10)
            tk.Label(warning_frame, text="⚠️ IMPORTANT WARNING",
                    bg='#ffe6e6', fg='#c0392b', font=('Arial', 11, 'bold')).pack(pady=(5, 0))
            warning_text = """Transferring this account will:
• Move all rentals to the new staff member
• Move all transactions to the new staff member
• Deactivate this staff account
• Log the transfer for audit purposes

This action CANNOT be undone!"""
            tk.Label(warning_frame, text=warning_text, bg='#ffe6e6', fg='#2c3e50',
                    font=('Arial', 10), justify=tk.LEFT, padx=10, pady=5).pack()
        else:
            tk.Label(transfer_frame, text="No other active staff members available for transfer.",
                    bg='#ecf0f1', fg='#e74c3c', font=('Arial', 12, 'bold')).pack(pady=50)

        # ========== BUTTONS ==========
        button_frame = tk.Frame(main_frame, bg='#2c3e50')
        button_frame.pack(fill=tk.X, pady=(10, 0))

        # Save Basic Info function
        def save_basic_info():
            username = username_var.get().strip()
            first_name = first_name_var.get().strip()
            last_name = last_name_var.get().strip()
            phone = phone_var.get().strip()
            email = email_var.get().strip()

            if not all([username, first_name, last_name]):
                messagebox.showerror("Error", "Please fill in all required fields.")
                return

            # Validate username
            if len(username) < 3:
                messagebox.showerror("Error", "Username must be at least 3 characters.")
                return

            # Validate phone if provided
            if phone and not re.match(r'^[0-9+\- ]+$', phone):
                messagebox.showerror("Error", "Phone number can only contain digits, plus, hyphen, or space.")
                return

            # Validate email if provided
            if email:
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, email):
                    messagebox.showerror("Error", "Invalid email format. Please enter a valid email address.")
                    return

            success, message = self.db.update_staff_info(staff_id, username, first_name, last_name, phone, email)

            if success:
                messagebox.showinfo("Success", "✅ Basic information updated successfully!")
                self.db.log_activity(self.user_info['user_id'], f"Updated staff info for {username}")
                self.load_staff_list()
                dialog.destroy()
            else:
                messagebox.showerror("Error", f"❌ Update failed:\n{message}")

        # Change Password function
        def change_password():
            new_pass = new_pass_var.get()
            confirm_pass = confirm_pass_var.get()

            if not new_pass or not confirm_pass:
                messagebox.showerror("Error", "Please fill in both password fields.")
                return

            if new_pass != confirm_pass:
                messagebox.showerror("Error", "Passwords do not match.")
                return

            success, message = self.db.change_staff_password(staff_id, new_pass)

            if success:
                messagebox.showinfo("Success", f"✅ {message}")
                self.db.log_activity(self.user_info['user_id'], f"Changed password for staff ID {staff_id}")
                self.load_staff_list()
                dialog.destroy()
            else:
                messagebox.showerror("Error", f"❌ Password change failed:\n{message}")

        # Transfer Account function
        def transfer_account():
            if not transfer_targets:
                messagebox.showerror("Error", "No transfer targets available.")
                return

            selected_target = target_var.get()
            reason = reason_text.get("1.0", tk.END).strip()

            if not selected_target:
                messagebox.showerror("Error", "Please select a target staff member.")
                return

            # Find target staff ID
            target_staff = None
            for s in transfer_targets:
                if s['full_name'] == selected_target:
                    target_staff = s
                    break

            if not target_staff:
                messagebox.showerror("Error", "Selected staff not found.")
                return

            # Double-check with user
            confirm_msg = f"⚠️ CONFIRM ACCOUNT TRANSFER ⚠️\n\n"
            confirm_msg += f"From: {staff_data['first_name']} {staff_data['last_name']} ({staff_data['username']})\n"
            confirm_msg += f"To: {target_staff['first_name']} {target_staff['last_name']} ({target_staff['username']})\n\n"
            confirm_msg += f"Reason: {reason or 'Not specified'}\n\n"
            confirm_msg += "This will:\n"
            confirm_msg += "• Move ALL rentals to new staff\n"
            confirm_msg += "• Move ALL transactions to new staff\n"
            confirm_msg += "• Deactivate current staff account\n"
            confirm_msg += "• Log the transfer permanently\n\n"
            confirm_msg += "This action CANNOT be undone!\n\n"
            confirm_msg += "Are you ABSOLUTELY sure?"

            if not messagebox.askyesno("⚠️ CONFIRM TRANSFER", confirm_msg, icon='warning'):
                return

            success, message = self.db.transfer_staff_account(staff_id, target_staff['user_id'],
                                                             self.user_info['user_id'], reason)

            if success:
                messagebox.showinfo("Success", f"✅ {message}")
                self.db.log_activity(self.user_info['user_id'], f"Transferred account from {staff_data['username']} to {target_staff['username']}")
                self.load_staff_list()
                dialog.destroy()
            else:
                messagebox.showerror("Error", f"❌ Transfer failed:\n{message}")

        # Buttons based on active tab
        def save_current_tab():
            current_tab = notebook.index(notebook.select())
            if current_tab == 0:  # Basic Info
                save_basic_info()
            elif current_tab == 1:  # Password
                change_password()
            elif current_tab == 2:  # Transfer
                transfer_account()

        save_btn = tk.Button(button_frame, text="💾 SAVE CHANGES", command=save_current_tab,
                            bg='#27ae60', fg='white', font=('Arial', 14, 'bold'),
                            width=18, height=2, relief='raised', bd=3)
        save_btn.pack(side=tk.LEFT, padx=(0, 10))

        cancel_btn = tk.Button(button_frame, text="✗ CANCEL", command=dialog.destroy,
                              bg='#e74c3c', fg='white', font=('Arial', 14, 'bold'),
                              width=18, height=2, relief='raised', bd=3)
        cancel_btn.pack(side=tk.RIGHT)

        # Bind Enter key
        dialog.bind('<Return>', lambda e: save_current_tab())

    def toggle_password_visibility(self, entry_widget):
        """Toggle password visibility for a specific entry."""
        if entry_widget.cget('show') == "•":
            entry_widget.config(show="")
        else:
            entry_widget.config(show="•")

    def setup_financial_dashboard(self, parent):
        """Setup financial dashboard with scrollable canvas and responsive layout."""
        main_container = tk.Frame(parent, bg='#ecf0f1')
        main_container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(main_container, bg='#ecf0f1', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)

        scrollable_frame = tk.Frame(canvas, bg='#ecf0f1')
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", on_canvas_configure)

        def on_mouse_wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mouse_wheel)

        control_frame = tk.Frame(scrollable_frame, bg='#ecf0f1', pady=10)
        control_frame.pack(fill=tk.X, padx=20)

        add_expense_btn = tk.Button(
            control_frame,
            text="➕ Add Expense",
            command=self.add_expense_dialog,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 11, 'bold'),
            width=15
        )
        add_expense_btn.pack(side=tk.LEFT, padx=5)

        date_range_frame = tk.Frame(control_frame, bg='#ecf0f1')
        date_range_frame.pack(side=tk.LEFT, padx=20)

        tk.Label(date_range_frame, text="From:", bg='#ecf0f1').pack(side=tk.LEFT, padx=(0, 5))
        self.start_date_picker = tk.Entry(date_range_frame, width=12, bd=2, relief='solid')
        self.start_date_picker.pack(side=tk.LEFT, padx=(0, 10))
        self.start_date_picker.insert(0, datetime.now().strftime("%Y-%m-%d"))

        tk.Label(date_range_frame, text="To:", bg='#ecf0f1').pack(side=tk.LEFT, padx=(0, 5))
        self.end_date_picker = tk.Entry(date_range_frame, width=12, bd=2, relief='solid')
        self.end_date_picker.pack(side=tk.LEFT, padx=(0, 10))
        self.end_date_picker.insert(0, datetime.now().strftime("%Y-%m-%d"))

        date_filter_btn = tk.Button(
            control_frame,
            text="📅 Apply Date Range",
            command=lambda: self.apply_date_range_filter(parent),
            bg='#9b59b6',
            fg='white',
            font=('Arial', 11)
        )
        date_filter_btn.pack(side=tk.LEFT, padx=5)

        refresh_btn = tk.Button(
            control_frame,
            text="⟳ Refresh Dashboard",
            command=lambda: self.refresh_financial_dashboard(parent),
            bg='#3498db',
            fg='white',
            font=('Arial', 11)
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)

        export_btn = tk.Button(
            control_frame,
            text="📁 Export Report",
            command=self.export_financial_report,
            bg='#f39c12',
            fg='white',
            font=('Arial', 11)
        )
        export_btn.pack(side=tk.LEFT, padx=5)

        daily_summary_btn = tk.Button(
            control_frame,
            text="📊 Daily Summary",
            command=self.show_daily_summary,
            bg='#1abc9c',
            fg='white',
            font=('Arial', 11)
        )
        daily_summary_btn.pack(side=tk.LEFT, padx=5)

        weekly_data = self.db.get_weekly_financial_data()

        summary_frame = tk.Frame(scrollable_frame, bg='#ecf0f1')
        summary_frame.pack(fill=tk.X, pady=(10, 20), padx=20)

        summary_container = tk.Frame(summary_frame, bg='#ecf0f1')
        summary_container.pack(fill=tk.X)

        for i in range(4):
            summary_container.grid_columnconfigure(i, weight=1)

        card_width = 320
        card_height = 120

        income_card = tk.Frame(summary_container, bg='#27ae60', width=card_width, height=card_height,
                               relief='solid', bd=2)
        income_card.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        income_card.grid_propagate(False)
        income_card.pack_propagate(False)

        tk.Label(income_card, text="WEEKLY INCOME", bg='#27ae60', fg='white',
                 font=('Arial', 14, 'bold')).pack(pady=(15, 5))

        if weekly_data['weekly_income'] == 0:
            income_display = "GH₵0.00"
        else:
            income_display = f"GH₵{weekly_data['weekly_income']:,.2f}"

        tk.Label(income_card, text=income_display, bg='#27ae60', fg='white',
                 font=('Arial', 18, 'bold')).pack()
        tk.Label(income_card, text=f"{weekly_data['start_date']} to {weekly_data['end_date']}",
                 bg='#27ae60', fg='white', font=('Arial', 10)).pack(pady=(5, 0))

        expense_card = tk.Frame(summary_container, bg='#e74c3c', width=card_width, height=card_height,
                                relief='solid', bd=2)
        expense_card.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')
        expense_card.grid_propagate(False)
        expense_card.pack_propagate(False)

        tk.Label(expense_card, text="WEEKLY EXPENSES", bg='#e74c3c', fg='white',
                 font=('Arial', 14, 'bold')).pack(pady=(15, 5))
        tk.Label(expense_card, text=f"GH₵{weekly_data['weekly_expenses']:,.2f}", bg='#e74c3c', fg='white',
                 font=('Arial', 18, 'bold')).pack()
        tk.Label(expense_card, text=f"{weekly_data['start_date']} to {weekly_data['end_date']}",
                 bg='#e74c3c', fg='white', font=('Arial', 10)).pack(pady=(5, 0))

        refund_card = tk.Frame(summary_container, bg='#ff6b6b', width=card_width, height=card_height,
                               relief='solid', bd=2)
        refund_card.grid(row=0, column=2, padx=5, pady=5, sticky='nsew')
        refund_card.grid_propagate(False)
        refund_card.pack_propagate(False)

        tk.Label(refund_card, text="WEEKLY REFUNDS", bg='#ff6b6b', fg='white',
                 font=('Arial', 14, 'bold')).pack(pady=(15, 5))
        tk.Label(refund_card, text=f"GH₵{weekly_data['weekly_refunds']:,.2f}", bg='#ff6b6b', fg='white',
                 font=('Arial', 18, 'bold')).pack()
        tk.Label(refund_card, text=f"{weekly_data['start_date']} to {weekly_data['end_date']}",
                 bg='#ff6b6b', fg='white', font=('Arial', 10)).pack(pady=(5, 0))

        balance_card = tk.Frame(summary_container, bg='#2980b9', width=card_width, height=card_height,
                                relief='solid', bd=2)
        balance_card.grid(row=0, column=3, padx=5, pady=5, sticky='nsew')
        balance_card.grid_propagate(False)
        balance_card.pack_propagate(False)

        tk.Label(balance_card, text="AVAILABLE BALANCE", bg='#2980b9', fg='white',
                 font=('Arial', 14, 'bold')).pack(pady=(15, 5))

        available_balance_display = f"GH₵{weekly_data['available_balance']:,.2f}"
        tk.Label(balance_card, text=available_balance_display, bg='#2980b9', fg='#f1c40f',
                 font=('Arial', 18, 'bold')).pack()
        tk.Label(balance_card, text="For expense validation", bg='#2980b9', fg='white',
                 font=('Arial', 10)).pack(pady=(5, 0))

        middle_frame = tk.Frame(scrollable_frame, bg='#ecf0f1')
        middle_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        middle_frame.grid_rowconfigure(0, weight=1)
        middle_frame.grid_columnconfigure(0, weight=1)
        middle_frame.grid_columnconfigure(1, weight=1)
        middle_frame.grid_columnconfigure(2, weight=1)

        items_frame = tk.Frame(middle_frame, bg='white', relief='solid', bd=2)
        items_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10), pady=5)

        tk.Label(items_frame, text="Items Rented This Week", font=('Arial', 12, 'bold'),
                 bg='white', pady=10).pack()

        if weekly_data['weekly_items']:
            self.fig1, ax1 = plt.subplots(figsize=(5, 4), dpi=100)
            items = [row[0] for row in weekly_data['weekly_items']]
            quantities = [row[1] for row in weekly_data['weekly_items']]

            colors = plt.cm.Set3.colors[:len(items)]
            ax1.pie(quantities, labels=items, colors=colors, autopct='%1.1f%%', startangle=90)
            ax1.axis('equal')

            canvas1 = FigureCanvasTkAgg(self.fig1, items_frame)
            canvas1.draw()
            canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        else:
            tk.Label(items_frame, text="No rental data for this week",
                     bg='white', font=('Arial', 11)).pack(pady=50)

        finance_frame = tk.Frame(middle_frame, bg='white', relief='solid', bd=2)
        finance_frame.grid(row=0, column=1, sticky='nsew', padx=10, pady=5)

        tk.Label(finance_frame, text="Financial Overview", font=('Arial', 12, 'bold'),
                 bg='white', pady=10).pack()

        self.fig2, ax2 = plt.subplots(figsize=(5, 4), dpi=100)
        categories = ['Income', 'Expenses', 'Refunds']
        values = [weekly_data['weekly_income'], weekly_data['weekly_expenses'], weekly_data['weekly_refunds']]
        colors = ['#27ae60', '#e74c3c', '#ff6b6b']

        bars = ax2.bar(categories, values, color=colors, width=0.6)
        ax2.set_ylabel('Amount (GH₵)')
        ax2.set_title('Weekly Financial Overview')

        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width() / 2., height + max(values) * 0.01,
                     f'GH₵{value:,.2f}', ha='center', va='bottom', fontsize=9)

        canvas2 = FigureCanvasTkAgg(self.fig2, finance_frame)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        staff_stats_frame = tk.Frame(middle_frame, bg='white', relief='solid', bd=2)
        staff_stats_frame.grid(row=0, column=2, sticky='nsew', padx=(10, 0), pady=5)

        tk.Label(staff_stats_frame, text="Staff Performance Summary", font=('Arial', 12, 'bold'),
                 bg='white', pady=10).pack()

        staff_stats = self.get_staff_performance_summary()

        stats_text = tk.Text(staff_stats_frame, height=15, width=30, bg='white',
                             font=('Arial', 10), relief='solid', bd=1)
        stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        if staff_stats:
            stats_text.insert(tk.END, "Top Performing Staff:\n")
            stats_text.insert(tk.END, "=" * 30 + "\n")
            for staff in staff_stats[:5]:
                stats_text.insert(tk.END, f"\n{staff[0]}:\n")
                stats_text.insert(tk.END, f"  Rentals: {staff[1]}\n")
                stats_text.insert(tk.END, f"  Revenue: GH₵{staff[2]:,.2f}\n")
        else:
            stats_text.insert(tk.END, "No staff performance data available")

        stats_text.config(state=tk.DISABLED)

        full_report_btn = tk.Button(staff_stats_frame, text="📈 Full Staff Report",
                                    command=self.show_staff_performance,
                                    bg='#8e44ad', fg='white', font=('Arial', 10, 'bold'))
        full_report_btn.pack(pady=(0, 10))

        def cleanup_figures():
            if hasattr(self, 'fig1'):
                plt.close(self.fig1)
            if hasattr(self, 'fig2'):
                plt.close(self.fig2)

        self.cleanup_dashboard_figures = cleanup_figures

    def apply_date_range_filter(self, parent):
        """Apply date range filter to financial dashboard."""
        start_date = self.start_date_picker.get().strip()
        end_date = self.end_date_picker.get().strip()

        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")

            self.custom_start_date = start_date
            self.custom_end_date = end_date

            self.refresh_financial_dashboard(parent)

            messagebox.showinfo("Success", f"Date range applied: {start_date} to {end_date}")

        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD")

    def get_staff_performance_summary(self):
        """Get staff performance metrics."""
        try:
            result = self.db.execute_query('''
                SELECT 
                    u.username,
                    COUNT(r.id) as rental_count,
                    COALESCE(SUM(r.rental_charges), 0) as total_revenue
                FROM users u
                LEFT JOIN rentals r ON u.user_id = r.user_id
                WHERE u.user_type = 'staff' AND u.is_active = 1
                GROUP BY u.user_id, u.username
                ORDER BY total_revenue DESC
            ''')
            return result
        except Exception as e:
            print(f"Error getting staff performance: {e}")
            return []

    def show_staff_performance(self):
        """Show detailed staff performance report."""
        dialog = tk.Toplevel(self.master)
        dialog.title("Staff Performance Report")
        dialog.geometry("800x600")
        dialog.configure(bg='#2c3e50')
        dialog.grab_set()

        main_frame = tk.Frame(dialog, bg='#2c3e50', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="STAFF PERFORMANCE REPORT",
                 font=('Arial', 20, 'bold'), bg='#2c3e50', fg='white'
                 ).pack(pady=(0, 20))

        staff_data = self.get_staff_performance_summary()

        tree_frame = tk.Frame(main_frame, bg='#2c3e50', padx=10, pady=10)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("Staff", "Total Rentals", "Total Revenue", "Avg. per Rental")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for staff in staff_data:
            username, rentals, revenue = staff
            avg_revenue = revenue / rentals if rentals > 0 else 0
            tree.insert("", "end", values=(
                username,
                rentals,
                f"GH₵{revenue:,.2f}",
                f"GH₵{avg_revenue:,.2f}"
            ))

        def export_staff_report():
            self.export_staff_performance_report(staff_data)

        export_btn = tk.Button(main_frame, text="📁 Export to Excel",
                               command=export_staff_report,
                               bg='#27ae60', fg='white', font=('Arial', 12, 'bold'))
        export_btn.pack(pady=(10, 0))

    def show_daily_summary(self):
        """Show daily transaction summary."""
        dialog = tk.Toplevel(self.master)
        dialog.title("Daily Transaction Summary")
        dialog.geometry("1000x700")
        dialog.configure(bg='#2c3e50')
        dialog.grab_set()

        main_frame = tk.Frame(dialog, bg='#2c3e50', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="DAILY TRANSACTION SUMMARY",
                 font=('Arial', 20, 'bold'), bg='#2c3e50', fg='white'
                 ).pack(pady=(0, 20))

        date_frame = tk.Frame(main_frame, bg='#2c3e50', pady=10)
        date_frame.pack(fill=tk.X)

        tk.Label(date_frame, text="Select Date:", bg='#2c3e50', fg='white',
                 font=('Arial', 12)).pack(side=tk.LEFT, padx=(0, 10))

        date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        date_entry = tk.Entry(date_frame, textvariable=date_var, width=15, bd=2, relief='solid')
        date_entry.pack(side=tk.LEFT, padx=(0, 20))

        def load_daily_summary():
            selected_date = date_var.get()
            transactions = self.db.execute_query('''
                SELECT 
                    transaction_type,
                    category,
                    amount,
                    description,
                    timestamp,
                    u.username,
                    reference_number
                FROM financial_transactions ft
                JOIN users u ON ft.user_id = u.user_id
                WHERE date(ft.timestamp) = ?
                ORDER BY ft.timestamp DESC
            ''', (selected_date,))

            for item in tree.get_children():
                tree.delete(item)

            total_income = 0
            total_expenses = 0
            total_refunds = 0

            for trans in transactions:
                trans_type, category, amount, description, timestamp, username, reference = trans
                tree.insert("", "end", values=(
                    trans_type,
                    category or "N/A",
                    f"GH₵{amount:,.2f}",
                    description,
                    timestamp,
                    username,
                    reference or ""
                ))

                if trans_type == 'income':
                    total_income += amount
                elif trans_type == 'expense':
                    total_expenses += amount
                elif trans_type == 'refund':
                    total_refunds += amount

            total_income_label.config(text=f"GH₵{total_income:,.2f}")
            total_expenses_label.config(text=f"GH₵{total_expenses:,.2f}")
            total_refunds_label.config(text=f"GH₵{total_refunds:,.2f}")
            net_balance_label.config(text=f"GH₵{total_income - total_expenses - total_refunds:,.2f}")

        load_btn = tk.Button(date_frame, text="Load Summary", command=load_daily_summary,
                             bg='#3498db', fg='white', font=('Arial', 11))
        load_btn.pack(side=tk.LEFT, padx=(0, 10))

        export_btn = tk.Button(date_frame, text="Export Daily Report",
                               command=lambda: self.export_daily_report(date_var.get()),
                               bg='#f39c12', fg='white', font=('Arial', 11))
        export_btn.pack(side=tk.LEFT)

        summary_frame = tk.Frame(main_frame, bg='#2c3e50', pady=10)
        summary_frame.pack(fill=tk.X)

        income_frame = tk.Frame(summary_frame, bg='#27ae60', padx=20, pady=10, relief='solid', bd=2)
        income_frame.pack(side=tk.LEFT, padx=5)
        tk.Label(income_frame, text="Total Income", bg='#27ae60', fg='white',
                 font=('Arial', 12)).pack()
        total_income_label = tk.Label(income_frame, text="GH₵0.00", bg='#27ae60', fg='white',
                                      font=('Arial', 14, 'bold'))
        total_income_label.pack()

        expense_frame = tk.Frame(summary_frame, bg='#e74c3c', padx=20, pady=10, relief='solid', bd=2)
        expense_frame.pack(side=tk.LEFT, padx=5)
        tk.Label(expense_frame, text="Total Expenses", bg='#e74c3c', fg='white',
                 font=('Arial', 12)).pack()
        total_expenses_label = tk.Label(expense_frame, text="GH₵0.00", bg='#e74c3c', fg='white',
                                        font=('Arial', 14, 'bold'))
        total_expenses_label.pack()

        refund_frame = tk.Frame(summary_frame, bg='#ff6b6b', padx=20, pady=10, relief='solid', bd=2)
        refund_frame.pack(side=tk.LEFT, padx=5)
        tk.Label(refund_frame, text="Total Refunds", bg='#ff6b6b', fg='white',
                 font=('Arial', 12)).pack()
        total_refunds_label = tk.Label(refund_frame, text="GH₵0.00", bg='#ff6b6b', fg='white',
                                       font=('Arial', 14, 'bold'))
        total_refunds_label.pack()

        net_frame = tk.Frame(summary_frame, bg='#2980b9', padx=20, pady=10, relief='solid', bd=2)
        net_frame.pack(side=tk.LEFT, padx=5)
        tk.Label(net_frame, text="Net Balance", bg='#2980b9', fg='white',
                 font=('Arial', 12)).pack()
        net_balance_label = tk.Label(net_frame, text="GH₵0.00", bg='#2980b9', fg='white',
                                     font=('Arial', 14, 'bold'))
        net_balance_label.pack()

        tree_frame = tk.Frame(main_frame, bg='#2c3e50', padx=10, pady=10)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("Type", "Category", "Amount", "Description", "Time", "User", "Reference")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)

        col_widths = [80, 100, 100, 200, 120, 100, 100]
        for i, col in enumerate(columns):
            tree.heading(col, text=col)
            tree.column(col, width=col_widths[i], anchor="center")

        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        load_daily_summary()

    def export_financial_report(self):
        """Export financial report to Excel with better formatting."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"financial_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

        if not file_path:
            return

        try:
            if hasattr(self, 'custom_start_date') and hasattr(self, 'custom_end_date'):
                start_date = self.custom_start_date
                end_date = self.custom_end_date
            else:
                weekly_data = self.db.get_weekly_financial_data()
                start_date = weekly_data['start_date']
                end_date = weekly_data['end_date']

            wb = Workbook()
            ws = wb.active
            ws.title = "Financial Report"

            header_font = Font(bold=True, color="FFFFFF", size=12)
            header_fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
            total_fill = PatternFill(start_color="27ae60", end_color="27ae60", fill_type="solid")
            expense_fill = PatternFill(start_color="e74c3c", end_color="e74c3c", fill_type="solid")
            refund_fill = PatternFill(start_color="ff6b6b", end_color="ff6b6b", fill_type="solid")
            center_align = Alignment(horizontal="center", vertical="center")
            border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )

            ws.merge_cells('A1:G1')
            title_cell = ws['A1']
            title_cell.value = f"Financial Report - {start_date} to {end_date}"
            title_cell.font = Font(bold=True, size=16, color="2C3E50")
            title_cell.alignment = Alignment(horizontal="center")

            ws['A3'] = "SUMMARY"
            ws['A3'].font = Font(bold=True, size=14)

            summary_data = [
                ["Total Income", f"GH₵{weekly_data['weekly_income']:,.2f}"],
                ["Total Expenses", f"GH₵{weekly_data['weekly_expenses']:,.2f}"],
                ["Total Refunds", f"GH₵{weekly_data['weekly_refunds']:,.2f}"],
                ["Net Balance",
                 f"GH₵{weekly_data['weekly_income'] - weekly_data['weekly_expenses'] - weekly_data['weekly_refunds']:,.2f}"],
                ["Available Balance", f"GH₵{weekly_data['available_balance']:,.2f}"]
            ]

            for i, (label, value) in enumerate(summary_data, start=4):
                ws[f'A{i}'] = label
                ws[f'B{i}'] = value
                ws[f'A{i}'].font = Font(bold=True)
                ws[f'B{i}'].font = Font(bold=True)
                if "Income" in label or "Balance" in label:
                    ws[f'B{i}'].fill = total_fill
                    ws[f'B{i}'].font = Font(bold=True, color="FFFFFF")
                elif "Expenses" in label:
                    ws[f'B{i}'].fill = expense_fill
                    ws[f'B{i}'].font = Font(bold=True, color="FFFFFF")
                elif "Refunds" in label:
                    ws[f'B{i}'].fill = refund_fill
                    ws[f'B{i}'].font = Font(bold=True, color="FFFFFF")

            ws['A10'] = "TRANSACTIONS"
            ws['A10'].font = Font(bold=True, size=14)

            result = self.db.execute_query('''
                SELECT ft.timestamp, ft.transaction_type, ft.category, ft.amount, 
                       ft.description, u.username, ft.reference_number
                FROM financial_transactions ft
                JOIN users u ON ft.user_id = u.user_id
                WHERE date(ft.timestamp) BETWEEN ? AND ?
                ORDER BY ft.timestamp
            ''', (start_date, end_date))

            columns = ["Date", "Type", "Category", "Amount", "Description", "User", "Reference"]
            data = []
            for row in result:
                data.append([row[0], row[1], row[2] or "N/A", row[3], row[4], row[5], row[6] or ""])

            df = pd.DataFrame(data, columns=columns)

            for col_num, column_title in enumerate(columns, 1):
                cell = ws.cell(row=12, column=col_num)
                cell.value = column_title
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_align
                cell.border = border

            for row_num, row_data in enumerate(df.values, 13):
                for col_num, cell_value in enumerate(row_data, 1):
                    cell = ws.cell(row=row_num, column=col_num)
                    cell.value = cell_value
                    cell.border = border
                    if col_num == 4:
                        cell.number_format = '"GH₵"#,##0.00'
                        if row_data[1] == 'income':
                            cell.font = Font(color="27ae60", bold=True)
                        elif row_data[1] == 'expense':
                            cell.font = Font(color="e74c3c", bold=True)
                        elif row_data[1] == 'refund':
                            cell.font = Font(color="ff6b6b", bold=True)

            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width

            ws[f'A{len(df) + 15}'] = "ITEMS RENTED THIS WEEK"
            ws[f'A{len(df) + 15}'].font = Font(bold=True, size=14)

            if weekly_data['weekly_items']:
                for i, (item, quantity) in enumerate(weekly_data['weekly_items'], len(df) + 17):
                    ws[f'A{i}'] = item
                    ws[f'B{i}'] = quantity
                    ws[f'B{i}'].alignment = center_align

            wb.save(file_path)

            messagebox.showinfo("Success", f"✅ Report exported to:\n{file_path}")
            self.db.log_activity(self.user_info['user_id'], "Exported financial report to Excel")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export report: {e}")
            print(f"Export error: {traceback.format_exc()}")

    def export_staff_performance_report(self, staff_data):
        """Export staff performance report to Excel."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile=f"staff_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

        if not file_path:
            return

        try:
            df = pd.DataFrame(staff_data, columns=["Staff", "Total Rentals", "Total Revenue"])
            df['Average per Rental'] = df.apply(lambda row: row['Total Revenue'] / row['Total Rentals']
            if row['Total Rentals'] > 0 else 0, axis=1)

            df['Total Revenue'] = df['Total Revenue'].apply(lambda x: f"GH₵{x:,.2f}")
            df['Average per Rental'] = df['Average per Rental'].apply(lambda x: f"GH₵{x:,.2f}")

            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Staff Performance', index=False)

                workbook = writer.book
                worksheet = writer.sheets['Staff Performance']

                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 30)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

            messagebox.showinfo("Success", f"✅ Staff report exported to:\n{file_path}")
            self.db.log_activity(self.user_info['user_id'], "Exported staff performance report")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export staff report: {e}")

    def export_daily_report(self, date):
        """Export daily report to Excel."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile=f"daily_report_{date.replace('-', '')}.xlsx"
        )

        if not file_path:
            return

        try:
            transactions = self.db.execute_query('''
                SELECT 
                    transaction_type,
                    category,
                    amount,
                    description,
                    timestamp,
                    u.username,
                    reference_number
                FROM financial_transactions ft
                JOIN users u ON ft.user_id = u.user_id
                WHERE date(ft.timestamp) = ?
                ORDER BY ft.timestamp DESC
            ''', (date,))

            df = pd.DataFrame(transactions,
                              columns=["Type", "Category", "Amount", "Description", "Time", "User", "Reference"])

            total_income = df[df['Type'] == 'income']['Amount'].sum()
            total_expenses = df[df['Type'] == 'expense']['Amount'].sum()
            total_refunds = df[df['Type'] == 'refund']['Amount'].sum()
            net_balance = total_income - total_expenses - total_refunds

            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                summary_data = pd.DataFrame({
                    'Metric': ['Total Income', 'Total Expenses', 'Total Refunds', 'Net Balance'],
                    'Amount': [total_income, total_expenses, total_refunds, net_balance]
                })
                summary_data.to_excel(writer, sheet_name='Summary', index=False)

                df.to_excel(writer, sheet_name='Transactions', index=False)

            messagebox.showinfo("Success", f"✅ Daily report exported to:\n{file_path}")
            self.db.log_activity(self.user_info['user_id'], f"Exported daily report for {date}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export daily report: {e}")

    def setup_system_logs(self, parent):
        """Setup system logs interface with search/filter."""
        filter_frame = tk.Frame(parent, bg='#ecf0f1', pady=10)
        filter_frame.pack(fill=tk.X, padx=10)

        tk.Label(filter_frame, text="Search:", bg='#ecf0f1').pack(side=tk.LEFT, padx=(0, 5))
        self.log_search_var = tk.StringVar()
        search_entry = tk.Entry(filter_frame, textvariable=self.log_search_var, width=25, bd=2, relief='solid')
        search_entry.pack(side=tk.LEFT, padx=(0, 10))
        search_entry.bind('<KeyRelease>', lambda e: self.filter_logs())

        tk.Label(filter_frame, text="Filter by User", bg='#ecf0f1').pack(side=tk.LEFT, padx=(0, 5))

        self.log_user_filter = ttk.Combobox(filter_frame, width=20)
        self.log_user_filter.pack(side=tk.LEFT, padx=(0, 10))
        self.log_user_filter.bind('<<ComboboxSelected>>', lambda e: self.filter_logs())

        tk.Label(filter_frame, text="Date Range", bg='#ecf0f1').pack(side=tk.LEFT, padx=(0, 5))

        self.log_start_date = tk.Entry(filter_frame, width=12, bd=2, relief='solid')
        self.log_start_date.pack(side=tk.LEFT, padx=(0, 5))
        self.log_start_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.log_start_date.bind('<KeyRelease>', lambda e: self.filter_logs())

        tk.Label(filter_frame, text="to", bg='#ecf0f1').pack(side=tk.LEFT, padx=5)

        self.log_end_date = tk.Entry(filter_frame, width=12, bd=2, relief='solid')
        self.log_end_date.pack(side=tk.LEFT, padx=(0, 10))
        self.log_end_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.log_end_date.bind('<KeyRelease>', lambda e: self.filter_logs())

        filter_btn = tk.Button(
            filter_frame,
            text="🔍 Filter",
            command=self.filter_logs,
            bg='#3498db',
            fg='white',
            font=('Arial', 10)
        )
        filter_btn.pack(side=tk.LEFT, padx=5)

        clear_btn = tk.Button(
            filter_frame,
            text="🗑️ Clear All Logs",
            command=self.clear_all_logs,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 10)
        )
        clear_btn.pack(side=tk.LEFT)

        export_btn = tk.Button(
            filter_frame,
            text="📁 Export Logs",
            command=self.export_logs,
            bg='#f39c12',
            fg='white',
            font=('Arial', 10)
        )
        export_btn.pack(side=tk.LEFT, padx=(10, 0))

        logs_frame = tk.Frame(parent, bg='#ecf0f1')
        logs_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        columns = ("ID", "Timestamp", "User", "Activity")
        self.logs_tree = ttk.Treeview(logs_frame, columns=columns, show="headings", height=20)

        col_widths = [50, 150, 100, 400]
        for i, col in enumerate(columns):
            self.logs_tree.heading(col, text=col)
            self.logs_tree.column(col, width=col_widths[i], anchor="w")

        scrollbar = ttk.Scrollbar(logs_frame, orient="vertical", command=self.logs_tree.yview)
        self.logs_tree.configure(yscrollcommand=scrollbar.set)

        self.logs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.load_user_filter_list()
        self.filter_logs()

    def filter_logs(self, event=None):
        """Filter logs based on search criteria."""
        for item in self.logs_tree.get_children():
            self.logs_tree.delete(item)

        try:
            search_text = self.log_search_var.get().strip().lower()
            user_filter = self.log_user_filter.get()
            start_date = self.log_start_date.get().strip()
            end_date = self.log_end_date.get().strip()

            query = '''
                SELECT a.id, a.timestamp, u.username, a.activity_description
                FROM activities a
                JOIN users u ON a.user_id = u.user_id
                WHERE 1=1
            '''
            params = []

            if user_filter and user_filter != 'All Users':
                query += " AND u.username = ?"
                params.append(user_filter)

            if start_date:
                query += " AND date(a.timestamp) >= ?"
                params.append(start_date)

            if end_date:
                query += " AND date(a.timestamp) <= ?"
                params.append(end_date)

            query += " ORDER BY a.timestamp DESC"

            result = self.db.execute_query(query, tuple(params))

            for row in result:
                log_text = f"{row[1]} {row[2]} {row[3]}".lower()
                if search_text in log_text:
                    self.logs_tree.insert("", "end", values=row)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to filter logs: {e}")

    def export_logs(self):
        """Export system logs to Excel."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile=f"system_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

        if not file_path:
            return

        try:
            result = self.db.execute_query('''
                SELECT a.id, a.timestamp, u.username, a.activity_description
                FROM activities a
                JOIN users u ON a.user_id = u.user_id
                ORDER BY a.timestamp DESC
                LIMIT 500
            ''')

            df = pd.DataFrame(result, columns=["ID", "Timestamp", "User", "Activity"])

            df.to_excel(file_path, index=False)

            messagebox.showinfo("Success", f"✅ Logs exported to:\n{file_path}")
            self.db.log_activity(self.user_info['user_id'], "Exported system logs")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export logs: {e}")

    def refresh_financial_dashboard(self, parent):
        """Refresh the financial dashboard with cleanup."""
        if hasattr(self, 'cleanup_dashboard_figures'):
            self.cleanup_dashboard_figures()

        for widget in parent.winfo_children():
            widget.destroy()

        self.setup_financial_dashboard(parent)

    def add_expense_dialog(self):
        """Open dialog to add an expense with STRICT balance validation."""
        dialog = tk.Toplevel(self.master)
        dialog.title("Add Expense")
        dialog.geometry("700x450")
        dialog.configure(bg='#2c3e50')
        dialog.grab_set()
        dialog.resizable(False, False)

        main_frame = tk.Frame(dialog, bg='#2c3e50', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="ADD EXPENSE",
                 font=('Arial', 18, 'bold'), bg='#2c3e50', fg='white'
                 ).pack(pady=(0, 20))

        weekly_data = self.db.get_weekly_financial_data()
        available_balance = weekly_data['available_balance']

        balance_frame = tk.Frame(main_frame, bg='#2980b9', padx=15, pady=10, relief='solid', bd=2)
        balance_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(balance_frame, text="CURRENT AVAILABLE BALANCE:",
                 font=('Arial', 12, 'bold'), bg='#2980b9', fg='white'
                 ).pack(side=tk.LEFT)
        tk.Label(balance_frame, text=f"GH₵{available_balance:,.2f}",
                 font=('Arial', 14, 'bold'), bg='#2980b9', fg='#f1c40f'
                 ).pack(side=tk.LEFT, padx=(10, 0))

        form_frame = tk.Frame(main_frame, bg='white', relief='solid', bd=2, padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)

        row = 0
        tk.Label(form_frame, text="Amount (GH₵) Required", bg='white',
                 font=('Arial', 11)).grid(row=row, column=0, sticky='w', pady=10)
        amount_var = tk.StringVar()
        amount_entry = tk.Entry(form_frame, textvariable=amount_var, width=25, font=('Arial', 11), bd=2, relief='solid')
        amount_entry.grid(row=row, column=1, pady=10, padx=(10, 0))
        amount_entry.focus_set()
        row += 1

        tk.Label(form_frame, text="Category Required", bg='white',
                 font=('Arial', 11)).grid(row=row, column=0, sticky='w', pady=10)
        categories = self.db.get_expense_categories()
        category_var = tk.StringVar()
        category_combo = ttk.Combobox(form_frame, textvariable=category_var,
                                      values=categories, width=23, font=('Arial', 11))
        category_combo.grid(row=row, column=1, pady=10, padx=(10, 0))
        if categories:
            category_combo.current(0)
        row += 1

        tk.Label(form_frame, text="Description Required", bg='white',
                 font=('Arial', 11)).grid(row=row, column=0, sticky='w', pady=10)
        desc_var = tk.StringVar()
        desc_entry = tk.Entry(form_frame, textvariable=desc_var, width=25, font=('Arial', 11), bd=2, relief='solid')
        desc_entry.grid(row=row, column=1, pady=10, padx=(10, 0))
        row += 1

        form_frame.grid_columnconfigure(1, weight=1)

        info_label = tk.Label(form_frame,
                              text=f"Note: Expense cannot exceed available balance (GH₵{available_balance:,.2f})",
                              bg='white', fg='#e74c3c', font=('Arial', 9, 'italic'))
        info_label.grid(row=row, column=0, columnspan=2, pady=(20, 0), sticky='w')
        row += 1

        button_frame = tk.Frame(main_frame, bg='#2c3e50', pady=10)
        button_frame.pack(fill=tk.X)

        def validate_and_save():
            amount_str = amount_var.get().strip()
            category = category_var.get().strip()
            description = desc_var.get().strip()

            if not all([amount_str, category, description]):
                messagebox.showerror("Error", "All fields are required.")
                return

            try:
                amount = float(amount_str)
                if amount <= 0:
                    messagebox.showerror("Error", "Amount must be greater than 0.")
                    return
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid amount.")
                return

            if amount > available_balance:
                messagebox.showerror("❌ EXPENSE REJECTED",
                                     f"Expense amount (GH₵{amount:,.2f}) exceeds available balance (GH₵{available_balance:,.2f})\n\n"
                                     f"Shortfall: GH₵{amount - available_balance:,.2f}\n\n"
                                     f"You cannot add this expense.")
                return

            if not messagebox.askyesno("Confirm Expense",
                                       f"Add expense of GH₵{amount:,.2f}?\n\n"
                                       f"Category: {category}\n"
                                       f"Description: {description}\n\n"
                                       f"Balance after expense: GH₵{available_balance - amount:,.2f}"):
                return

            success, message = self.db.record_expense(amount, description, category, self.user_info['user_id'])

            if success:
                messagebox.showinfo("Success", "✅ Expense added successfully!")
                self.db.log_activity(self.user_info['user_id'],
                                     f"Added expense: {description} - GH₵{amount:.2f}")
                dialog.destroy()

                self.refresh_financial_dashboard(self.notebook.winfo_children()[1])
            else:
                messagebox.showerror("Error", f"Failed to add expense: {message}")

        save_btn = tk.Button(
            button_frame,
            text="💾 SAVE EXPENSE",
            command=validate_and_save,
            bg='#27ae60',
            fg='white',
            font=('Arial', 12, 'bold'),
            width=15,
            height=2,
            relief='raised',
            bd=2
        )
        save_btn.pack(side=tk.LEFT, padx=(0, 10))

        cancel_btn = tk.Button(
            button_frame,
            text="✗ CANCEL",
            command=dialog.destroy,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 12, 'bold'),
            width=15,
            height=2,
            relief='raised',
            bd=2
        )
        cancel_btn.pack(side=tk.RIGHT)

        dialog.bind('<Return>', lambda e: validate_and_save())

    def add_expense_category_dialog(self, parent_dialog):
        """Open dialog to add a new expense category with improved UI."""
        dialog = tk.Toplevel(parent_dialog)
        dialog.title("Add Expense Category")
        dialog.geometry("450x400")
        dialog.configure(bg='#34495e')
        dialog.grab_set()
        dialog.resizable(False, False)

        main_container = tk.Frame(dialog, bg='#34495e')
        main_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)

        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_rowconfigure(1, weight=0)
        main_container.grid_columnconfigure(0, weight=1)

        form_area = tk.Frame(main_container, bg='#34495e')
        form_area.grid(row=0, column=0, sticky='nsew', pady=(0, 20))

        tk.Label(form_area, text="ADD NEW CATEGORY",
                 font=('Arial', 16, 'bold'), bg='#34495e', fg='white'
                 ).pack(pady=(0, 20))

        cat_frame = tk.Frame(form_area, bg='#34495e')
        cat_frame.pack(fill=tk.X, pady=10)

        tk.Label(cat_frame, text="Category Name Required",
                 bg='#34495e', fg='white',
                 font=('Arial', 11, 'bold'), width=20, anchor='w').pack(side=tk.LEFT, padx=(0, 10))

        cat_name_var = tk.StringVar()
        cat_name_entry = tk.Entry(cat_frame, textvariable=cat_name_var,
                                  width=25, font=('Arial', 11),
                                  bd=2, relief='solid', bg='white', fg='black')
        cat_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        cat_name_entry.focus_set()

        desc_frame = tk.Frame(form_area, bg='#34495e')
        desc_frame.pack(fill=tk.X, pady=10)

        tk.Label(desc_frame, text="Description (Optional)",
                 bg='#34495e', fg='white',
                 font=('Arial', 11), width=20, anchor='w').pack(side=tk.LEFT, padx=(0, 10))

        desc_var = tk.StringVar()
        desc_entry = tk.Entry(desc_frame, textvariable=desc_var,
                              width=25, font=('Arial', 11),
                              bd=2, relief='solid', bg='white', fg='black')
        desc_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        info_label = tk.Label(form_area,
                              text="Note: Category names must be unique and descriptive.",
                              bg='#34495e', fg='#bdc3c7', font=('Arial', 9, 'italic'))
        info_label.pack(pady=(20, 0))

        button_area = tk.Frame(main_container, bg='#34495e', height=80)
        button_area.grid(row=1, column=0, sticky='ew', pady=(20, 0))
        button_area.grid_propagate(False)

        button_center = tk.Frame(button_area, bg='#34495e')
        button_center.place(relx=0.5, rely=0.5, anchor='center')

        def save_category():
            category_name = cat_name_var.get().strip()
            description = desc_var.get().strip()

            if not category_name:
                messagebox.showerror("Error", "Category name is required.")
                cat_name_entry.focus_set()
                return

            if len(category_name) < 2:
                messagebox.showerror("Error", "Category name must be at least 2 characters.")
                return

            success, message = self.db.add_expense_category(category_name, description)

            if success:
                messagebox.showinfo("Success", f"✅ {message}")
                self.db.log_activity(self.user_info['user_id'],
                                     f"Added expense category: {category_name}")

                if hasattr(parent_dialog, 'refresh_categories'):
                    parent_dialog.refresh_categories()

                dialog.destroy()

            else:
                messagebox.showerror("Error", f"❌ {message}")
                cat_name_entry.focus_set()

        save_btn = tk.Button(button_center, text="💾 SAVE CATEGORY", command=save_category,
                             bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
                             width=18, height=2, relief='raised', bd=2)
        save_btn.pack(side=tk.LEFT, padx=(0, 15))

        cancel_btn = tk.Button(button_center, text="✗ CANCEL", command=dialog.destroy,
                               bg='#e74c3c', fg='white', font=('Arial', 11, 'bold'),
                               width=15, height=2, relief='raised', bd=2)
        cancel_btn.pack(side=tk.LEFT)

        dialog.bind('<Return>', lambda e: save_category())

    def setup_settings(self, parent):
        """Setup settings interface."""
        settings_frame = tk.Frame(parent, bg='#ecf0f1', padx=20, pady=20)
        settings_frame.pack(fill=tk.BOTH, expand=True)

        # Password change frame
        pass_frame = tk.LabelFrame(settings_frame, text="Change Admin Password", bg='#ecf0f1', padx=10, pady=10,
                                   relief='solid', bd=2)
        pass_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(pass_frame, text="Current Password", bg='#ecf0f1').grid(row=0, column=0, sticky='w', pady=5)
        self.current_pass = tk.Entry(pass_frame, show="•", width=25, font=('Arial', 11), bd=2, relief='solid')
        self.current_pass.grid(row=0, column=1, pady=5, padx=(10, 0), sticky='w')

        # Eye icon for current password - NO BOX
        current_eye_label = tk.Label(pass_frame, text="👁️", cursor="hand2",
                                     bg='white', fg='#7f8c8d', font=('Arial', 14))
        current_eye_label.grid(row=0, column=2, padx=(5, 0))
        current_eye_label.bind("<Button-1>", lambda e: self.toggle_password_visibility(self.current_pass))

        tk.Label(pass_frame, text="New Password", bg='#ecf0f1').grid(row=1, column=0, sticky='w', pady=5)
        self.new_pass = tk.Entry(pass_frame, show="•", width=25, font=('Arial', 11), bd=2, relief='solid')
        self.new_pass.grid(row=1, column=1, pady=5, padx=(10, 0), sticky='w')

        # Eye icon for new password - NO BOX
        new_eye_label = tk.Label(pass_frame, text="👁️", cursor="hand2",
                                 bg='white', fg='#7f8c8d', font=('Arial', 14))
        new_eye_label.grid(row=1, column=2, padx=(5, 0))
        new_eye_label.bind("<Button-1>", lambda e: self.toggle_password_visibility(self.new_pass))

        tk.Label(pass_frame, text="Confirm Password", bg='#ecf0f1').grid(row=2, column=0, sticky='w', pady=5)
        self.confirm_pass = tk.Entry(pass_frame, show="•", width=25, font=('Arial', 11), bd=2, relief='solid')
        self.confirm_pass.grid(row=2, column=1, pady=5, padx=(10, 0), sticky='w')

        # Eye icon for confirm password - NO BOX
        confirm_eye_label = tk.Label(pass_frame, text="👁️", cursor="hand2",
                                     bg='white', fg='#7f8c8d', font=('Arial', 14))
        confirm_eye_label.grid(row=2, column=2, padx=(5, 0))
        confirm_eye_label.bind("<Button-1>", lambda e: self.toggle_password_visibility(self.confirm_pass))

        change_btn = tk.Button(
            pass_frame,
            text="Change Password",
            command=self.change_admin_password,
            bg='#27ae60',
            fg='white',
            font=('Arial', 11)
        )
        change_btn.grid(row=3, column=0, columnspan=3, pady=10, sticky='ew')

        # Timeout settings
        timeout_frame = tk.LabelFrame(settings_frame, text="Session Timeout Settings", bg='#ecf0f1', padx=10, pady=10,
                                      relief='solid', bd=2)
        timeout_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(timeout_frame, text="Auto Logout (minutes)", bg='#ecf0f1').grid(row=0, column=0, sticky='w', pady=5)
        self.timeout_minutes = tk.StringVar(value="30")
        timeout_entry = tk.Entry(timeout_frame, textvariable=self.timeout_minutes, width=10, font=('Arial', 11), bd=2,
                                 relief='solid')
        timeout_entry.grid(row=0, column=1, pady=5, padx=(10, 0), sticky='w')

        def set_timeout_for_all():
            try:
                minutes = int(self.timeout_minutes.get())
                if minutes < 1 or minutes > 480:
                    messagebox.showerror("Error", "Please enter a value between 1 and 480 minutes.")
                    return

                staff_users = self.db.execute_query("SELECT user_id FROM users WHERE user_type = 'staff'")
                for user in staff_users:
                    self.db.set_session_timeout(user[0], minutes)

                self.db.set_session_timeout(self.user_info['user_id'], minutes)

                messagebox.showinfo("Success", f"Session timeout set to {minutes} minutes for all users.")
                self.db.log_activity(self.user_info['user_id'],
                                     f"Set session timeout to {minutes} minutes for all users")

            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number.")

        timeout_btn = tk.Button(
            timeout_frame,
            text="Set for All Users",
            command=set_timeout_for_all,
            bg='#3498db',
            fg='white',
            font=('Arial', 10)
        )
        timeout_btn.grid(row=0, column=2, pady=5, padx=(10, 0), sticky='w')

        # Database operations
        db_frame = tk.LabelFrame(settings_frame, text="Database Operations", bg='#ecf0f1', padx=10, pady=10,
                                 relief='solid', bd=2)
        db_frame.pack(fill=tk.X, pady=(0, 20))

        backup_btn = tk.Button(
            db_frame,
            text="Backup Database",
            command=self.backup_database,
            bg='#3498db',
            fg='white',
            font=('Arial', 11),
            width=20
        )
        backup_btn.pack(pady=5)

        restore_btn = tk.Button(
            db_frame,
            text="Restore Database",
            command=self.restore_database,
            bg='#f39c12',
            fg='white',
            font=('Arial', 11),
            width=20
        )
        restore_btn.pack(pady=5)

        # System information
        info_frame = tk.LabelFrame(settings_frame, text="System Information", bg='#ecf0f1', padx=10, pady=10,
                                   relief='solid', bd=2)
        info_frame.pack(fill=tk.X)

        tk.Label(info_frame, text=f"Database: {DATABASE_FILENAME}", bg='#ecf0f1').pack(anchor='w', pady=2)
        tk.Label(info_frame, text=f"Receipts Folder: {RECEIPTS_FOLDER}", bg='#ecf0f1').pack(anchor='w', pady=2)

        staff_count = len(
            self.db.execute_query("SELECT user_id FROM users WHERE user_type = 'staff' AND is_active = 1"))
        rentals_count = len(self.db.execute_query("SELECT id FROM rentals WHERE status = 'Rented'"))

        tk.Label(info_frame, text=f"Active Staff: {staff_count}", bg='#ecf0f1').pack(anchor='w', pady=2)
        tk.Label(info_frame, text=f"Active Rentals: {rentals_count}", bg='#ecf0f1').pack(anchor='w', pady=2)

    def create_staff_account(self):
        """Open dialog to create new staff account with improved layout and eye buttons WITHOUT BOXES."""
        dialog = tk.Toplevel(self.master)
        dialog.title("Create Staff Account")
        dialog.geometry("550x650")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.configure(bg='#2c3e50')

        main_frame = tk.Frame(dialog, bg='#2c3e50', padx=30, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)

        header_frame = tk.Frame(main_frame, bg='#2c3e50', relief='solid', bd=2)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(
            header_frame,
            text="CREATE STAFF ACCOUNT",
            font=('Arial', 18, 'bold'),
            bg='#2c3e50',
            fg='white',
            pady=15
        ).pack()

        form_container = tk.Frame(main_frame, bg='#ecf0f1', relief='solid', bd=2)
        form_container.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        fields_frame = tk.Frame(form_container, bg='#ecf0f1', padx=30, pady=30)
        fields_frame.pack(fill=tk.BOTH, expand=True)

        # Configure grid weights
        for i in range(2):
            fields_frame.grid_columnconfigure(i, weight=1)

        row = 0
        # Username
        tk.Label(fields_frame, text="Username ", bg='#ecf0f1', font=('Arial', 11, 'bold'),
                 fg='#2c3e50').grid(row=row, column=0, sticky='w', pady=(0, 5))
        username_var = tk.StringVar()
        username_entry = tk.Entry(fields_frame, textvariable=username_var, width=30, font=('Arial', 11),
                                  bd=2, relief='solid', bg='white')
        username_entry.grid(row=row, column=1, pady=(0, 15), padx=(10, 0), sticky='ew')
        username_entry.focus_set()
        row += 1

        # Password with eye icon
        tk.Label(fields_frame, text="Password ", bg='#ecf0f1', font=('Arial', 11, 'bold'),
                 fg='#2c3e50').grid(row=row, column=0, sticky='w', pady=(0, 5))
        password_frame = tk.Frame(fields_frame, bg='#ecf0f1')
        password_frame.grid(row=row, column=1, pady=(0, 15), padx=(10, 0), sticky='ew')
        password_var = tk.StringVar()
        password_entry = tk.Entry(password_frame, textvariable=password_var, show="•", width=25, font=('Arial', 11),
                                  bd=2, relief='solid', bg='white')
        password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        password_eye_label = tk.Label(password_frame, text="👁️", cursor="hand2",
                                      bg='white', fg='#7f8c8d', font=('Arial', 14))
        password_eye_label.pack(side=tk.RIGHT, padx=(5, 0))
        password_eye_label.bind("<Button-1>", lambda e: self.toggle_password_visibility(password_entry))
        row += 1

        # Confirm Password with eye icon - WITHOUT BOX
        tk.Label(fields_frame, text="Confirm Password ", bg='#ecf0f1', font=('Arial', 11, 'bold'),
                 fg='#2c3e50').grid(row=row, column=0, sticky='w', pady=(0, 5))
        confirm_frame = tk.Frame(fields_frame, bg='#ecf0f1')
        confirm_frame.grid(row=row, column=1, pady=(0, 15), padx=(10, 0), sticky='ew')
        confirm_var = tk.StringVar()
        confirm_entry = tk.Entry(confirm_frame, textvariable=confirm_var, show="•", width=25, font=('Arial', 11),
                                 bd=2, relief='solid', bg='white')
        confirm_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        confirm_eye_label = tk.Label(confirm_frame, text="👁️", cursor="hand2",
                                     bg='white', fg='#7f8c8d', font=('Arial', 14))
        confirm_eye_label.pack(side=tk.RIGHT, padx=(5, 0))
        confirm_eye_label.bind("<Button-1>", lambda e: self.toggle_password_visibility(confirm_entry))
        row += 1

        # First Name
        tk.Label(fields_frame, text="First Name ", bg='#ecf0f1', font=('Arial', 11, 'bold'),
                 fg='#2c3e50').grid(row=row, column=0, sticky='w', pady=(0, 5))
        first_name_var = tk.StringVar()
        first_name_entry = tk.Entry(fields_frame, textvariable=first_name_var, width=30, font=('Arial', 11),
                                    bd=2, relief='solid', bg='white')
        first_name_entry.grid(row=row, column=1, pady=(0, 15), padx=(10, 0), sticky='ew')
        row += 1

        # Last Name
        tk.Label(fields_frame, text="Last Name ", bg='#ecf0f1', font=('Arial', 11, 'bold'),
                 fg='#2c3e50').grid(row=row, column=0, sticky='w', pady=(0, 5))
        last_name_var = tk.StringVar()
        last_name_entry = tk.Entry(fields_frame, textvariable=last_name_var, width=30, font=('Arial', 11),
                                   bd=2, relief='solid', bg='white')
        last_name_entry.grid(row=row, column=1, pady=(0, 15), padx=(10, 0), sticky='ew')
        row += 1

        # Phone
        tk.Label(fields_frame, text="Phone ", bg='#ecf0f1', font=('Arial', 11),
                 fg='#2c3e50').grid(row=row, column=0, sticky='w', pady=(0, 5))
        phone_var = tk.StringVar()
        phone_entry = tk.Entry(fields_frame, textvariable=phone_var, width=30, font=('Arial', 11),
                               bd=2, relief='solid', bg='white')
        phone_entry.grid(row=row, column=1, pady=(0, 15), padx=(10, 0), sticky='ew')
        row += 1

        # Email
        tk.Label(fields_frame, text="Email ", bg='#ecf0f1', font=('Arial', 11),
                 fg='#2c3e50').grid(row=row, column=0, sticky='w', pady=(0, 5))
        email_var = tk.StringVar()
        email_entry = tk.Entry(fields_frame, textvariable=email_var, width=30, font=('Arial', 11),
                               bd=2, relief='solid', bg='white')
        email_entry.grid(row=row, column=1, pady=(0, 15), padx=(10, 0), sticky='ew')
        row += 1

        info_label = tk.Label(fields_frame,
                              text="⚠️ Password must be at least 8 characters with letters, numbers, and special characters",
                              bg='#ecf0f1', fg='#e74c3c', font=('Arial', 9, 'italic'), wraplength=400)
        info_label.grid(row=row, column=0, columnspan=2, pady=(20, 0), sticky='w')
        row += 1

        button_frame = tk.Frame(main_frame, bg='#2c3e50')
        button_frame.pack(fill=tk.X, pady=(10, 0))

        def submit():
            data = {
                'username': username_var.get().strip(),
                'password': password_var.get(),
                'confirm': confirm_var.get(),
                'first_name': first_name_var.get().strip(),
                'last_name': last_name_var.get().strip(),
                'phone': phone_var.get().strip(),
                'email': email_var.get().strip()
            }

            required_fields = ['username', 'password', 'confirm', 'first_name', 'last_name']
            for field in required_fields:
                if not data[field]:
                    messagebox.showerror("Error", f"Please fill in all required fields.")
                    return

            if data['password'] != data['confirm']:
                messagebox.showerror("Error", "Passwords do not match.")
                return

            if len(data['password']) < 8:
                messagebox.showerror("Error", "Password must be at least 8 characters.")
                return

            import re
            has_letter = re.search(r'[a-zA-Z]', data['password']) is not None
            has_number = re.search(r'[0-9]', data['password']) is not None
            has_special = re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', data['password']) is not None

            if not (has_letter and has_number and has_special):
                messagebox.showerror("Error",
                                     "Password must contain:\n"
                                     "• At least one letter (a-z, A-Z)\n"
                                     "• At least one number (0-9)\n"
                                     "• At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)")
                return

            if len(data['username']) < 3:
                messagebox.showerror("Error", "Username must be at least 3 characters.")
                return

            if data['phone'] and not re.match(r'^[0-9+\- ]+$', data['phone']):
                messagebox.showerror("Error", "Phone number can only contain digits, plus, hyphen, or space.")
                return

            if data['email']:
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, data['email']):
                    messagebox.showerror("Error", "Invalid email format. Please enter a valid email address.")
                    return

            success, message = self.db.create_staff_account(
                data['username'],
                data['password'],
                data['first_name'],
                data['last_name'],
                data['phone'],
                data['email']
            )

            if success:
                messagebox.showinfo("Success", message)
                self.db.log_activity(self.user_info['user_id'], f"Created staff account: {data['username']}")
                self.load_staff_list()
                dialog.destroy()
            else:
                messagebox.showerror("Error", message)

        create_btn = tk.Button(
            button_frame,
            text="💾 CREATE ACCOUNT",
            command=submit,
            bg='#27ae60',
            fg='white',
            font=('Arial', 14, 'bold'),
            width=18,
            height=2,
            relief='raised',
            bd=3
        )
        create_btn.pack(side=tk.LEFT, padx=(0, 10), pady=10)

        cancel_btn = tk.Button(
            button_frame,
            text="✗ CANCEL",
            command=dialog.destroy,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 14, 'bold'),
            width=18,
            height=2,
            relief='raised',
            bd=3
        )
        cancel_btn.pack(side=tk.RIGHT, pady=10)

        dialog.bind('<Return>', lambda e: submit())

    def toggle_staff_status(self):
        """Toggle staff account active/inactive status."""
        selected = self.staff_tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a staff member to activate/deactivate.")
            return

        staff_id = self.staff_tree.item(selected[0])['values'][0]
        username = self.staff_tree.item(selected[0])['values'][1]
        staff_name = f"{self.staff_tree.item(selected[0])['values'][2]} {self.staff_tree.item(selected[0])['values'][3]}"
        current_status = self.staff_tree.item(selected[0])['values'][8]

        current_status_text = "Active" if current_status == "Yes" else "Inactive"
        new_status_text = "Inactive" if current_status == "Yes" else "Active"

        if not messagebox.askyesno("Confirm Status Change",
                                   f"Change status for {staff_name}?\n\n"
                                   f"Current: {current_status_text}\n"
                                   f"New: {new_status_text}\n\n"
                                   f"This will {'deactivate' if current_status == 'Yes' else 'activate'} the account."):
            return

        success, message = self.db.toggle_staff_status(staff_id)

        if success:
            messagebox.showinfo("Success", f"✅ {message}")
            self.db.log_activity(self.user_info['user_id'],
                                 f"{'Deactivated' if current_status == 'Yes' else 'Activated'} staff account: {username}")
            self.load_staff_list()
        else:
            messagebox.showerror("Error", f"Failed to change status:\n{message}")

    def load_staff_list(self):
        """Load staff list into treeview."""
        for item in self.staff_tree.get_children():
            self.staff_tree.delete(item)

        try:
            result = self.db.execute_query('''
                SELECT user_id, username, first_name, last_name, phone, email, user_type, 
                       CASE WHEN is_active = 1 THEN 'Active' ELSE 'Inactive' END as status,
                       CASE WHEN is_active = 1 THEN 'Yes' ELSE 'No' END as is_active_display,
                       last_login
                FROM users
                WHERE user_type = 'staff'
                ORDER BY user_id
            ''')

            for row in result:
                tags = ()
                if row[7] == 'Inactive':
                    tags = ('inactive',)

                self.staff_tree.insert("", "end", values=row, tags=tags)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load staff list: {e}")

    def load_user_filter_list(self):
        """Load user list for log filter."""
        try:
            result = self.db.execute_query(
                "SELECT username FROM users ORDER BY username"
            )
            users = [row[0] for row in result]
            self.log_user_filter['values'] = ['All Users'] + users
            self.log_user_filter.set('All Users')
        except Exception as e:
            print(f"Error loading user list: {e}")

    def load_all_logs(self):
        """Load all system logs."""
        for item in self.logs_tree.get_children():
            self.logs_tree.delete(item)

        try:
            result = self.db.execute_query('''
                SELECT a.id, a.timestamp, u.username, a.activity_description
                FROM activities a
                JOIN users u ON a.user_id = u.user_id
                ORDER BY a.timestamp DESC
                LIMIT 500
            ''')

            for row in result:
                self.logs_tree.insert("", "end", values=row)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load logs: {e}")

    def clear_all_logs(self):
        """Clear all system logs."""
        if not messagebox.askyesno("Confirm Clear All Logs",
                                   "Are you sure you want to clear ALL system logs?\n\n"
                                   "This action cannot be undone!"):
            return

        try:
            success = self.db.clear_all_logs()
            if success:
                messagebox.showinfo("Success", "All system logs have been cleared.")
                self.db.log_activity(self.user_info['user_id'], "Cleared all system logs")
                self.load_all_logs()
            else:
                messagebox.showerror("Error", "Failed to clear logs.")
        except Exception as e:
            messagebox.showerror("Error", f"Database error: {e}")

    def change_admin_password(self):
        """Change admin password."""
        current = self.current_pass.get()
        new = self.new_pass.get()
        confirm = self.confirm_pass.get()

        if not all([current, new, confirm]):
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        if new != confirm:
            messagebox.showerror("Error", "New passwords do not match.")
            return

        if len(new) < 8:
            messagebox.showerror("Error", "New password must be at least 8 characters.")
            return

        result = self.db.execute_query(
            "SELECT password FROM users WHERE user_id = ?",
            (self.user_info['user_id'],)
        )

        if not result or not PasswordManager.check_password(current, result[0][0]):
            messagebox.showerror("Error", "Current password is incorrect.")
            return

        hashed_password = PasswordManager.hash_password(new)
        success = self.db.execute_write(
            "UPDATE users SET password = ? WHERE user_id = ?",
            (hashed_password, self.user_info['user_id'])
        )

        if success:
            self.db.log_activity(self.user_info['user_id'], "Changed admin password")
            messagebox.showinfo("Success", "Password changed successfully.")

            self.current_pass.delete(0, tk.END)
            self.new_pass.delete(0, tk.END)
            self.confirm_pass.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Failed to change password.")

    def backup_database(self):
        """Create a backup of the database."""
        backup_dir = filedialog.askdirectory(title="Select backup location")
        if not backup_dir:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"rental_backup_{timestamp}.db")

        try:
            self.db.conn.close()

            shutil.copy2(DATABASE_FILENAME, backup_file)

            self.db.conn = sqlite3.connect(DATABASE_FILENAME, check_same_thread=False)
            self.db.cursor = self.db.conn.cursor()

            messagebox.showinfo("Success", f"Database backed up to:\n{backup_file}")
            self.db.log_activity(self.user_info['user_id'], "Created database backup")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to backup database: {e}")
            try:
                self.db.conn = sqlite3.connect(DATABASE_FILENAME, check_same_thread=False)
                self.db.cursor = self.db.conn.cursor()
            except:
                pass

    def restore_database(self):
        """Restore database from backup."""
        if not messagebox.askyesno("Warning",
                                   "This will replace the current database with the backup.\nAll changes since the backup will be lost!\n\nAre you sure you want to proceed?"):
            return

        backup_file = filedialog.askopenfilename(
            title="Select backup file",
            filetypes=[("Database files", "*.db"), ("All files", "*.*")]
        )

        if not backup_file:
            return

        try:
            self.db.conn.close()

            shutil.copy2(backup_file, DATABASE_FILENAME)

            self.db.conn = sqlite3.connect(DATABASE_FILENAME, check_same_thread=False)
            self.db.cursor = self.db.conn.cursor()
            self.db.setup_tables()

            messagebox.showinfo("Success", "Database restored successfully!")
            self.db.log_activity(self.user_info['user_id'], "Restored database from backup")

            self.logout()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore database: {e}")
            try:
                self.db.conn = sqlite3.connect(DATABASE_FILENAME, check_same_thread=False)
                self.db.cursor = self.db.conn.cursor()
            except:
                pass

    def logout(self):
        """Logout admin and return to login screen."""
        self.session_running = False
        self.db.log_activity(self.user_info['user_id'], "Logged out from admin dashboard")
        self.master.destroy()
        self.logout_callback()


class StaffRentalSystem:
    """Staff rental management system with enhanced features."""

    def __init__(self, master, user_info, logout_callback):
        self.master = master
        self.user_info = user_info
        self.logout_callback = logout_callback

        self.master.title(f"Rental Management System - Staff: {user_info['first_name']}")
        self.master.configure(bg='#f0f0f0')
        self.master.state('zoomed')

        self.db = DatabaseManager()

        self.session_check_thread = None
        self.session_running = True

        self.rates = {
            "Barrow": {"daily": 15, "weekly": 80, "monthly": 250},
            "Scaffold (per unit)": {"daily": 30, "weekly": 40, "monthly": 120},
        }

        self.rental_items = []
        self.rental_start_date = datetime.now()
        self.rental_end_date = datetime.now()

        self.setup_ui()
        self.log_activity("Logged in to rental system")
        self.start_session_check()
        self.setup_function_keys()

    def setup_function_keys(self):
        """Setup function key bindings."""
        self.master.bind('<F1>', lambda e: self.print_receipt())
        self.master.bind('<F2>', lambda e: self.new_rental())
        self.master.bind('<F3>', lambda e: self.open_quick_rental())
        self.master.bind('<F4>', lambda e: self.show_not_returned())
        self.master.bind('<F5>', lambda e: self.import_rental_data())
        self.master.bind('<F6>', lambda e: self.show_active_summary_fullscreen())
        self.master.bind('<F8>', lambda e: self.exit_system())

    def setup_ui(self):
        """Setup staff rental system UI."""
        header_frame = tk.Frame(self.master, bg='#2980b9', height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="BARROW & SCAFFOLD RENTAL MANAGEMENT SYSTEM",
            font=('Helvetica', 16, 'bold'),
            bg='#2980b9',
            fg='white'
        )
        title_label.pack(side=tk.LEFT, padx=20)

        right_frame = tk.Frame(header_frame, bg='#2980b9')
        right_frame.pack(side=tk.RIGHT, padx=20)

        user_label = tk.Label(
            right_frame,
            text=f"Staff: {self.user_info['first_name']} {self.user_info['last_name']}",
            font=('Arial', 12, 'bold'),
            bg='#2980b9',
            fg='white'
        )
        user_label.pack(side=tk.LEFT, padx=(0, 15))

        main_frame = tk.Frame(self.master, bg='#ecf0f1', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        main_frame.grid_rowconfigure(0, weight=0)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_rowconfigure(2, weight=0)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        self.create_customer_section(main_frame)
        self.create_rental_items_section(main_frame)
        self.create_rental_period_section(main_frame)
        self.create_results_and_buttons_section(main_frame)

    def exit_system(self):
        """Exit the entire system with confirmation."""
        if messagebox.askyesno("Exit System", "Are you sure you want to exit ?"):
            self.session_running = False
            self.log_activity("Exited the system")
            self.master.destroy()
            import sys
            sys.exit(0)

    def start_session_check(self):
        """Start thread to check for session timeout."""

        def check_session():
            while self.session_running:
                time.sleep(60)
                self.db.update_session_timeout(self.user_info['user_id'])
                if self.db.check_session_timeout(self.user_info['user_id']):
                    self.master.after(0, self.session_timeout)
                    break

        self.session_check_thread = threading.Thread(target=check_session, daemon=True)
        self.session_check_thread.start()

    def session_timeout(self):
        """Handle session timeout."""
        if messagebox.askyesno("Session Timeout",
                               "Your session has expired due to inactivity. Would you like to login again?"):
            self.logout()
        else:
            self.logout()

    def create_customer_section(self, parent):
        """Create customer details section WITHOUT black borders."""
        cust_frame = tk.LabelFrame(parent, text="Customer Details", bg='#f0f0f0',
                                   padx=10, pady=10, font=('Arial', 12))
        cust_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        ttk.Label(cust_frame, text="Customer Name").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.cust_name = tk.Entry(cust_frame, width=40, bd=2, relief='solid')
        self.cust_name.grid(row=0, column=1, padx=5, pady=5, columnspan=3, sticky='ew')

        ttk.Label(cust_frame, text="Phone Number").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.cust_phone = tk.Entry(cust_frame, width=25, bd=2, relief='solid')
        self.cust_phone.grid(row=1, column=1, padx=5, pady=5, sticky='ew')

        ttk.Label(cust_frame, text="ID/Reference").grid(row=1, column=2, sticky="e", padx=5, pady=5)
        self.cust_id = tk.Entry(cust_frame, width=25, bd=2, relief='solid')
        self.cust_id.grid(row=1, column=3, padx=5, pady=5, sticky='ew')

        ttk.Label(cust_frame, text="Deposit Paid").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.deposit = tk.Entry(cust_frame, width=25, bd=2, relief='solid')
        self.deposit.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        self.deposit.insert(0, "0.00")

        for i in range(4):
            cust_frame.grid_columnconfigure(i, weight=1)

    def create_rental_items_section(self, parent):
        """Create rental items section WITHOUT black borders."""
        items_frame = tk.LabelFrame(parent, text="Rental Items", bg='#f0f0f0',
                                    padx=10, pady=10, font=('Arial', 12))
        items_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 5), padx=(0, 10))

        items_frame.grid_rowconfigure(1, weight=1)
        items_frame.grid_columnconfigure(0, weight=1)

        control_frame = tk.Frame(items_frame, bg='#f0f0f0')
        control_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(control_frame, text="Item Type").pack(side=tk.LEFT, padx=5)
        self.item_type = ttk.Combobox(control_frame, values=list(self.rates.keys()), width=20)
        self.item_type.pack(side=tk.LEFT, padx=5)
        self.item_type.current(0)

        ttk.Label(control_frame, text="Quantity").pack(side=tk.LEFT, padx=(10, 5))
        self.quantity = tk.Spinbox(control_frame, from_=1, to=100, width=8, bd=2, relief='solid')
        self.quantity.pack(side=tk.LEFT, padx=5)

        add_btn = tk.Button(
            control_frame,
            text="Add Item",
            command=self.add_rental_item,
            bg='#3498db',
            fg='white',
            font=('Arial', 11, 'bold'),
            height=2,
            width=15
        )
        add_btn.pack(side=tk.LEFT, padx=10)

        tree_frame = tk.Frame(items_frame, bg='#f0f0f0')
        tree_frame.grid(row=1, column=0, sticky="nsew")

        columns = ("Item", "Qty", "Rate Type", "Daily Rate", "Total")
        self.items_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8)

        col_widths = [120, 60, 80, 80, 80]
        for i, col in enumerate(columns):
            self.items_tree.heading(col, text=col)
            self.items_tree.column(col, width=col_widths[i], anchor="center")

        items_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=items_scrollbar.set)

        self.items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        items_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        remove_btn = tk.Button(
            items_frame,
            text="Remove Selected",
            command=self.remove_item,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 11, 'bold'),
            height=2,
            width=15
        )
        remove_btn.grid(row=2, column=0, pady=(10, 0), sticky="ew")

    def create_rental_period_section(self, parent):
        """Create rental period section WITHOUT black borders."""
        period_frame = tk.LabelFrame(parent, text="Rental Period", bg='#f0f0f0',
                                     padx=10, pady=10, font=('Arial', 12))
        period_frame.grid(row=1, column=1, sticky="nsew", pady=(0, 5), padx=(10, 0))

        for i in range(4):
            period_frame.grid_columnconfigure(i, weight=1)

        ttk.Label(period_frame, text="Start Date").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.start_date = tk.Entry(period_frame, width=15, bd=2, relief='solid')
        self.start_date.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        self.start_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ttk.Label(period_frame, text="Time").grid(row=0, column=2, sticky="e", padx=5, pady=5)
        self.start_time = ttk.Combobox(period_frame,
                                       values=["08:00", "09:00", "10:00", "11:00", "12:00",
                                               "13:00", "14:00", "15:00", "16:00"], width=8)
        self.start_time.grid(row=0, column=3, padx=5, pady=5, sticky='ew')
        self.start_time.current(0)

        ttk.Label(period_frame, text="Return Date Required").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.end_date = tk.Entry(period_frame, width=15, bd=2, relief='solid')
        self.end_date.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        self.end_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ttk.Label(period_frame, text="Time Required").grid(row=1, column=2, sticky="e", padx=5, pady=5)
        self.end_time = ttk.Combobox(period_frame,
                                     values=["08:00", "09:00", "10:00", "11:00", "12:00",
                                             "13:00", "14:00", "15:00", "16:00"], width=8)
        self.end_time.grid(row=1, column=3, padx=5, pady=5, sticky='ew')
        self.end_time.current(0)

        ttk.Label(period_frame, text="Rate Type").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.rate_type = ttk.Combobox(period_frame, values=["daily", "weekly", "monthly"], width=10)
        self.rate_type.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        self.rate_type.current(0)

        calc_btn = tk.Button(
            period_frame,
            text="Calculate Period",
            command=self.calculate_rental_period,
            bg='#f39c12',
            fg='white',
            font=('Arial', 11, 'bold'),
            height=2,
            width=15
        )
        calc_btn.grid(row=2, column=2, columnspan=2, padx=5, pady=5, sticky='ew')

        self.period_display = ttk.Label(period_frame, text="Rental Period: 0 days", font=('Arial', 11, 'bold'))
        self.period_display.grid(row=3, column=0, columnspan=4, pady=(10, 0), sticky='ew')

        period_frame.grid_rowconfigure(4, weight=1)

    def create_results_and_buttons_section(self, parent):
        """Create combined results and buttons section WITHOUT black borders."""
        bottom_frame = tk.Frame(parent, bg='#ecf0f1')
        bottom_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(20, 0))

        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=2)

        results_frame = tk.LabelFrame(bottom_frame, text="Calculation Results", bg='#f0f0f0',
                                      padx=15, pady=15, font=('Arial', 12))
        results_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        results_frame.grid_propagate(False)
        results_frame.config(height=180, width=350)

        for i in range(4):
            results_frame.grid_rowconfigure(i, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_columnconfigure(1, weight=2)

        ttk.Label(results_frame, text="Rental Charges", font=('Arial', 11)).grid(row=0, column=0, sticky="e", padx=5,
                                                                                 pady=8)
        self.rental_charges = tk.Label(results_frame, text="GH₵0.00", background='white',
                                       relief="solid", width=15, font=('Arial', 11), bd=2)
        self.rental_charges.grid(row=0, column=1, padx=5, pady=8, sticky="ew")

        ttk.Label(results_frame, text="Deposit Paid", font=('Arial', 11)).grid(row=1, column=0, sticky="e", padx=5,
                                                                               pady=8)
        self.deposit_paid = tk.Label(results_frame, text="GH₵0.00", background='white',
                                     relief="solid", width=15, font=('Arial', 11), bd=2)
        self.deposit_paid.grid(row=1, column=1, padx=5, pady=8, sticky="ew")

        ttk.Label(results_frame, text="Total Due", font=('Arial', 12, 'bold'),
                  foreground="red").grid(row=2, column=0, sticky="e", padx=5, pady=8)
        self.total_due = tk.Label(results_frame, text="GH₵0.00", background='white',
                                  relief="solid", width=15, font=('Arial', 11), foreground="red", bd=2)
        self.total_due.grid(row=2, column=1, padx=5, pady=8, sticky="ew")

        buttons_frame = tk.Frame(bottom_frame, bg='#34495e', padx=10, pady=15)
        buttons_frame.grid(row=0, column=1, sticky="nsew")

        for i in range(3):
            buttons_frame.grid_columnconfigure(i, weight=1)
        for i in range(2):
            buttons_frame.grid_rowconfigure(i, weight=1)

        buttons_config = [
            ("Print Receipt ", lambda: self.print_receipt(), "#2196F3", 0, 0),
            ("New Rental ", lambda: self.new_rental(), "#FF9800", 0, 1),
            ("Quick Rental ", lambda: self.open_quick_rental(), "#FFA500", 0, 2),

            ("Active Summary ", lambda: self.show_active_summary_fullscreen(), "#3498db", 1, 0),
            ("Not Returned ", lambda: self.show_not_returned(), "#E91E63", 1, 1),
            ("Exit ", lambda: self.exit_system(), "#4CAF50", 1, 2),
        ]

        for text, command, color, row, col in buttons_config:
            btn = tk.Button(buttons_frame, text=text, command=command,
                            bg=color, fg="white", font=('Arial', 10, 'bold'),
                            height=3, width=15, relief='raised', bd=2)
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

    def log_activity(self, description: str):
        """Log staff activity."""
        self.db.log_activity(self.user_info['user_id'], description)

    def add_rental_item(self):
        """Add item to rental list."""
        item = self.item_type.get()
        try:
            qty = int(self.quantity.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid quantity")
            return

        rate_type = self.rate_type.get()

        if item and qty > 0:
            daily_rate = self.rates[item][rate_type]
            total = qty * daily_rate

            self.items_tree.insert("", "end", values=(item, qty, rate_type,
                                                      f"GH₵{daily_rate:.2f}", f"GH₵{total:.2f}"))
            self.rental_items.append({
                "item": item,
                "quantity": qty,
                "rate_type": rate_type,
                "daily_rate": daily_rate,
                "total": total
            })

            self.log_activity(f"Added rental item: {item} (Qty: {qty})")

            self.auto_calculate_total()
        else:
            messagebox.showerror("Error", "Please select an item and quantity")

    def auto_calculate_total(self):
        """Automatically calculate total when items are added."""
        try:
            if not self.rental_items:
                self.rental_charges.config(text="GH₵0.00")
                self.deposit_paid.config(text="GH₵0.00")
                self.total_due.config(text="GH₵0.00")
                return

            # Calculate days using the same logic as calculate_rental_period
            try:
                start_date_str = f"{self.start_date.get()} {self.start_time.get()}"
                end_date_str = f"{self.end_date.get()} {self.end_time.get()}"
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M")
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M")

                # Ensure end date is not before start date
                if end_date < start_date:
                    end_date = start_date

                # Calculate days - minimum 1 day
                delta = end_date - start_date
                days = delta.days

                # If same day rental, it's 1 day
                if days == 0:
                    days = 1
            except:
                days = 1

            # Calculate total rental charges
            total_rental = sum(item['total'] * days for item in self.rental_items)

            # Get deposit amount safely
            try:
                deposit_text = self.deposit.get()
                deposit = float(deposit_text) if deposit_text else 0.0
            except ValueError:
                deposit = 0.0

            # Format with 2 decimal places
            self.rental_charges.config(text=f"GH₵{total_rental:.2f}")
            self.deposit_paid.config(text=f"GH₵{deposit:.2f}")

            total_due = max(0, total_rental - deposit)
            self.total_due.config(text=f"GH₵{total_due:.2f}")

        except Exception as e:
            print(f"Error in auto_calculate_total: {e}")
            # Set default values on error
            self.rental_charges.config(text="GH₵0.00")
            self.deposit_paid.config(text="GH₵0.00")
            self.total_due.config(text="GH₵0.00")

    def remove_item(self):
        """Remove selected item from rental list."""
        selected_item = self.items_tree.selection()
        if selected_item:
            index = self.items_tree.index(selected_item[0])
            self.items_tree.delete(selected_item)
            if index < len(self.rental_items):
                removed_item = self.rental_items.pop(index)
                self.log_activity(f"Removed rental item: {removed_item['item']}")

            self.auto_calculate_total()
        else:
            messagebox.showerror("Error", "Please select an item to remove")

    def calculate_rental_period(self):
        """Calculate rental period in days."""
        try:
            start_date_str = f"{self.start_date.get()} {self.start_time.get()}"
            end_date_str = f"{self.end_date.get()} {self.end_time.get()}"

            start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M")

            delta = end_date - start_date
            days = delta.days

            self.period_display.config(text=f"Rental Period: {days} days")
            self.rental_start_date = start_date
            self.rental_end_date = end_date

            self.log_activity(f"Calculated rental period: {days} days")

            self.auto_calculate_total()

        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")

    def generate_reference_number(self):
        """Generate a unique reference number."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_num = random.randint(100, 999)
        return f"REF{timestamp}{random_num}"

    def store_reference(self, customer_name: str, reference_number: str) -> bool:
        """Store reference number in the database."""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return self.db.execute_write('''
                INSERT OR IGNORE INTO reference_storage (reference_number, customer_name, date_created, status, created_by)
                VALUES (?, ?, ?, ?, ?)
            ''', (reference_number, customer_name, current_date, 'Active', self.user_info['user_id']))
        except Exception as e:
            print(f"Error storing reference: {e}")
            return False

    def generate_receipt_text(self, customer_name: str, reference_number: str) -> str:
        """Generate receipt text for printing."""
        try:
            # Get current date and time
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Calculate amounts
            rental_charges_amount = float(self.rental_charges['text'].replace("GH₵", "").strip())
            deposit_amount = float(self.deposit_paid['text'].replace("GH₵", "").strip())
            total_due_amount = float(self.total_due['text'].replace("GH₵", "").strip())

            # Get items from tree
            items_text = ""
            for item in self.items_tree.get_children():
                values = self.items_tree.item(item)['values']
                items_text += f"{values[0]} x {values[1]} ({values[2]}) - {values[4]}\n"

            # Generate receipt
            receipt = f"""
{'=' * 40}
        KOB BARROW & SCAFFOLD RENTALS
{'=' * 40}
Date: {current_time}
Reference: {reference_number}
{'=' * 40}
Customer: {customer_name}
Phone: {self.cust_phone.get()}
{'=' * 40}
ITEMS RENTED:
{items_text}
{'=' * 40}
Rental Charges: GH₵{rental_charges_amount:.2f}
Deposit Paid: GH₵{deposit_amount:.2f}
Total Due: GH₵{total_due_amount:.2f}
{'=' * 40}
Rental Period: {self.period_display['text']}
{'=' * 40}
        THANK YOU FOR YOUR BUSINESS!
{'=' * 40}
Developed by Techify Solution
Call us on 0547607270
{'=' * 40}
"""
            return receipt
        except Exception as e:
            print(f"Error generating receipt text: {e}")
            return ""

    def save_rental(self, customer_name: str, phone: str, reference_number: str,
                    rental_charges: float, deposit_paid: float):
        """Save rental data to database."""
        try:
            items_text = ", ".join([f"{item['item']} x {item['quantity']}" for item in self.rental_items])

            success = self.db.execute_write('''
                INSERT INTO rentals 
                (customer_name, phone, customer_id, start_date, end_date, items, 
                 rental_charges, deposit_paid, total_due, status, created_at, user_id, receipt_printed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                customer_name,
                phone,
                reference_number,
                self.rental_start_date.strftime("%Y-%m-%d %H:%M"),
                self.rental_end_date.strftime("%Y-%m-%d %H:%M"),
                items_text,
                rental_charges,
                deposit_paid,
                rental_charges - deposit_paid,
                'Rented',
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                self.user_info['user_id'],
                1  # receipt_printed
            ))

            return success
        except Exception as e:
            print(f"Error saving rental: {e}")
            return False

    def save_receipt_to_file(self, customer_name: str, receipt_text: str):
        """Save receipt to a file."""
        try:
            # Clean customer name for filename
            clean_name = "".join(c for c in customer_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Receipt_{clean_name}_{timestamp}.txt"
            filepath = os.path.join(RECEIPTS_FOLDER, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(receipt_text)

            return filepath
        except Exception as e:
            print(f"Error saving receipt to file: {e}")
            return None

    def open_receipt_for_printing(self, receipt_text: str):
        """Open receipt in default text editor for printing."""
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(receipt_text)
                temp_file = f.name

            # Open the file with default application
            if platform.system() == 'Windows':
                os.startfile(temp_file)
            elif platform.system() == 'Darwin':  # macOS
                os.system(f'open "{temp_file}"')
            else:  # Linux
                os.system(f'xdg-open "{temp_file}"')

            # File will be deleted when program exits
            return True
        except Exception as e:
            print(f"Error opening receipt for printing: {e}")
            return False

    def print_receipt(self):
        """Generate and print receipt with duplicate printing prevention and review."""
        try:
            customer_name = self.cust_name.get().strip()
            phone = self.cust_phone.get().strip()

            if not customer_name:
                messagebox.showerror("Error", "Please enter customer name")
                return

            cleaned_customer_name = customer_name.replace('*', '')
            if not re.match("^[A-Za-z ]+$", cleaned_customer_name):
                messagebox.showerror("Error", "Customer name must contain only alphabetic characters.")
                return

            if phone and not re.match(r'^[0-9+ ]', phone):
                messagebox.showerror("Error", "Phone number can only contain digits, plus, hyphen, or space.")
                return

            self.auto_calculate_total()

            rental_charges_amount = float(self.rental_charges['text'].replace("GH₵", "").strip())
            deposit_amount = float(self.deposit_paid['text'].replace("GH₵", "").strip())

            reference_number = self.generate_reference_number()

            existing_reference = self.cust_id.get().strip()
            if existing_reference:
                if self.db.check_receipt_printed(existing_reference):
                    messagebox.showerror("Error",
                                         "❌ Cannot print the same rental receipt duplicate!\n\nThis receipt has already been printed and cannot be printed again.")
                    return
                else:
                    reference_number = existing_reference

            if not self.store_reference(customer_name, reference_number):
                reference_number = self.generate_reference_number()
                self.store_reference(customer_name, reference_number)

            # Generate receipt text for preview
            receipt = self.generate_receipt_text(customer_name, reference_number)

            # Create receipt review dialog
            review_dialog = tk.Toplevel(self.master)
            review_dialog.title("Review Receipt Before Printing")
            review_dialog.geometry("600x700")
            review_dialog.configure(bg='#2c3e50')
            review_dialog.grab_set()

            main_frame = tk.Frame(review_dialog, bg='#2c3e50', padx=20, pady=20)
            main_frame.pack(fill=tk.BOTH, expand=True)

            tk.Label(main_frame, text="REVIEW RECEIPT BEFORE PRINTING",
                     font=('Arial', 16, 'bold'), bg='#2c3e50', fg='white'
                     ).pack(pady=(0, 15))

            # Receipt preview frame
            preview_frame = tk.Frame(main_frame, bg='white', relief='solid', bd=2)
            preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

            # Create text widget for receipt preview
            receipt_text = tk.Text(preview_frame, wrap='word', font=('Courier', 10),
                                   bg='white', fg='black', height=25, width=60)
            receipt_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            receipt_text.insert('1.0', receipt)
            receipt_text.config(state='disabled')  # Make it read-only

            # Add scrollbar for receipt preview
            scrollbar = tk.Scrollbar(preview_frame, command=receipt_text.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            receipt_text.config(yscrollcommand=scrollbar.set)

            # Print status label
            print_status_var = tk.StringVar()
            print_status_var.set("Ready to print")
            status_label = tk.Label(main_frame, textvariable=print_status_var,
                                    font=('Arial', 11), bg='#2c3e50', fg='white')
            status_label.pack(pady=(0, 10))

            # Buttons frame
            button_frame = tk.Frame(main_frame, bg='#2c3e50')
            button_frame.pack(fill=tk.X)

            def confirm_print():
                """Process the actual printing after confirmation."""
                try:
                    # Check again for duplicate printing (in case status changed)
                    if existing_reference and self.db.check_receipt_printed(existing_reference):
                        print_status_var.set("❌ Error: Receipt already printed!")
                        messagebox.showerror("Error",
                                             "❌ Cannot print the same rental receipt duplicate!\n\nThis receipt has already been printed and cannot be printed again.")
                        review_dialog.destroy()
                        return

                    # Save rental data
                    self.save_rental(customer_name, phone, reference_number,
                                     rental_charges_amount, deposit_amount)

                    remaining_amount = rental_charges_amount - deposit_amount
                    if remaining_amount > 0:
                        description = f"Rental income from {customer_name}"
                        self.db.record_income(remaining_amount, description, self.user_info['user_id'])

                    if deposit_amount > 0:
                        deposit_description = f"Deposit from {customer_name} for rental"
                        self.db.record_income(deposit_amount, deposit_description, self.user_info['user_id'])

                    # Mark receipt as printed
                    success = self.db.mark_receipt_printed(reference_number)
                    if not success:
                        print_status_var.set("❌ Error: Failed to mark receipt as printed!")
                        messagebox.showerror("Error", "Failed to mark receipt as printed. Process rolled back.")
                        review_dialog.destroy()
                        return

                    self.log_activity(f"Printed receipt for: {customer_name}")

                    # Save receipt to file
                    self.save_receipt_to_file(customer_name, receipt)

                    # Open receipt for printing
                    self.open_receipt_for_printing(receipt)

                    print_status_var.set("✅ Receipt printed successfully!")
                    messagebox.showinfo("Success", "✅ Receipt sent to printer!")
                    review_dialog.destroy()

                except Exception as e:
                    print_status_var.set(f"❌ Error: {str(e)}")
                    messagebox.showerror("Error", f"Error during printing: {str(e)}")
                    # Rollback occurs automatically if any step fails

            def cancel_print():
                """Cancel the print process."""
                if messagebox.askyesno("Cancel Print",
                                       "Are you sure you want to cancel printing? No changes will be saved."):
                    print_status_var.set("❌ Print cancelled - no changes saved")
                    review_dialog.destroy()

            # Action buttons
            print_btn = tk.Button(button_frame, text="✅ CONFIRM & PRINT", command=confirm_print,
                                  bg='#27ae60', fg='white', font=('Arial', 12, 'bold'),
                                  width=20, height=2, relief='raised', bd=2)
            print_btn.pack(side=tk.LEFT, padx=(0, 10))

            cancel_btn = tk.Button(button_frame, text="✗ CANCEL PRINT", command=cancel_print,
                                   bg='#e74c3c', fg='white', font=('Arial', 12, 'bold'),
                                   width=20, height=2, relief='raised', bd=2)
            cancel_btn.pack(side=tk.RIGHT)

        except Exception as e:
            messagebox.showerror("Error", f"Error generating receipt: {str(e)}")

    def new_rental(self):
        """Clear form for new rental."""
        self.cust_name.delete(0, tk.END)
        self.cust_phone.delete(0, tk.END)
        self.cust_id.delete(0, tk.END)
        self.deposit.delete(0, tk.END)
        self.deposit.insert(0, "0.00")

        self.items_tree.delete(*self.items_tree.get_children())
        self.rental_items = []

        today = datetime.now().strftime("%Y-%m-%d")
        self.start_date.delete(0, tk.END)
        self.start_date.insert(0, today)
        self.end_date.delete(0, tk.END)
        self.end_date.insert(0, today)

        self.rental_charges.config(text="GH₵0.00")
        self.deposit_paid.config(text="GH₵0.00")
        self.total_due.config(text="GH₵0.00")
        self.period_display.config(text="Rental Period: 1 days")

        self.log_activity("Started new rental")

    def open_quick_rental(self):
        """Open simplified rental out form with same styling as Create Staff Account."""
        dialog = tk.Toplevel(self.master)
        dialog.title("QUICK RENTAL FORM")
        dialog.geometry("550x650")
        dialog.configure(bg='#2c3e50')
        dialog.grab_set()
        dialog.resizable(False, False)

        main_frame = tk.Frame(dialog, bg='#2c3e50', padx=30, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)

        header_frame = tk.Frame(main_frame, bg='#2c3e50', relief='solid', bd=2)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(
            header_frame,
            text="QUICK RENTAL FORM",
            font=('Arial', 18, 'bold'),
            bg='#2c3e50',
            fg='white',
            pady=15
        ).pack()

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        time_label = tk.Label(header_frame, text=f"Time: {current_time}",
                              font=('Arial', 11), bg='#2c3e50', fg='#27ae60')
        time_label.pack(pady=(0, 10))

        form_container = tk.Frame(main_frame, bg='#ecf0f1', relief='solid', bd=2)
        form_container.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        fields_frame = tk.Frame(form_container, bg='#ecf0f1', padx=30, pady=30)
        fields_frame.pack(fill=tk.BOTH, expand=True)

        # Configure grid weights
        for i in range(2):
            fields_frame.grid_columnconfigure(i, weight=1)

        row = 0
        # Customer Name
        tk.Label(fields_frame, text="Customer Name Required", bg='#ecf0f1', font=('Arial', 11, 'bold'),
                 fg='#2c3e50').grid(row=row, column=0, sticky='w', pady=(0, 5))
        name_var = tk.StringVar()
        name_entry = tk.Entry(fields_frame, textvariable=name_var, width=30, font=('Arial', 11),
                              bd=2, relief='solid', bg='white')
        name_entry.grid(row=row, column=1, pady=(0, 15), padx=(10, 0), sticky='ew')
        name_entry.focus_set()
        row += 1

        # Phone
        tk.Label(fields_frame, text="Phone Required", bg='#ecf0f1', font=('Arial', 11, 'bold'),
                 fg='#2c3e50').grid(row=row, column=0, sticky='w', pady=(0, 5))
        phone_var = tk.StringVar()
        phone_entry = tk.Entry(fields_frame, textvariable=phone_var, width=30, font=('Arial', 11),
                               bd=2, relief='solid', bg='white')
        phone_entry.grid(row=row, column=1, pady=(0, 15), padx=(10, 0), sticky='ew')
        row += 1

        # Item
        tk.Label(fields_frame, text="Item Required", bg='#ecf0f1', font=('Arial', 11, 'bold'),
                 fg='#2c3e50').grid(row=row, column=0, sticky='w', pady=(0, 5))
        item_var = tk.StringVar()
        item_combo = ttk.Combobox(fields_frame, textvariable=item_var,
                                  values=list(self.rates.keys()), width=28, font=('Arial', 11))
        item_combo.grid(row=row, column=1, pady=(0, 15), padx=(10, 0), sticky='ew')
        item_combo.current(0)
        row += 1

        # Quantity
        tk.Label(fields_frame, text="Quantity Required", bg='#ecf0f1', font=('Arial', 11, 'bold'),
                 fg='#2c3e50').grid(row=row, column=0, sticky='w', pady=(0, 5))
        quantity_frame = tk.Frame(fields_frame, bg='#ecf0f1')
        quantity_frame.grid(row=row, column=1, pady=(0, 15), padx=(10, 0), sticky='ew')
        quantity_var = tk.StringVar(value="1")
        quantity_spin = tk.Spinbox(quantity_frame, from_=1, to=100,
                                   textvariable=quantity_var, width=10, font=('Arial', 11),
                                   bd=2, relief='solid', bg='white')
        quantity_spin.pack(side=tk.LEFT)
        row += 1

        # Area
        tk.Label(fields_frame, text="Job Site Location", bg='#ecf0f1', font=('Arial', 11, 'bold'),
                 fg='#2c3e50').grid(row=row, column=0, sticky='w', pady=(0, 5))
        area_var = tk.StringVar()
        area_entry = tk.Entry(fields_frame, textvariable=area_var, width=30, font=('Arial', 11),
                              bd=2, relief='solid', bg='white')
        area_entry.grid(row=row, column=1, pady=(0, 15), padx=(10, 0), sticky='ew')
        row += 1

        # Rate Type
        tk.Label(fields_frame, text="Rate Type Required", bg='#ecf0f1', font=('Arial', 11, 'bold'),
                 fg='#2c3e50').grid(row=row, column=0, sticky='w', pady=(0, 5))
        rate_var = tk.StringVar()
        rate_combo = ttk.Combobox(fields_frame, textvariable=rate_var,
                                  values=["daily", "weekly"], width=10, font=('Arial', 11))
        rate_combo.grid(row=row, column=1, pady=(0, 15), padx=(10, 0), sticky='w')
        rate_combo.current(0)
        row += 1

        # Deposit Paid
        tk.Label(fields_frame, text="Deposit Paid Required", bg='#ecf0f1', font=('Arial', 11, 'bold'),
                 fg='#2c3e50').grid(row=row, column=0, sticky='w', pady=(0, 5))
        deposit_var = tk.StringVar(value="0.00")
        deposit_entry = tk.Entry(fields_frame, textvariable=deposit_var, width=30, font=('Arial', 11),
                                 bd=2, relief='solid', bg='white')
        deposit_entry.grid(row=row, column=1, pady=(0, 15), padx=(10, 0), sticky='ew')
        row += 1

        ref_number = self.generate_reference_number()
        ref_label = tk.Label(fields_frame, text=f"Reference: {ref_number}",
                             bg='#ecf0f1', font=('Arial', 11, 'bold'), fg='#27ae60')
        ref_label.grid(row=row, column=0, columnspan=2, pady=(20, 0))
        row += 1

        button_frame = tk.Frame(main_frame, bg='#2c3e50')
        button_frame.pack(fill=tk.X, pady=(10, 0))

        def save_quick_rental():
            name = name_var.get().strip()
            phone = phone_var.get().strip()
            item = item_var.get()
            quantity = quantity_var.get()
            area = area_var.get().strip()
            rate_type = rate_var.get()
            deposit_str = deposit_var.get().strip()

            if not all([name, phone, item, quantity, area, deposit_str]):
                messagebox.showerror("Error", "Please fill all required fields.")
                return

            cleaned_name = name.replace('*', '')
            if not re.match("^[A-Za-z ]+$", cleaned_name):
                messagebox.showerror("Error", "Customer name must contain only alphabetic characters.")
                return

            if phone and not re.match(r'^[0-9+\- ]+$', phone):
                messagebox.showerror("Error", "Phone number can only contain digits, plus, hyphen, or space.")
                return

            try:
                qty = int(quantity)
                deposit_amount = float(deposit_str)
                current_date = datetime.now().strftime("%Y-%m-%d")
                current_time = datetime.now().strftime("%H:%M")

                success = self.db.add_to_not_returned(
                    ref_number, name, phone, area, item, qty, rate_type, deposit_amount, self.user_info['user_id']
                )

                if success:
                    self.store_reference(name, ref_number)

                    messagebox.showinfo("Success",
                                        f"✅ Rental Recorded Successfully!\n\n"
                                        f"Reference: {ref_number}\n"
                                        f"Customer: {name}\n"
                                        f"Item: {item} x {qty}\n"
                                        f"Area: {area}\n"
                                        f"Deposit: GH₵{deposit_amount:.2f}\n"
                                        f"Time: {current_time}")

                    self.log_activity(f"Quick rental - Ref: {ref_number}, Item: {item} x {qty}")

                    dialog.destroy()
                    self.show_not_returned()
                else:
                    messagebox.showerror("Error", "Failed to save rental data")

            except ValueError as ve:
                if "deposit" in str(ve).lower():
                    messagebox.showerror("Error", "Please enter a valid deposit amount (e.g., 0.00)")
                else:
                    messagebox.showerror("Error", "Please enter valid quantity and deposit amount")
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Reference number already exists")
            except Exception as e:
                messagebox.showerror("Error", f"Error saving data: {str(e)}")

        save_btn = tk.Button(
            button_frame,
            text="💾 SAVE RENTAL",
            command=save_quick_rental,
            bg='#27ae60',
            fg='white',
            font=('Arial', 14, 'bold'),
            width=18,
            height=3,
            relief='raised',
            bd=3
        )
        save_btn.pack(side=tk.LEFT, padx=(0, 10), pady=10)

        cancel_btn = tk.Button(
            button_frame,
            text="✗ CANCEL",
            command=dialog.destroy,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 14, 'bold'),
            width=18,
            height=3,
            relief='raised',
            bd=3
        )
        cancel_btn.pack(side=tk.RIGHT, pady=10)

        dialog.bind('<Return>', lambda e: save_quick_rental())

    def import_rental_data(self):
        """Import button function - loads all data when clicked after reference ID is entered."""
        reference = self.cust_id.get().strip()

        if not reference:
            messagebox.showerror("Error", "Please enter a reference ID or use 'TO IMPORT' button first.")
            return

        try:
            rental_data = self.db.get_rental_by_reference(reference)
            if not rental_data:
                messagebox.showerror("Error", f"No rental data found for reference: {reference}")
                return

            customer_name, phone, area, item, quantity, rate_type, deposit_paid, date_out, time_out, receipt_printed, refund_processed, refund_amount = rental_data

            if receipt_printed == 1:
                messagebox.showerror("Error", "❌ Cannot import - receipt already printed!")
                return

            self.cust_name.delete(0, tk.END)
            self.cust_name.insert(0, customer_name)

            self.cust_phone.delete(0, tk.END)
            self.cust_phone.insert(0, phone)

            self.deposit.delete(0, tk.END)
            self.deposit.insert(0, f"{deposit_paid:.2f}")

            if item in self.rates:
                self.item_type.set(item)

            self.quantity.delete(0, tk.END)
            self.quantity.insert(0, str(quantity))

            if rate_type in ["daily", "weekly", "monthly"]:
                self.rate_type.set(rate_type)

            self.start_date.delete(0, tk.END)
            self.start_date.insert(0, date_out)

            self.start_time.delete(0, tk.END)
            if time_out:
                self.start_time.insert(0, time_out)

            self.end_date.delete(0, tk.END)
            self.end_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

            self.add_rental_item()

            self.calculate_rental_period()

            messagebox.showinfo("Success",
                                f"✅ Rental data imported successfully!\n\n"
                                f"Reference: {reference}\n"
                                f"Customer: {customer_name}\n"
                                f"Item: {item} x {quantity}\n"
                                f"Area: {area}\n"
                                f"Deposit: GH₵{deposit_paid:.2f}")

            self.log_activity(f"IMPORT: Loaded all data for reference: {reference}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to import data: {str(e)}")

    def show_not_returned(self):
        """Show list of items not returned with refund and mark as returned buttons."""
        dialog = tk.Toplevel(self.master)
        dialog.title("Items Not Returned")
        dialog.geometry("1200x700")
        dialog.configure(bg='#34495e')
        dialog.grab_set()

        try:
            dialog.state('zoomed')
        except:
            pass

        main_frame = tk.Frame(dialog, bg='#34495e', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        header_frame = tk.Frame(main_frame, bg='#2c3e50', pady=20)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(header_frame, text="ITEMS NOT RETURNED (ALL ACTIVE RENTALS)",
                 font=('Arial', 22, 'bold'), bg='#2c3e50', fg='white'
                 ).pack()

        tree_frame = tk.Frame(main_frame, bg='#2c3e50', padx=15, pady=10)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("Reference", "Customer Name", "Phone", "Area", "Item", "Quantity", "Date Out",
                   "Time Out", "Days With Customer", "Deposit Paid", "Status", "Overdue Days", "Refund")
        self.not_returned_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)

        col_widths = [80, 150, 120, 150, 120, 80, 100, 80, 120, 100, 100, 100, 80]
        for i, col in enumerate(columns):
            self.not_returned_tree.heading(col, text=col)
            self.not_returned_tree.column(col, width=col_widths[i], anchor="center")

        # Configure tags for different overdue statuses
        self.not_returned_tree.tag_configure('overdue_2', foreground='red', background='#ffe6e6',
                                             font=('Arial', 10, 'bold'))
        self.not_returned_tree.tag_configure('overdue_3', foreground='darkred', background='#ffcccc',
                                             font=('Arial', 10, 'bold'))
        self.not_returned_tree.tag_configure('overdue_4', foreground='maroon', background='#ff9999',
                                             font=('Arial', 10, 'bold'))
        self.not_returned_tree.tag_configure('overdue_5plus', foreground='white', background='#ff3333',
                                             font=('Arial', 10, 'bold'))
        self.not_returned_tree.tag_configure('today', foreground='orange', font=('Arial', 10, 'bold'))
        self.not_returned_tree.tag_configure('normal', foreground='black')
        self.not_returned_tree.tag_configure('refunded', foreground='blue', font=('Arial', 10, 'italic'))

        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.not_returned_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.not_returned_tree.xview)
        self.not_returned_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.not_returned_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        def load_not_returned():
            for item in self.not_returned_tree.get_children():
                self.not_returned_tree.delete(item)

            active_rentals = self.db.get_overdue_rentals()

            if not active_rentals:
                self.not_returned_tree.insert("", "end",
                                              values=("No active rentals", "", "", "", "", "", "", "", "", "", "", "",
                                                      ""))
                return

            for row in active_rentals:
                reference = row[0]
                customer_name = row[1]
                phone = row[2]
                area = row[3]
                item = row[4]
                quantity = row[5]
                date_out = row[6]
                time_out = row[7]
                days_with_customer = row[8] if len(row) > 8 else 0
                deposit_paid = row[9] if len(row) > 9 else 0.0
                overdue = row[10] if len(row) > 10 else 0
                overdue_days = row[11] if len(row) > 11 else 0
                refund_processed = row[12] if len(row) > 12 else 0
                refund_amount = row[13] if len(row) > 13 else 0.0

                status = "Overdue" if overdue == 1 else "Active"
                refund_status = "Yes" if refund_processed == 1 else "No"

                # Determine tag based on overdue status
                tags = ()
                if refund_processed == 1:
                    tags = ('refunded',)
                elif overdue == 1:
                    if overdue_days == 2:
                        tags = ('overdue_2',)
                    elif overdue_days == 3:
                        tags = ('overdue_3',)
                    elif overdue_days == 4:
                        tags = ('overdue_4',)
                    elif overdue_days >= 5:
                        tags = ('overdue_5plus',)
                elif days_with_customer == 0:
                    tags = ('today',)
                else:
                    tags = ('normal',)

                values = (reference, customer_name, phone, area, item, quantity, date_out,
                          time_out, days_with_customer, f"GH₵{deposit_paid:.2f}", status, overdue_days, refund_status)

                self.not_returned_tree.insert("", "end", values=values, tags=tags)

        def send_to_import():
            selected = self.not_returned_tree.selection()
            if not selected:
                messagebox.showerror("Error", "Please select a rental record to import.")
                return

            item_data = self.not_returned_tree.item(selected)['values']
            if item_data[0] == "No active rentals":
                return

            reference = item_data[0]

            try:
                rental_data = self.db.get_complete_rental_data_by_reference(reference)
                if not rental_data:
                    messagebox.showerror("Error", f"No rental data found for reference: {reference}")
                    return

                if rental_data['receipt_printed'] == 1:
                    messagebox.showerror("Error", "❌ Cannot import - receipt already printed!")
                    return

                self.new_rental()

                self.cust_name.delete(0, tk.END)
                self.cust_name.insert(0, rental_data['customer_name'])

                self.cust_phone.delete(0, tk.END)
                if rental_data['phone']:
                    self.cust_phone.insert(0, rental_data['phone'])

                self.cust_id.delete(0, tk.END)
                self.cust_id.insert(0, reference)

                self.deposit.delete(0, tk.END)
                self.deposit.insert(0, f"{rental_data['deposit_paid']:.2f}")

                if rental_data['item'] in self.rates:
                    self.item_type.set(rental_data['item'])

                self.quantity.delete(0, tk.END)
                self.quantity.insert(0, str(rental_data['quantity']))

                if rental_data['rate_type'] in ["daily", "weekly", "monthly"]:
                    self.rate_type.set(rental_data['rate_type'])

                self.start_date.delete(0, tk.END)
                self.start_date.insert(0, rental_data['date'])

                self.start_time.delete(0, tk.END)
                if rental_data['time_out']:
                    self.start_time.insert(0, rental_data['time_out'])
                else:
                    self.start_time.insert(0, "08:00")

                self.end_date.delete(0, tk.END)
                self.end_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

                self.end_time.delete(0, tk.END)
                self.end_time.insert(0, datetime.now().strftime("%H:%M"))

                days_with_customer = rental_data.get('days_with_customer', 1)
                if days_with_customer <= 0:
                    days_with_customer = 1

                item = rental_data['item']
                quantity = rental_data['quantity']
                rate_type = rental_data['rate_type']

                if item in self.rates:
                    daily_rate = self.rates[item][rate_type]
                    total = quantity * daily_rate * days_with_customer

                    self.items_tree.insert("", "end", values=(item, quantity, rate_type,
                                                              f"GH₵{daily_rate:.2f}", f"GH₵{total:.2f}"))

                    self.rental_items.append({
                        "item": item,
                        "quantity": quantity,
                        "rate_type": rate_type,
                        "daily_rate": daily_rate,
                        "total": total
                    })

                    self.period_display.config(text=f"Rental Period: {days_with_customer} days")

                    self.auto_calculate_total()

                    messagebox.showinfo("Success",
                                        f"✅ ALL Data imported successfully!\n\n"
                                        f"Reference: {reference}\n"
                                        f"Customer: {rental_data['customer_name']}\n"
                                        f"Item: {item} x {quantity}\n"
                                        f"Rate Type: {rate_type}\n"
                                        f"Deposit: GH₵{rental_data['deposit_paid']:.2f}\n"
                                        f"Days: {days_with_customer}\n\n"
                                        f"Ready to print receipt!")

                    self.log_activity(f"TO IMPORT: Loaded ALL data for reference: {reference}")

                    dialog.destroy()

                    self.master.focus_set()

                else:
                    messagebox.showerror("Error", f"Item '{item}' not found in rates database.")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to import data: {str(e)}")
                print(f"Import error: {traceback.format_exc()}")

        def mark_as_return():
            selected = self.not_returned_tree.selection()
            if not selected:
                messagebox.showerror("Error", "Please select a rental record to mark as returned.")
                return

            item_data = self.not_returned_tree.item(selected)['values']
            if item_data[0] == "No active rentals":
                return

            reference = item_data[0]
            customer_name = item_data[1]
            phone = item_data[2]
            item = item_data[4]

            if not messagebox.askyesno("Confirm Return",
                                       f"Mark this item as returned?\n\n"
                                       f"Reference: {reference}\n"
                                       f"Customer: {customer_name}\n"
                                       f"Item: {item}\n\n"
                                       f"Are you sure you?"):
                return

            success, message = self.db.mark_item_as_returned(reference, customer_name, phone, item)

            if success:
                messagebox.showinfo("Success", f" Item marked as returned!\n\n{message}")
                load_not_returned()
                self.log_activity(f"Marked item as returned: {item} for {customer_name} (Ref: {reference})")
            else:
                messagebox.showerror("Error", f"Failed to mark item as returned:\n{message}")

        def process_refund():
            """Process refund for selected rental."""
            selected = self.not_returned_tree.selection()
            if not selected:
                messagebox.showerror("Error", "Please select a rental record to process refund.")
                return

            item_data = self.not_returned_tree.item(selected)['values']
            if item_data[0] == "No active rentals":
                return

            reference = item_data[0]
            customer_name = item_data[1]
            deposit_paid_text = item_data[9].replace("GH₵", "").replace(",", "").strip()

            try:
                deposit_paid = float(deposit_paid_text)
            except ValueError:
                deposit_paid = 0.0

            # Check if already refunded
            refund_status = item_data[12]
            if refund_status == "Yes":
                messagebox.showerror("Error", "Refund has already been processed for this item.")
                return

            # Open refund dialog
            refund_dialog = tk.Toplevel(dialog)
            refund_dialog.title(f"Process Refund - {reference}")
            refund_dialog.geometry("500x450")
            refund_dialog.configure(bg='#2c3e50')
            refund_dialog.grab_set()
            refund_dialog.resizable(False, False)

            main_frame = tk.Frame(refund_dialog, bg='#2c3e50', padx=20, pady=20)
            main_frame.pack(fill=tk.BOTH, expand=True)

            tk.Label(main_frame, text=f"PROCESS REFUND",
                     font=('Arial', 16, 'bold'), bg='#2c3e50', fg='white'
                     ).pack(pady=(0, 10))

            tk.Label(main_frame, text=f"Customer: {customer_name}",
                     font=('Arial', 12), bg='#2c3e50', fg='#f39c12'
                     ).pack(pady=(0, 5))

            tk.Label(main_frame, text=f"Reference: {reference}",
                     font=('Arial', 12), bg='#2c3e50', fg='#f39c12'
                     ).pack(pady=(0, 20))

            tk.Label(main_frame, text=f"Deposit Paid: GH₵{deposit_paid:,.2f}",
                     font=('Arial', 12, 'bold'), bg='#2c3e50', fg='#27ae60'
                     ).pack(pady=(0, 20))

            form_frame = tk.Frame(main_frame, bg='white', padx=20, pady=20)
            form_frame.pack(fill=tk.BOTH, expand=True)

            tk.Label(form_frame, text="Refund Amount (GH₵) ",
                     bg='white', font=('Arial', 11)).pack(anchor='w', pady=(0, 5))
            refund_amount_var = tk.StringVar()
            refund_amount_entry = tk.Entry(form_frame, textvariable=refund_amount_var,
                                           width=20, font=('Arial', 11), bd=2, relief='solid')
            refund_amount_entry.pack(pady=(0, 15))
            refund_amount_entry.focus_set()

            tk.Label(form_frame, text="Reason for Refund Required",
                     bg='white', font=('Arial', 11)).pack(anchor='w', pady=(0, 5))
            reason_var = tk.StringVar()
            reason_combo = ttk.Combobox(form_frame, textvariable=reason_var,
                                        values=["Item not used", "Early return", "Customer cancellation",
                                                "Damage waiver", "Other"], width=20, font=('Arial', 11))
            reason_combo.pack(pady=(0, 15))
            reason_combo.current(0)

            def submit_refund():
                refund_amount_str = refund_amount_var.get().strip()
                reason = reason_var.get().strip()

                if not refund_amount_str or not reason:
                    messagebox.showerror("Error", "Please fill in all required fields.")
                    return

                try:
                    refund_amount = float(refund_amount_str)

                    if refund_amount < 0:
                        messagebox.showerror("Error", "Refund amount cannot be negative.")
                        return

                    confirm_msg = f"Process refund of GH₵{refund_amount:,.2f}?\n\n"
                    confirm_msg += f"Customer: {customer_name}\n"
                    confirm_msg += f"Reference: {reference}\n"
                    confirm_msg += f"Current Deposit: GH₵{deposit_paid:,.2f}\n"
                    confirm_msg += f"Refund Amount: GH₵{refund_amount:,.2f}\n"
                    confirm_msg += f"Reason: {reason}\n"

                    if deposit_paid == 0 and refund_amount > 0:
                        confirm_msg += "\n⚠️ NOTE: Customer has zero deposit balance.\n"
                        confirm_msg += "Refund will be paid from company funds."
                    elif refund_amount == 0:
                        confirm_msg += "\n⚠️ NOTE: This is an administrative refund record.\n"
                        confirm_msg += "No money will be transferred."

                    if not messagebox.askyesno("Confirm Refund", confirm_msg):
                        return

                    success, message = self.db.process_refund(reference, customer_name, deposit_paid,
                                                              refund_amount, reason, self.user_info['user_id'])

                    if success:
                        messagebox.showinfo("Success",
                                            f"✅ Refund processed successfully!\n\n"
                                            f"Customer: {customer_name}\n"
                                            f"Amount: GH₵{refund_amount:,.2f}\n"
                                            f"Reason: {reason}")

                        self.log_activity(f"Processed refund for {customer_name}: GH₵{refund_amount:.2f}")

                        refund_dialog.destroy()
                        load_not_returned()
                    else:
                        messagebox.showerror("Error", message)

                except ValueError:
                    messagebox.showerror("Error", "Please enter a valid number for refund amount.")

            button_frame = tk.Frame(main_frame, bg='#2c3e50')
            button_frame.pack(fill=tk.X, pady=(10, 0))

            refund_btn = tk.Button(button_frame, text="APPROVE REFUND", command=submit_refund,
                                   bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
                                   width=15, height=2, relief='raised', bd=2)
            refund_btn.pack(side=tk.LEFT, padx=(0, 10))

            cancel_btn = tk.Button(button_frame, text="CANCEL", command=refund_dialog.destroy,
                                   bg='#e74c3c', fg='white', font=('Arial', 11, 'bold'),
                                   width=15, height=2, relief='raised', bd=2)
            cancel_btn.pack(side=tk.RIGHT)

            refund_dialog.bind('<Return>', lambda e: submit_refund())

        bottom_button_frame = tk.Frame(main_frame, bg='#2c3e50', pady=15)
        bottom_button_frame.pack(fill=tk.X, pady=(10, 0))

        left_buttons_frame = tk.Frame(bottom_button_frame, bg='#2c3e50')
        left_buttons_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        load_btn = tk.Button(left_buttons_frame, text="⟳ Refresh List", command=load_not_returned,
                             bg='#3498db', fg='white', font=('Arial', 12, 'bold'),
                             width=20, height=2, relief='raised', bd=2)
        load_btn.pack(side=tk.LEFT, padx=5)

        right_buttons_frame = tk.Frame(bottom_button_frame, bg='#2c3e50')
        right_buttons_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # Add refund button
        refund_btn = tk.Button(
            right_buttons_frame,
            text="💰 Return & Refund ",
            command=process_refund,
            bg='#f39c12',
            fg='white',
            font=('Arial', 12, 'bold'),
            width=20,
            height=2,
            relief='raised',
            bd=2
        )
        refund_btn.pack(side=tk.RIGHT, padx=10)

        mark_return_btn = tk.Button(
            right_buttons_frame,
            text="✓ Mark as Returned",
            command=mark_as_return,
            bg='#27ae60',
            fg='white',
            font=('Arial', 12, 'bold'),
            width=20,
            height=2,
            relief='raised',
            bd=2
        )
        mark_return_btn.pack(side=tk.RIGHT, padx=10)

        to_import_btn = tk.Button(
            right_buttons_frame,
            text="📋 Send to Import",
            command=send_to_import,
            bg='#1abc9c',
            fg='white',
            font=('Arial', 12, 'bold'),
            width=20,
            height=2,
            relief='raised',
            bd=2
        )
        to_import_btn.pack(side=tk.RIGHT, padx=10)

        close_btn = tk.Button(right_buttons_frame, text="✗ Close", command=dialog.destroy,
                              bg='#e74c3c', fg='white', font=('Arial', 12, 'bold'),
                              width=15, height=2, relief='raised', bd=2)
        close_btn.pack(side=tk.RIGHT, padx=5)

        load_not_returned()

    def show_active_summary_fullscreen(self):
        dialog = tk.Toplevel(self.master)
        dialog.title("Active Rentals Summary ")
        dialog.configure(bg='#34495e')
        dialog.grab_set()

        try:
            dialog.state('zoomed')
        except:
            dialog.geometry(f"{self.master.winfo_screenwidth()}x{self.master.winfo_screenheight()}")

        main_frame = tk.Frame(dialog, bg='#34495e', padx=30, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="ACTIVE RENTALS SUMMARY ",
                 font=('Arial', 28, 'bold'), bg='#34495e', fg='white'
                 ).pack(pady=(0, 30))

        summary_frame = tk.Frame(main_frame, bg='#2c3e50', padx=40, pady=40)
        summary_frame.pack(fill=tk.BOTH, expand=True)

        def refresh_summary():
            total_active, total_items, total_deposits, total_refunds = self.db.get_active_rentals_summary()

            if total_deposits is None:
                total_deposits = 0.0
            else:
                try:
                    total_deposits = float(total_deposits)
                except (ValueError, TypeError):
                    total_deposits = 0.0

            if total_refunds is None:
                total_refunds = 0.0
            else:
                try:
                    total_refunds = float(total_refunds)
                except (ValueError, TypeError):
                    total_refunds = 0.0

            for widget in summary_frame.winfo_children():
                widget.destroy()

            for i in range(4):
                summary_frame.grid_rowconfigure(i, weight=1)
            summary_frame.grid_columnconfigure(0, weight=1)
            summary_frame.grid_columnconfigure(1, weight=2)

            tk.Label(summary_frame, text="Total Active Rentals",
                     font=('Arial', 24), bg='#2c3e50', fg='white'
                     ).grid(row=0, column=0, sticky='w', pady=40, padx=40)
            tk.Label(summary_frame, text=str(total_active),
                     font=('Arial', 36, 'bold'), bg='#2c3e50', fg='#3498db'
                     ).grid(row=0, column=1, sticky='w', pady=40, padx=40)

            tk.Label(summary_frame, text="Total Items Currently Rented",
                     font=('Arial', 24), bg='#2c3e50', fg='white'
                     ).grid(row=1, column=0, sticky='w', pady=40, padx=40)
            tk.Label(summary_frame, text=str(total_items),
                     font=('Arial', 36, 'bold'), bg='#2c3e50', fg='#27ae60'
                     ).grid(row=1, column=1, sticky='w', pady=40, padx=40)

            tk.Label(summary_frame, text="Total Deposits Held",
                     font=('Arial', 24), bg='#2c3e50', fg='white'
                     ).grid(row=2, column=0, sticky='w', pady=40, padx=40)
            tk.Label(summary_frame, text=f"GH₵{total_deposits:,.2f}",
                     font=('Arial', 36, 'bold'), bg='#2c3e50', fg='#f39c12'
                     ).grid(row=2, column=1, sticky='w', pady=40, padx=40)

            tk.Label(summary_frame, text="Total Refunds Processed",
                     font=('Arial', 24), bg='#2c3e50', fg='white'
                     ).grid(row=3, column=0, sticky='w', pady=40, padx=40)
            tk.Label(summary_frame, text=f"GH₵{total_refunds:,.2f}",
                     font=('Arial', 36, 'bold'), bg='#2c3e50', fg='#ff6b6b'
                     ).grid(row=3, column=1, sticky='w', pady=40, padx=40)

        refresh_summary()

        close_btn = tk.Button(main_frame, text="CLOSE", command=dialog.destroy,
                              bg='#e74c3c', fg='white', font=('Arial', 14, 'bold'),
                              width=15, height=2, relief='raised', bd=2)
        close_btn.pack(pady=(20, 0))

    def logout(self):
        """Logout staff and return to login."""
        self.session_running = False
        self.log_activity("Logged out")
        self.master.destroy()
        self.logout_callback()


class MainApplication:
    """Main application controller."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()

        login_root = tk.Toplevel(self.root)
        self.login_screen = LoginScreen(login_root, self.launch_main_app)

        self.root.mainloop()

    def launch_main_app(self, user_info: Dict, window: tk.Toplevel):
        """Launch appropriate application based on user type."""
        if user_info['user_type'] == 'admin':
            AdminDashboard(window, user_info, self.return_to_login)
        else:
            StaffRentalSystem(window, user_info, self.return_to_login)

    def return_to_login(self):
        """Return to login screen."""
        for widget in self.root.winfo_children():
            widget.destroy()

        login_root = tk.Toplevel(self.root)
        self.login_screen = LoginScreen(login_root, self.launch_main_app)


if __name__ == "__main__":
    app = MainApplication()

