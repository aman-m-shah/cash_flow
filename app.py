# app.py - Main Streamlit application file
import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np

# Set page configuration
st.set_page_config(
    page_title="Cash Flow & Credit Card Management",
    page_icon="💰",
    layout="wide"
)

# Database setup
def init_db():
    """Initialize the SQLite database if it doesn't exist"""
    # Check if database file exists
    if not os.path.exists('finance_data.db'):
        conn = sqlite3.connect('finance_data.db')
        c = conn.cursor()

        # Create bank_accounts table
        c.execute('''
            CREATE TABLE IF NOT EXISTS bank_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                balance REAL NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create credit_cards table
        c.execute('''
            CREATE TABLE IF NOT EXISTS credit_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                current_balance REAL NOT NULL,
                statement_balance REAL NOT NULL,
                interest_rate REAL NOT NULL,
                due_date DATE NOT NULL,
                credit_limit REAL NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create recurring_transactions table
        c.execute('''
            CREATE TABLE IF NOT EXISTS recurring_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                frequency TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE,
                category TEXT NOT NULL,
                type TEXT NOT NULL,
                account_id INTEGER,
                credit_card_id INTEGER,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (account_id) REFERENCES bank_accounts (id),
                FOREIGN KEY (credit_card_id) REFERENCES credit_cards (id)
            )
        ''')

        # Create actual_transactions table to track actual spending
        c.execute('''
            CREATE TABLE IF NOT EXISTS actual_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                date DATE NOT NULL,
                category TEXT NOT NULL,
                type TEXT NOT NULL,
                account_id INTEGER,
                credit_card_id INTEGER,
                FOREIGN KEY (account_id) REFERENCES bank_accounts (id),
                FOREIGN KEY (credit_card_id) REFERENCES credit_cards (id)
            )
        ''')

        conn.commit()
        conn.close()
        st.success("Database initialized successfully!")
    else:
        # Database already exists
        conn = sqlite3.connect('finance_data.db')
        conn.close()

# Initialize database
init_db()

# Connection function to reuse
def get_db_connection():
    """Get a database connection"""
    conn = sqlite3.connect('finance_data.db')
    conn.row_factory = sqlite3.Row
    return conn

# Main application with sidebar navigation
def main():
    st.title("💰 Cash Flow & Credit Card Management")

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Dashboard", "Bank Accounts", "Credit Cards", "Recurring Transactions", "Actual Transactions", "Visualization"]
    )

    # Page routing
    if page == "Dashboard":
        show_dashboard()
    elif page == "Bank Accounts":
        manage_bank_accounts()
    elif page == "Credit Cards":
        manage_credit_cards()
    elif page == "Recurring Transactions":
        manage_recurring_transactions()
    elif page == "Actual Transactions":
        manage_actual_transactions()
    elif page == "Visualization":
        show_visualizations()

# Dashboard placeholder
def show_dashboard():
    st.header("Dashboard")
    st.write("This is your financial overview. More detailed features coming soon.")

    # Placeholders for other pages - we'll implement these in subsequent modules

if __name__ == "__main__":
    main()

# Add this function to your app.py file

def manage_bank_accounts():
    st.header("Manage Bank Accounts")

    # Create tabs for different operations
    tabs = st.tabs(["View Accounts", "Add Account", "Update Account", "Delete Account"])

    # Tab 1: View Accounts
    with tabs[0]:
        st.subheader("Current Bank Accounts")

        # Get bank accounts data
        conn = get_db_connection()
        accounts_df = pd.read_sql_query("SELECT * FROM bank_accounts ORDER BY name", conn)
        conn.close()

        if not accounts_df.empty:
            # Format the last_updated column
            accounts_df['last_updated'] = pd.to_datetime(accounts_df['last_updated']).dt.strftime('%Y-%m-%d %H:%M')

            # Calculate total balance
            total_balance = accounts_df['balance'].sum()

            # Display accounts in a dataframe
            st.dataframe(
                accounts_df[['id', 'name', 'balance', 'last_updated']],
                column_config={
                    "id": "ID",
                    "name": "Account Name",
                    "balance": st.column_config.NumberColumn(
                        "Balance",
                        format="$%.2f",
                    ),
                    "last_updated": "Last Updated"
                },
                hide_index=True
            )

            # Display total balance
            st.metric("Total Bank Balance", f"${total_balance:.2f}")
        else:
            st.info("No bank accounts found. Add an account to get started.")

    # Tab 2: Add Account
    with tabs[1]:
        st.subheader("Add New Bank Account")

        with st.form("add_account_form"):
            account_name = st.text_input("Account Name", placeholder="e.g., Chase Checking")
            account_balance = st.number_input("Current Balance", min_value=0.0, format="%.2f", step=100.0)
            submit_button = st.form_submit_button("Add Account")

            if submit_button:
                if account_name:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO bank_accounts (name, balance) VALUES (?, ?)",
                            (account_name, account_balance)
                        )
                        conn.commit()
                        conn.close()
                        st.success(f"Account '{account_name}' successfully added!")
                        # Clear the form
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding account: {e}")
                else:
                    st.warning("Please enter an account name.")

    # Tab 3: Update Account
    with tabs[2]:
        st.subheader("Update Bank Account")

        # Get bank accounts for selection
        conn = get_db_connection()
        accounts = conn.execute("SELECT id, name, balance FROM bank_accounts ORDER BY name").fetchall()
        conn.close()

        if accounts:
            account_options = {account['name']: account['id'] for account in accounts}
            account_balances = {account['id']: account['balance'] for account in accounts}

            selected_account_name = st.selectbox("Select Account to Update", options=list(account_options.keys()))
            selected_account_id = account_options[selected_account_name]

            with st.form("update_account_form"):
                updated_name = st.text_input("Account Name", value=selected_account_name)
                updated_balance = st.number_input(
                    "Current Balance",
                    value=float(account_balances[selected_account_id]),
                    format="%.2f",
                    step=100.0
                )
                update_button = st.form_submit_button("Update Account")

                if update_button:
                    if updated_name:
                        try:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute(
                                """UPDATE bank_accounts
                                SET name = ?, balance = ?, last_updated = CURRENT_TIMESTAMP
                                WHERE id = ?""",
                                (updated_name, updated_balance, selected_account_id)
                            )
                            conn.commit()
                            conn.close()
                            st.success(f"Account '{updated_name}' successfully updated!")
                            # Refresh the page to show updated data
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating account: {e}")
                    else:
                        st.warning("Account name cannot be empty.")
        else:
            st.info("No accounts available to update. Please add an account first.")

    # Tab 4: Delete Account
    with tabs[3]:
        st.subheader("Delete Bank Account")
        st.warning("⚠️ Deleting an account will remove all associated data. This action cannot be undone.")

        # Get bank accounts for selection
        conn = get_db_connection()
        accounts = conn.execute("SELECT id, name FROM bank_accounts ORDER BY name").fetchall()
        conn.close()

        if accounts:
            account_options = {account['name']: account['id'] for account in accounts}

            selected_account_name = st.selectbox("Select Account to Delete", options=list(account_options.keys()))
            selected_account_id = account_options[selected_account_name]

            if st.button("Delete Account", type="primary", use_container_width=True):
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()

                    # Check if account has linked transactions
                    recurring_count = cursor.execute(
                        "SELECT COUNT(*) FROM recurring_transactions WHERE account_id = ?",
                        (selected_account_id,)
                    ).fetchone()[0]

                    actual_count = cursor.execute(
                        "SELECT COUNT(*) FROM actual_transactions WHERE account_id = ?",
                        (selected_account_id,)
                    ).fetchone()[0]

                    if recurring_count > 0 or actual_count > 0:
                        st.error(f"Cannot delete account '{selected_account_name}' because it has linked transactions. Please remove those transactions first.")
                    else:
                        cursor.execute("DELETE FROM bank_accounts WHERE id = ?", (selected_account_id,))
                        conn.commit()
                        st.success(f"Account '{selected_account_name}' successfully deleted!")
                        # Refresh the page to show updated data
                        st.rerun()

                    conn.close()
                except Exception as e:
                    st.error(f"Error deleting account: {e}")
        else:
            st.info("No accounts available to delete.")

# Add this function to your app.py file

def manage_credit_cards():
    st.header("Manage Credit Cards")

    # Create tabs for different operations
    tabs = st.tabs(["View Credit Cards", "Add Credit Card", "Update Credit Card", "Delete Credit Card"])

    # Tab 1: View Credit Cards
    with tabs[0]:
        st.subheader("Current Credit Cards")

        # Get credit cards data
        conn = get_db_connection()
        cards_df = pd.read_sql_query("SELECT * FROM credit_cards ORDER BY name", conn)
        conn.close()

        if not cards_df.empty:
            # Format the dates and timestamps
            cards_df['last_updated'] = pd.to_datetime(cards_df['last_updated']).dt.strftime('%Y-%m-%d %H:%M')
            cards_df['due_date'] = pd.to_datetime(cards_df['due_date']).dt.strftime('%Y-%m-%d')

            # Calculate utilization percentage
            cards_df['utilization'] = (cards_df['current_balance'] / cards_df['credit_limit']) * 100

            # Calculate total balances
            total_current_balance = cards_df['current_balance'].sum()
            total_statement_balance = cards_df['statement_balance'].sum()

            # Display cards in a dataframe
            st.dataframe(
                cards_df[['id', 'name', 'current_balance', 'statement_balance', 'interest_rate', 'due_date', 'credit_limit', 'utilization']],
                column_config={
                    "id": "ID",
                    "name": "Card Name",
                    "current_balance": st.column_config.NumberColumn(
                        "Current Balance",
                        format="$%.2f",
                    ),
                    "statement_balance": st.column_config.NumberColumn(
                        "Statement Balance",
                        format="$%.2f",
                    ),
                    "interest_rate": st.column_config.NumberColumn(
                        "Interest Rate",
                        format="%.2f%%",
                    ),
                    "due_date": "Due Date",
                    "credit_limit": st.column_config.NumberColumn(
                        "Credit Limit",
                        format="$%.2f",
                    ),
                    "utilization": st.column_config.ProgressColumn(
                        "Utilization",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100,
                    ),
                },
                hide_index=True
            )

            # Display total balances
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Current Balance", f"${total_current_balance:.2f}")
            with col2:
                st.metric("Total Statement Balance", f"${total_statement_balance:.2f}")

            # Show cards approaching due date
            today = datetime.now().date()
            upcoming_due = cards_df[pd.to_datetime(cards_df['due_date']).dt.date.between(today, today + timedelta(days=7))]

            if not upcoming_due.empty:
                st.warning("### Payment Due Soon")
                for _, card in upcoming_due.iterrows():
                    st.info(f"🔔 {card['name']} payment of ${card['statement_balance']:.2f} due on {card['due_date']}")
        else:
            st.info("No credit cards found. Add a card to get started.")

    # Tab 2: Add Credit Card
    with tabs[1]:
        st.subheader("Add New Credit Card")

        with st.form("add_card_form"):
            card_name = st.text_input("Card Name", placeholder="e.g., Chase Sapphire Preferred")

            col1, col2 = st.columns(2)
            with col1:
                current_balance = st.number_input("Current Balance", min_value=0.0, format="%.2f", step=100.0)
            with col2:
                statement_balance = st.number_input("Statement Balance", min_value=0.0, format="%.2f", step=100.0)

            col1, col2 = st.columns(2)
            with col1:
                interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, max_value=50.0, format="%.2f", step=0.25)
            with col2:
                credit_limit = st.number_input("Credit Limit", min_value=0.0, format="%.2f", step=1000.0)

            due_date = st.date_input("Payment Due Date", value=datetime.now().date() + timedelta(days=15))

            submit_button = st.form_submit_button("Add Credit Card")

            if submit_button:
                if card_name:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            """INSERT INTO credit_cards
                            (name, current_balance, statement_balance, interest_rate, due_date, credit_limit)
                            VALUES (?, ?, ?, ?, ?, ?)""",
                            (card_name, current_balance, statement_balance, interest_rate, due_date, credit_limit)
                        )
                        conn.commit()
                        conn.close()
                        st.success(f"Credit card '{card_name}' successfully added!")
                        # Clear the form
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding credit card: {e}")
                else:
                    st.warning("Please enter a card name.")

    # Tab 3: Update Credit Card
    with tabs[2]:
        st.subheader("Update Credit Card")

        # Get credit cards for selection
        conn = get_db_connection()
        cards = conn.execute("SELECT * FROM credit_cards ORDER BY name").fetchall()
        conn.close()

        if cards:
            card_options = {card['name']: card['id'] for card in cards}
            card_data = {card['id']: {
                'name': card['name'],
                'current_balance': card['current_balance'],
                'statement_balance': card['statement_balance'],
                'interest_rate': card['interest_rate'],
                'due_date': card['due_date'],
                'credit_limit': card['credit_limit']
            } for card in cards}

            selected_card_name = st.selectbox("Select Credit Card to Update", options=list(card_options.keys()))
            selected_card_id = card_options[selected_card_name]
            selected_card = card_data[selected_card_id]

            with st.form("update_card_form"):
                updated_name = st.text_input("Card Name", value=selected_card['name'])

                col1, col2 = st.columns(2)
                with col1:
                    updated_current_balance = st.number_input(
                        "Current Balance",
                        value=float(selected_card['current_balance']),
                        format="%.2f",
                        step=100.0
                    )
                with col2:
                    updated_statement_balance = st.number_input(
                        "Statement Balance",
                        value=float(selected_card['statement_balance']),
                        format="%.2f",
                        step=100.0
                    )

                col1, col2 = st.columns(2)
                with col1:
                    updated_interest_rate = st.number_input(
                        "Interest Rate (%)",
                        value=float(selected_card['interest_rate']),
                        min_value=0.0,
                        max_value=50.0,
                        format="%.2f",
                        step=0.25
                    )
                with col2:
                    updated_credit_limit = st.number_input(
                        "Credit Limit",
                        value=float(selected_card['credit_limit']),
                        format="%.2f",
                        step=1000.0
                    )

                # Parse the date string from the database
                due_date_value = datetime.strptime(selected_card['due_date'], '%Y-%m-%d').date() if isinstance(selected_card['due_date'], str) else selected_card['due_date']
                updated_due_date = st.date_input("Payment Due Date", value=due_date_value)

                update_button = st.form_submit_button("Update Credit Card")

                if update_button:
                    if updated_name:
                        try:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute(
                                """UPDATE credit_cards
                                SET name = ?, current_balance = ?, statement_balance = ?,
                                interest_rate = ?, due_date = ?, credit_limit = ?, last_updated = CURRENT_TIMESTAMP
                                WHERE id = ?""",
                                (updated_name, updated_current_balance, updated_statement_balance,
                                 updated_interest_rate, updated_due_date, updated_credit_limit, selected_card_id)
                            )
                            conn.commit()
                            conn.close()
                            st.success(f"Credit card '{updated_name}' successfully updated!")
                            # Refresh the page to show updated data
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating credit card: {e}")
                    else:
                        st.warning("Card name cannot be empty.")
        else:
            st.info("No credit cards available to update. Please add a credit card first.")

    # Tab 4: Delete Credit Card
    with tabs[3]:
        st.subheader("Delete Credit Card")
        st.warning("⚠️ Deleting a credit card will remove all associated data. This action cannot be undone.")

        # Get credit cards for selection
        conn = get_db_connection()
        cards = conn.execute("SELECT id, name FROM credit_cards ORDER BY name").fetchall()
        conn.close()

        if cards:
            card_options = {card['name']: card['id'] for card in cards}

            selected_card_name = st.selectbox("Select Credit Card to Delete", options=list(card_options.keys()))
            selected_card_id = card_options[selected_card_name]

            if st.button("Delete Credit Card", type="primary", use_container_width=True):
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()

                    # Check if card has linked transactions
                    recurring_count = cursor.execute(
                        "SELECT COUNT(*) FROM recurring_transactions WHERE credit_card_id = ?",
                        (selected_card_id,)
                    ).fetchone()[0]

                    actual_count = cursor.execute(
                        "SELECT COUNT(*) FROM actual_transactions WHERE credit_card_id = ?",
                        (selected_card_id,)
                    ).fetchone()[0]

                    if recurring_count > 0 or actual_count > 0:
                        st.error(f"Cannot delete credit card '{selected_card_name}' because it has linked transactions. Please remove those transactions first.")
                    else:
                        cursor.execute("DELETE FROM credit_cards WHERE id = ?", (selected_card_id,))
                        conn.commit()
                        st.success(f"Credit card '{selected_card_name}' successfully deleted!")
                        # Refresh the page to show updated data
                        st.rerun()

                    conn.close()
                except Exception as e:
                    st.error(f"Error deleting credit card: {e}")
        else:
            st.info("No credit cards available to delete.")

# Add this function to your app.py file

def manage_recurring_transactions():
    st.header("Manage Recurring Transactions")

    # Create tabs for different operations
    tabs = st.tabs(["View Transactions", "Add Transaction", "Update Transaction", "Delete Transaction"])

    # Tab 1: View Transactions
    with tabs[0]:
        st.subheader("Current Recurring Transactions")

        # Get filter options
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            show_inactive = st.checkbox("Show Inactive Transactions", value=False)
        with filter_col2:
            transaction_type = st.selectbox("Filter by Type", ["All", "Income", "Expense"])

        # Prepare SQL query based on filters
        query = "SELECT r.*, ba.name as account_name, cc.name as card_name FROM recurring_transactions r "
        query += "LEFT JOIN bank_accounts ba ON r.account_id = ba.id "
        query += "LEFT JOIN credit_cards cc ON r.credit_card_id = cc.id "
        where_clauses = []

        if not show_inactive:
            where_clauses.append("r.is_active = 1")

        if transaction_type != "All":
            where_clauses.append(f"r.type = '{transaction_type.lower()}'")

        if where_clauses:
            query += "WHERE " + " AND ".join(where_clauses)

        query += " ORDER BY r.start_date, r.description"

        # Get recurring transactions data
        conn = get_db_connection()
        transactions_df = pd.read_sql_query(query, conn)
        conn.close()

        if not transactions_df.empty:
            # Format dates
            for date_col in ['start_date', 'end_date']:
                if date_col in transactions_df.columns:
                    transactions_df[date_col] = pd.to_datetime(transactions_df[date_col]).dt.strftime('%Y-%m-%d')

            # Replace NaN values in account/card names
            transactions_df['account_name'] = transactions_df['account_name'].fillna('N/A')
            transactions_df['card_name'] = transactions_df['card_name'].fillna('N/A')

            # Create payment method column
            def get_payment_method(row):
                if pd.notna(row['account_id']):
                    return f"Bank: {row['account_name']}"
                elif pd.notna(row['credit_card_id']):
                    return f"Card: {row['card_name']}"
                else:
                    return "Other"

            transactions_df['payment_method'] = transactions_df.apply(get_payment_method, axis=1)

            # Add sign to amount based on type
            transactions_df['signed_amount'] = transactions_df.apply(
                lambda row: row['amount'] if row['type'] == 'income' else -row['amount'],
                axis=1
            )

            # Calculate totals
            total_income = transactions_df[transactions_df['type'] == 'income']['amount'].sum()
            total_expense = transactions_df[transactions_df['type'] == 'expense']['amount'].sum()
            net_cashflow = total_income - total_expense

            # Show the dataframe
            st.dataframe(
                transactions_df[['id', 'description', 'amount', 'frequency', 'category', 'type', 'payment_method', 'start_date', 'end_date', 'is_active']],
                column_config={
                    "id": "ID",
                    "description": "Description",
                    "amount": st.column_config.NumberColumn(
                        "Amount",
                        format="$%.2f",
                    ),
                    "frequency": "Frequency",
                    "category": "Category",
                    "type": st.column_config.TextColumn(
                        "Type",
                        help="Income or expense",
                    ),
                    "payment_method": "Payment Method",
                    "start_date": "Start Date",
                    "end_date": "End Date",
                    "is_active": st.column_config.CheckboxColumn(
                        "Active?",
                        help="Whether this transaction is currently active",
                    ),
                },
                hide_index=True
            )

            # Display summary metrics
            st.subheader("Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Monthly Income", f"${total_income:.2f}", delta=None)
            with col2:
                st.metric("Monthly Expenses", f"${total_expense:.2f}", delta=None)
            with col3:
                st.metric("Net Monthly Cash Flow", f"${net_cashflow:.2f}",
                          delta=f"{'Positive' if net_cashflow >= 0 else 'Negative'}",
                          delta_color="normal" if net_cashflow >= 0 else "inverse")
        else:
            st.info("No recurring transactions found. Add a transaction to get started.")

    # Tab 2: Add Transaction
    with tabs[1]:
        st.subheader("Add New Recurring Transaction")

        # Get bank accounts and credit cards for selection
        conn = get_db_connection()
        bank_accounts = conn.execute("SELECT id, name FROM bank_accounts ORDER BY name").fetchall()
        credit_cards = conn.execute("SELECT id, name FROM credit_cards ORDER BY name").fetchall()
        conn.close()

        # Convert to dictionaries for easy selection
        bank_account_options = {account['name']: account['id'] for account in bank_accounts}
        bank_account_options["None"] = None

        credit_card_options = {card['name']: card['id'] for card in credit_cards}
        credit_card_options["None"] = None

        with st.form("add_transaction_form"):
            description = st.text_input("Description", placeholder="e.g., Rent, Salary, Netflix")

            col1, col2 = st.columns(2)
            with col1:
                amount = st.number_input("Amount", min_value=0.01, format="%.2f", step=50.0)
            with col2:
                transaction_type = st.selectbox("Type", ["Income", "Expense"])

            col1, col2 = st.columns(2)
            with col1:
                frequency = st.selectbox("Frequency", ["Monthly", "Weekly", "Bi-weekly", "Quarterly", "Annually", "One-time"])
            with col2:
                category = st.text_input("Category", placeholder="e.g., Utilities, Salary, Entertainment")

            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=datetime.now().date())
            with col2:
                end_date = st.date_input("End Date (optional)", value=None)

            st.subheader("Payment Method")
            payment_method = st.radio("Select Payment Method", ["Bank Account", "Credit Card", "Other"])

            if payment_method == "Bank Account":
                selected_account = st.selectbox("Select Bank Account", options=list(bank_account_options.keys()))
                account_id = bank_account_options[selected_account]
                credit_card_id = None
            elif payment_method == "Credit Card":
                selected_card = st.selectbox("Select Credit Card", options=list(credit_card_options.keys()))
                credit_card_id = credit_card_options[selected_card]
                account_id = None
            else:
                account_id = None
                credit_card_id = None

            is_active = st.checkbox("Active", value=True, help="Uncheck to temporarily disable this transaction")

            submit_button = st.form_submit_button("Add Recurring Transaction")

            if submit_button:
                if description and category:
                    try:
                        # Handle empty end date
                        end_date_value = end_date if end_date else None

                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            """INSERT INTO recurring_transactions
                            (description, amount, frequency, start_date, end_date, category, type, account_id, credit_card_id, is_active)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (description, amount, frequency.lower(), start_date, end_date_value,
                             category, transaction_type.lower(), account_id, credit_card_id, is_active)
                        )
                        conn.commit()
                        conn.close()
                        st.success(f"Recurring transaction '{description}' successfully added!")
                        # Clear the form
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding transaction: {e}")
                else:
                    st.warning("Please enter a description and category.")

    # Tab 3: Update Transaction
    with tabs[2]:
        st.subheader("Update Recurring Transaction")

        # Get recurring transactions for selection
        conn = get_db_connection()
        transactions = conn.execute("""
            SELECT r.*, ba.name as account_name, cc.name as card_name
            FROM recurring_transactions r
            LEFT JOIN bank_accounts ba ON r.account_id = ba.id
            LEFT JOIN credit_cards cc ON r.credit_card_id = cc.id
            ORDER BY r.description
        """).fetchall()

        # Also get bank accounts and credit cards
        bank_accounts = conn.execute("SELECT id, name FROM bank_accounts ORDER BY name").fetchall()
        credit_cards = conn.execute("SELECT id, name FROM credit_cards ORDER BY name").fetchall()
        conn.close()

        # Convert to dictionaries for easy selection
        bank_account_options = {account['name']: account['id'] for account in bank_accounts}
        bank_account_options["None"] = None

        credit_card_options = {card['name']: card['id'] for card in credit_cards}
        credit_card_options["None"] = None

        if transactions:
            # Create a descriptive label for each transaction
            transaction_options = {
                f"{t['description']} (${t['amount']:.2f} {t['frequency'].capitalize()})": t['id']
                for t in transactions
            }

            selected_transaction_label = st.selectbox("Select Transaction to Update", options=list(transaction_options.keys()))
            selected_transaction_id = transaction_options[selected_transaction_label]

            # Find the selected transaction
            selected_transaction = next((t for t in transactions if t['id'] == selected_transaction_id), None)

            if selected_transaction:
                with st.form("update_transaction_form"):
                    description = st.text_input("Description", value=selected_transaction['description'])

                    col1, col2 = st.columns(2)
                    with col1:
                        amount = st.number_input(
                            "Amount",
                            value=float(selected_transaction['amount']),
                            min_value=0.01,
                            format="%.2f",
                            step=50.0
                        )
                    with col2:
                        transaction_type = st.selectbox(
                            "Type",
                            ["Income", "Expense"],
                            index=0 if selected_transaction['type'] == 'income' else 1
                        )

                    col1, col2 = st.columns(2)
                    with col1:
                        frequency_options = ["Monthly", "Weekly", "Bi-weekly", "Quarterly", "Annually", "One-time"]
                        frequency_index = next(
                            (i for i, f in enumerate(frequency_options) if f.lower() == selected_transaction['frequency']),
                            0
                        )
                        frequency = st.selectbox("Frequency", frequency_options, index=frequency_index)
                    with col2:
                        category = st.text_input("Category", value=selected_transaction['category'])

                    col1, col2 = st.columns(2)
                    with col1:
                        # Parse date strings if needed
                        start_date_value = (
                            datetime.strptime(selected_transaction['start_date'], '%Y-%m-%d').date()
                            if isinstance(selected_transaction['start_date'], str)
                            else selected_transaction['start_date']
                        )
                        start_date = st.date_input("Start Date", value=start_date_value)
                    with col2:
                        end_date_value = None
                        if selected_transaction['end_date']:
                            end_date_value = (
                                datetime.strptime(selected_transaction['end_date'], '%Y-%m-%d').date()
                                if isinstance(selected_transaction['end_date'], str)
                                else selected_transaction['end_date']
                            )
                        end_date = st.date_input("End Date (optional)", value=end_date_value)

                    st.subheader("Payment Method")

                    # Determine current payment method
                    current_method = "Other"
                    if selected_transaction['account_id'] is not None:
                        current_method = "Bank Account"
                    elif selected_transaction['credit_card_id'] is not None:
                        current_method = "Credit Card"

                    payment_method = st.radio("Select Payment Method", ["Bank Account", "Credit Card", "Other"], index=["Bank Account", "Credit Card", "Other"].index(current_method))

                    if payment_method == "Bank Account":
                        # Find current account in options or default to first
                        current_account = "None"
                        if selected_transaction['account_id'] is not None:
                            current_account = next(
                                (name for name, id in bank_account_options.items() if id == selected_transaction['account_id']),
                                "None"
                            )
                        selected_account = st.selectbox("Select Bank Account", options=list(bank_account_options.keys()), index=list(bank_account_options.keys()).index(current_account))
                        account_id = bank_account_options[selected_account]
                        credit_card_id = None
                    elif payment_method == "Credit Card":
                        # Find current card in options or default to first
                        current_card = "None"
                        if selected_transaction['credit_card_id'] is not None:
                            current_card = next(
                                (name for name, id in credit_card_options.items() if id == selected_transaction['credit_card_id']),
                                "None"
                            )
                        selected_card = st.selectbox("Select Credit Card", options=list(credit_card_options.keys()), index=list(credit_card_options.keys()).index(current_card))
                        credit_card_id = credit_card_options[selected_card]
                        account_id = None
                    else:
                        account_id = None
                        credit_card_id = None

                    is_active = st.checkbox("Active", value=bool(selected_transaction['is_active']), help="Uncheck to temporarily disable this transaction")

                    update_button = st.form_submit_button("Update Transaction")

                    if update_button:
                        if description and category:
                            try:
                                # Handle empty end date
                                end_date_value = end_date if end_date else None

                                conn = get_db_connection()
                                cursor = conn.cursor()
                                cursor.execute(
                                    """UPDATE recurring_transactions
                                    SET description = ?, amount = ?, frequency = ?, start_date = ?, end_date = ?,
                                    category = ?, type = ?, account_id = ?, credit_card_id = ?, is_active = ?
                                    WHERE id = ?""",
                                    (description, amount, frequency.lower(), start_date, end_date_value,
                                     category, transaction_type.lower(), account_id, credit_card_id, is_active,
                                     selected_transaction_id)
                                )
                                conn.commit()
                                conn.close()
                                st.success(f"Transaction '{description}' successfully updated!")
                                # Refresh page
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error updating transaction: {e}")
                        else:
                            st.warning("Please enter a description and category.")
        else:
            st.info("No recurring transactions available to update. Please add a transaction first.")

    # Tab 4: Delete Transaction
    with tabs[3]:
        st.subheader("Delete Recurring Transaction")
        st.warning("⚠️ Deleting a transaction will permanently remove it from your records. This action cannot be undone.")

        # Get recurring transactions for selection
        conn = get_db_connection()
        transactions = conn.execute("""
            SELECT id, description, amount, frequency, type
            FROM recurring_transactions
            ORDER BY description
        """).fetchall()
        conn.close()

        if transactions:
            # Create a descriptive label for each transaction
            transaction_options = {
                f"{t['description']} (${t['amount']:.2f} {t['frequency'].capitalize()} - {t['type'].capitalize()})": t['id']
                for t in transactions
            }

            selected_transaction_label = st.selectbox("Select Transaction to Delete", options=list(transaction_options.keys()))
            selected_transaction_id = transaction_options[selected_transaction_label]

            if st.button("Delete Transaction", type="primary", use_container_width=True):
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM recurring_transactions WHERE id = ?", (selected_transaction_id,))
                    conn.commit()
                    conn.close()
                    st.success(f"Transaction '{selected_transaction_label.split(' (')[0]}' successfully deleted!")
                    # Refresh page
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting transaction: {e}")
        else:
            st.info("No transactions available to delete.")
