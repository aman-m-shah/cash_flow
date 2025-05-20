import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
import streamlit as st
from datetime import datetime, timedelta
from google.colab import drive

def setup_database():
    """
    Mount Google Drive and set up the SQLite database.
    Returns the database connection and cursor.
    """
    # Mount Google Drive
    drive.mount('/content/drive')

    # Define database path
    db_path = '/content/drive/MyDrive/finance_tracker.db'

    # Connect to SQLite database (will create it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create necessary tables if they don't exist
    create_tables(cursor)

    # Commit changes and return connection
    conn.commit()
    return conn, cursor

def create_tables(cursor):
    """Create all necessary tables for the finance tracker if they don't exist."""

    # Bank accounts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bank_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_name TEXT NOT NULL,
        current_balance REAL NOT NULL,
        last_updated DATE NOT NULL
    )
    ''')

    # Credit cards table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS credit_cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        card_name TEXT NOT NULL,
        current_balance REAL NOT NULL,
        statement_balance REAL NOT NULL,
        apr REAL NOT NULL,
        credit_limit REAL NOT NULL,
        due_date DATE NOT NULL,
        last_updated DATE NOT NULL
    )
    ''')

    # Recurring transactions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS recurring_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        transaction_type TEXT NOT NULL,  -- 'income' or 'expense'
        frequency TEXT NOT NULL,         -- 'weekly', 'biweekly', 'monthly', etc.
        day_of_month INTEGER,           -- for monthly transactions
        day_of_week INTEGER,            -- for weekly transactions
        start_date DATE NOT NULL,
        end_date DATE,                  -- NULL if ongoing
        account_id INTEGER,             -- can be NULL if not associated with specific account
        category TEXT NOT NULL
    )
    ''')

    # Actual transactions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS actual_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        transaction_type TEXT NOT NULL,  -- 'income' or 'expense'
        date DATE NOT NULL,
        account_id INTEGER,              -- can be NULL
        category TEXT NOT NULL,
        is_reconciled BOOLEAN DEFAULT 0
    )
    ''')

def main():
    st.title("Personal Finance Tracker")
    st.write("Welcome to your personal finance tracker. This tool helps you manage your cash flow and track credit card payoffs.")

    # Setup database connection
    conn, cursor = setup_database()

    # Add sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Home", "Bank Accounts", "Credit Cards", "Recurring Transactions", "Reports"])

    # Close connection when app is done
    conn.close()

if __name__ == "__main__":
    main()



def bank_accounts_page(conn, cursor):
    """
    Handle the bank accounts page functionality.
    """
    st.header("Bank Accounts Management")

    # Create tabs for viewing vs adding/editing
    tab1, tab2 = st.tabs(["View Accounts", "Add/Edit Account"])

    with tab1:
        display_bank_accounts(conn, cursor)

    with tab2:
        manage_bank_accounts(conn, cursor)

def display_bank_accounts(conn, cursor):
    """
    Display all bank accounts and their current balances.
    """
    st.subheader("Current Bank Accounts")

    # Query all bank accounts
    cursor.execute("SELECT id, account_name, current_balance, last_updated FROM bank_accounts")
    accounts = cursor.fetchall()

    if not accounts:
        st.info("No bank accounts have been added yet. Use the 'Add/Edit Account' tab to add your first account.")
        return

    # Convert to DataFrame for easier display
    accounts_df = pd.DataFrame(accounts, columns=["ID", "Account Name", "Current Balance", "Last Updated"])

    # Format the dataframe
    formatted_df = accounts_df.copy()
    formatted_df["Current Balance"] = formatted_df["Current Balance"].apply(lambda x: f"${x:,.2f}")

    # Calculate total balance
    total_balance = accounts_df["Current Balance"].sum()

    # Display accounts table
    st.dataframe(formatted_df.drop("ID", axis=1), use_container_width=True)

    # Display total balance
    st.metric("Total Bank Balance", f"${total_balance:,.2f}")

    # Option to delete an account
    st.subheader("Delete Account")
    account_to_delete = st.selectbox(
        "Select account to delete:",
        options=accounts_df["Account Name"].tolist(),
        key="delete_account"
    )

    if st.button("Delete Selected Account"):
        account_id = accounts_df.loc[accounts_df["Account Name"] == account_to_delete, "ID"].iloc[0]
        cursor.execute("DELETE FROM bank_accounts WHERE id = ?", (account_id,))
        conn.commit()
        st.success(f"Account '{account_to_delete}' has been deleted.")
        st.experimental_rerun()

def manage_bank_accounts(conn, cursor):
    """
    Add new bank accounts or update existing ones.
    """
    st.subheader("Add/Edit Bank Account")

    # Get existing account names for the dropdown
    cursor.execute("SELECT id, account_name FROM bank_accounts")
    existing_accounts = cursor.fetchall()
    existing_account_names = ["-- New Account --"] + [acc[1] for acc in existing_accounts]

    # Select account to edit or create new one
    selected_account = st.selectbox(
        "Select account to edit or create new:",
        options=existing_account_names,
        key="select_account"
    )

    # Initialize form values
    account_name = ""
    current_balance = 0.0
    account_id = None

    # If editing existing account, populate fields
    if selected_account != "-- New Account --":
        account_id = next((acc[0] for acc in existing_accounts if acc[1] == selected_account), None)
        cursor.execute("SELECT account_name, current_balance FROM bank_accounts WHERE id = ?", (account_id,))
        account_data = cursor.fetchone()
        if account_data:
            account_name = account_data[0]
            current_balance = account_data[1]

    # Form for account details
    with st.form("bank_account_form"):
        new_account_name = st.text_input("Account Name", value=account_name)
        new_balance = st.number_input("Current Balance ($)", value=float(current_balance), step=100.0)

        submitted = st.form_submit_button("Save Account")

        if submitted:
            if not new_account_name:
                st.error("Account name cannot be empty.")
                return

            current_date = datetime.now().strftime("%Y-%m-%d")

            if account_id:  # Update existing account
                cursor.execute(
                    "UPDATE bank_accounts SET account_name = ?, current_balance = ?, last_updated = ? WHERE id = ?",
                    (new_account_name, new_balance, current_date, account_id)
                )
                message = f"Account '{new_account_name}' has been updated."
            else:  # Add new account
                cursor.execute(
                    "INSERT INTO bank_accounts (account_name, current_balance, last_updated) VALUES (?, ?, ?)",
                    (new_account_name, new_balance, current_date)
                )
                message = f"New account '{new_account_name}' has been added."

            conn.commit()
            st.success(message)
            st.experimental_rerun()

# Update the main function to include the bank accounts page
def main():
    st.title("Personal Finance Tracker")
    st.write("Welcome to your personal finance tracker. This tool helps you manage your cash flow and track credit card payoffs.")

    # Setup database connection
    conn, cursor = setup_database()

    # Add sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Home", "Bank Accounts", "Credit Cards", "Recurring Transactions", "Reports"])

    # Display the selected page
    if page == "Home":
        st.write("Please select a section from the sidebar to get started.")
    elif page == "Bank Accounts":
        bank_accounts_page(conn, cursor)
    # We'll implement the other pages in subsequent modules

    # Close connection when app is done
    conn.close()

if __name__ == "__main__":
    main()
