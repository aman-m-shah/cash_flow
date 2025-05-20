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
# Update the main function in your app.py file

def main():
    st.title("💰 Cash Flow & Credit Card Management")

    # Initialize session state for navigation if it doesn't exist
    if 'page' not in st.session_state:
        st.session_state['page'] = "Dashboard"

    # Sidebar navigation
    st.sidebar.title("Navigation")

    # Use buttons instead of radio for better UX
    if st.sidebar.button("Dashboard", use_container_width=True):
        st.session_state['page'] = "Dashboard"
        st.rerun()

    if st.sidebar.button("Bank Accounts", use_container_width=True):
        st.session_state['page'] = "Bank Accounts"
        st.rerun()

    if st.sidebar.button("Credit Cards", use_container_width=True):
        st.session_state['page'] = "Credit Cards"
        st.rerun()

    if st.sidebar.button("Recurring Transactions", use_container_width=True):
        st.session_state['page'] = "Recurring Transactions"
        st.rerun()

    if st.sidebar.button("Actual Transactions", use_container_width=True):
        st.session_state['page'] = "Actual Transactions"
        st.rerun()

    if st.sidebar.button("Visualization", use_container_width=True):
        st.session_state['page'] = "Visualization"
        st.rerun()

    # Display current page
    if st.session_state['page'] == "Dashboard":
        show_dashboard()
    elif st.session_state['page'] == "Bank Accounts":
        manage_bank_accounts()
    elif st.session_state['page'] == "Credit Cards":
        manage_credit_cards()
    elif st.session_state['page'] == "Recurring Transactions":
        manage_recurring_transactions()
    elif st.session_state['page'] == "Actual Transactions":
        manage_actual_transactions()
    elif st.session_state['page'] == "Visualization":
        show_visualizations()

# Add or update this function in your app.py file

def show_dashboard():
    st.header("Financial Dashboard")

    # Get current date
    today = datetime.now().date()

    # Get data from database
    conn = get_db_connection()

    # Bank account balances
    bank_accounts = pd.read_sql_query(
        "SELECT name, balance FROM bank_accounts ORDER BY name",
        conn
    )

    # Credit card information
    credit_cards = pd.read_sql_query(
        "SELECT name, current_balance, statement_balance, due_date, credit_limit FROM credit_cards ORDER BY name",
        conn,
        parse_dates=["due_date"]
    )

    # Recent transactions
    recent_transactions = pd.read_sql_query(
        """
        SELECT description, amount, date, category, type,
               CASE WHEN account_id IS NOT NULL THEN 'Bank' ELSE 'Credit Card' END as payment_method
        FROM actual_transactions
        ORDER BY date DESC, id DESC
        LIMIT 10
        """,
        conn,
        parse_dates=["date"]
    )

    # Monthly income and expenses
    current_month_start = today.replace(day=1)
    if today.month == 12:
        next_month_start = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month_start = today.replace(month=today.month + 1, day=1)

    monthly_totals = pd.read_sql_query(
        """
        SELECT type, SUM(amount) as total
        FROM actual_transactions
        WHERE date >= ? AND date < ?
        GROUP BY type
        """,
        conn,
        params=[current_month_start, next_month_start]
    )

    # Upcoming bills
    upcoming_bills = pd.read_sql_query(
        """
        SELECT r.description, r.amount, r.category,
               CASE WHEN r.account_id IS NOT NULL THEN ba.name ELSE cc.name END as payment_account
        FROM recurring_transactions r
        LEFT JOIN bank_accounts ba ON r.account_id = ba.id
        LEFT JOIN credit_cards cc ON r.credit_card_id = cc.id
        WHERE r.type = 'expense' AND r.is_active = 1
        ORDER BY r.amount DESC
        LIMIT 5
        """,
        conn
    )

    # Close connection
    conn.close()

    # Create dashboard

    # Summary metrics
    st.subheader("Financial Overview")

    # Calculate totals
    total_bank_balance = bank_accounts['balance'].sum() if not bank_accounts.empty else 0
    total_credit_card_balance = credit_cards['current_balance'].sum() if not credit_cards.empty else 0
    net_worth = total_bank_balance - total_credit_card_balance

    # Monthly income/expense
    monthly_income = monthly_totals[monthly_totals['type'] == 'income']['total'].sum() if not monthly_totals.empty else 0
    monthly_expense = monthly_totals[monthly_totals['type'] == 'expense']['total'].sum() if not monthly_totals.empty else 0
    monthly_net = monthly_income - monthly_expense

    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Bank Balance", f"${total_bank_balance:,.2f}")
    with col2:
        st.metric("Credit Card Debt", f"${total_credit_card_balance:,.2f}")
    with col3:
        st.metric("Net Worth", f"${net_worth:,.2f}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("This Month's Income", f"${monthly_income:,.2f}")
    with col2:
        st.metric("This Month's Expenses", f"${monthly_expense:,.2f}")
    with col3:
        st.metric("Monthly Net Cash Flow", f"${monthly_net:,.2f}",
                 delta=f"{'Positive' if monthly_net >= 0 else 'Negative'}",
                 delta_color="normal" if monthly_net >= 0 else "inverse")

    # Bank accounts and credit cards
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Bank Accounts")
        if not bank_accounts.empty:
            st.dataframe(
                bank_accounts,
                column_config={
                    "name": "Account",
                    "balance": st.column_config.NumberColumn(
                        "Balance",
                        format="$%.2f",
                    ),
                },
                hide_index=True
            )
        else:
            st.info("No bank accounts found. Add an account to get started.")

    with col2:
        st.subheader("Credit Cards")
        if not credit_cards.empty:
            # Format due date
            credit_cards['due_date_str'] = credit_cards['due_date'].dt.strftime('%Y-%m-%d')

            # Calculate days until due
            credit_cards['days_until_due'] = (credit_cards['due_date'] - pd.Timestamp(today)).dt.days

            # Add alert emoji for soon due dates
            def get_alert(days):
                if days < 0:
                    return "🚨 Overdue"
                elif days <= 3:
                    return "⚠️ Due soon"
                elif days <= 7:
                    return "⏰ Upcoming"
                else:
                    return ""

            credit_cards['alert'] = credit_cards['days_until_due'].apply(get_alert)

            st.dataframe(
                credit_cards[['name', 'current_balance', 'statement_balance', 'due_date_str', 'alert']],
                column_config={
                    "name": "Card",
                    "current_balance": st.column_config.NumberColumn(
                        "Current Balance",
                        format="$%.2f",
                    ),
                    "statement_balance": st.column_config.NumberColumn(
                        "Statement Balance",
                        format="$%.2f",
                    ),
                    "due_date_str": "Due Date",
                    "alert": "Status"
                },
                hide_index=True
            )
        else:
            st.info("No credit cards found. Add a card to get started.")

    # Recent transactions and upcoming bills
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Recent Transactions")
        if not recent_transactions.empty:
            # Format the date
            recent_transactions['date_str'] = recent_transactions['date'].dt.strftime('%Y-%m-%d')

            # Add sign to amount based on type
            recent_transactions['display_amount'] = recent_transactions.apply(
                lambda row: row['amount'] if row['type'] == 'income' else -row['amount'],
                axis=1
            )

            st.dataframe(
                recent_transactions[['date_str', 'description', 'display_amount', 'category']],
                column_config={
                    "date_str": "Date",
                    "description": "Description",
                    "display_amount": st.column_config.NumberColumn(
                        "Amount",
                        format="$%.2f",
                    ),
                    "category": "Category",
                },
                hide_index=True
            )
        else:
            st.info("No recent transactions found.")

    with col2:
        st.subheader("Top Monthly Expenses")
        if not upcoming_bills.empty:
            st.dataframe(
                upcoming_bills,
                column_config={
                    "description": "Description",
                    "amount": st.column_config.NumberColumn(
                        "Amount",
                        format="$%.2f",
                    ),
                    "category": "Category",
                    "payment_account": "Payment Method"
                },
                hide_index=True
            )
        else:
            st.info("No recurring bills found.")

    # Quick actions
    st.subheader("Quick Actions")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Add Transaction", use_container_width=True):
            st.session_state['page'] = "Actual Transactions"
            st.rerun()
    with col2:
        if st.button("Add Bank Account", use_container_width=True):
            st.session_state['page'] = "Bank Accounts"
            st.rerun()
    with col3:
        if st.button("Add Credit Card", use_container_width=True):
            st.session_state['page'] = "Credit Cards"
            st.rerun()
    with col4:
        if st.button("View Reports", use_container_width=True):
            st.session_state['page'] = "Visualization"
            st.rerun()

    # Tips and insights
    st.subheader("Financial Insights")

    # Generate insights based on data
    insights = []

    # Credit card due dates
    if not credit_cards.empty:
        due_soon = credit_cards[credit_cards['days_until_due'] <= 7]
        if not due_soon.empty:
            for _, card in due_soon.iterrows():
                day_text = "days" if card['days_until_due'] > 1 else "day"
                insights.append(f"💳 {card['name']} payment of ${card['statement_balance']:,.2f} is due in {card['days_until_due']} {day_text}.")

    # Low bank balance
    if not bank_accounts.empty:
        low_accounts = bank_accounts[bank_accounts['balance'] < 100]
        if not low_accounts.empty:
            for _, account in low_accounts.iterrows():
                insights.append(f"⚠️ {account['name']} has a low balance (${account['balance']:,.2f}).")

    # Positive cash flow
    if monthly_net > 0:
        insights.append(f"✅ You're cash flow positive this month by ${monthly_net:,.2f}.")
    else:
        insights.append(f"⚠️ You're spending more than you earn this month (${monthly_net:,.2f}).")

    # High credit card utilization
    if not credit_cards.empty:
        high_util_cards = credit_cards[credit_cards['current_balance'] / credit_cards['credit_limit'] > 0.3]
        if not high_util_cards.empty:
            for _, card in high_util_cards.iterrows():
                util_pct = (card['current_balance'] / card['credit_limit']) * 100
                insights.append(f"⚠️ {card['name']} has high utilization ({util_pct:.1f}%). Consider paying down this balance.")

    # Display insights
    if insights:
        for insight in insights:
            st.info(insight)
    else:
        st.success("All accounts look good! No urgent financial matters need attention.")

    # Additional dashboard widgets can be added here
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
                frequency = st.selectbox("Frequency", ["Monthly", "Semi-monthly", "Bi-weekly", "Weekly", "Quarterly", "Annually", "One-time"])
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
                        frequency_options = ["Monthly", "Semi-monthly", "Bi-weekly", "Weekly", "Quarterly", "Annually", "One-time"]
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

# Add this function to your app.py file

def manage_actual_transactions():
    st.header("Manage Actual Transactions")

    # Create tabs for different operations
    tabs = st.tabs(["View Transactions", "Add Transaction", "Update Transaction", "Delete Transaction", "Import Transactions"])

    # Tab 1: View Transactions
    with tabs[0]:
        st.subheader("Actual Transactions")

        # Date range filter
        col1, col2 = st.columns(2)
        with col1:
            start_date_filter = st.date_input(
                "From Date",
                value=datetime.now().replace(day=1).date(),  # First day of current month
                key="actual_trans_start_date"
            )
        with col2:
            end_date_filter = st.date_input(
                "To Date",
                value=datetime.now().date(),
                key="actual_trans_end_date"
            )

        # Transaction type filter
        transaction_type = st.selectbox("Filter by Type", ["All", "Income", "Expense"], key="actual_trans_type")

        # Category filter
        conn = get_db_connection()
        categories = conn.execute("SELECT DISTINCT category FROM actual_transactions ORDER BY category").fetchall()
        conn.close()

        category_options = ["All"] + [cat['category'] for cat in categories]
        selected_category = st.selectbox("Filter by Category", category_options, key="actual_trans_category")

        # Prepare SQL query based on filters
        query = """
            SELECT a.*, ba.name as account_name, cc.name as card_name
            FROM actual_transactions a
            LEFT JOIN bank_accounts ba ON a.account_id = ba.id
            LEFT JOIN credit_cards cc ON a.credit_card_id = cc.id
            WHERE a.date BETWEEN ? AND ?
        """
        params = [start_date_filter, end_date_filter]

        if transaction_type != "All":
            query += " AND a.type = ?"
            params.append(transaction_type.lower())

        if selected_category != "All":
            query += " AND a.category = ?"
            params.append(selected_category)

        query += " ORDER BY a.date DESC, a.id DESC"

        # Get actual transactions data
        conn = get_db_connection()
        cursor = conn.cursor()
        transactions = cursor.execute(query, params).fetchall()

        # Convert to DataFrame
        if transactions:
            transactions_df = pd.DataFrame(transactions)

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

            # Format dates
            transactions_df['date'] = pd.to_datetime(transactions_df['date']).dt.strftime('%Y-%m-%d')

            # Calculate totals
            total_income = transactions_df[transactions_df['type'] == 'income']['amount'].sum()
            total_expense = transactions_df[transactions_df['type'] == 'expense']['amount'].sum()
            net_cashflow = total_income - total_expense

            # Show the dataframe
            st.dataframe(
                transactions_df[['id', 'date', 'description', 'amount', 'category', 'type', 'payment_method']],
                column_config={
                    "id": "ID",
                    "date": "Date",
                    "description": "Description",
                    "amount": st.column_config.NumberColumn(
                        "Amount",
                        format="$%.2f",
                    ),
                    "category": "Category",
                    "type": st.column_config.TextColumn(
                        "Type",
                        help="Income or expense",
                    ),
                    "payment_method": "Payment Method",
                },
                hide_index=True
            )

            # Display summary metrics
            st.subheader("Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Income", f"${total_income:.2f}", delta=None)
            with col2:
                st.metric("Total Expenses", f"${total_expense:.2f}", delta=None)
            with col3:
                st.metric("Net Cash Flow", f"${net_cashflow:.2f}",
                          delta=f"{'Positive' if net_cashflow >= 0 else 'Negative'}",
                          delta_color="normal" if net_cashflow >= 0 else "inverse")
        else:
            st.info("No transactions found for the selected filters.")

        conn.close()

    # Tab 2: Add Transaction
    with tabs[1]:
        st.subheader("Add New Transaction")

        # Get bank accounts and credit cards for selection
        conn = get_db_connection()
        bank_accounts = conn.execute("SELECT id, name FROM bank_accounts ORDER BY name").fetchall()
        credit_cards = conn.execute("SELECT id, name FROM credit_cards ORDER BY name").fetchall()

        # Get existing categories for suggestions
        categories = conn.execute("SELECT DISTINCT category FROM actual_transactions UNION SELECT DISTINCT category FROM recurring_transactions ORDER BY category").fetchall()
        category_suggestions = [cat['category'] for cat in categories]

        conn.close()

        # Convert to dictionaries for easy selection
        bank_account_options = {account['name']: account['id'] for account in bank_accounts}
        bank_account_options["None"] = None

        credit_card_options = {card['name']: card['id'] for card in credit_cards}
        credit_card_options["None"] = None

        with st.form("add_actual_transaction_form"):
            description = st.text_input("Description", placeholder="e.g., Grocery shopping, Salary payment")

            col1, col2 = st.columns(2)
            with col1:
                amount = st.number_input("Amount", min_value=0.01, format="%.2f", step=10.0)
            with col2:
                transaction_type = st.selectbox("Type", ["Expense", "Income"])

            col1, col2 = st.columns(2)
            with col1:
                transaction_date = st.date_input("Transaction Date", value=datetime.now().date())
            with col2:
                # Category with autocomplete-like behavior
                category = st.selectbox(
                    "Category",
                    options=[""] + category_suggestions,
                    index=0
                )
                if category == "":
                    category = st.text_input("Or enter a new category", placeholder="e.g., Groceries, Salary, Entertainment")

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

            # Optional recurring transaction association
            associate_recurring = st.checkbox("Link to a recurring transaction", value=False)
            if associate_recurring:
                st.info("This feature will be implemented in a future update.")

            submit_button = st.form_submit_button("Add Transaction")

            if submit_button:
                if description and category:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            """INSERT INTO actual_transactions
                            (description, amount, date, category, type, account_id, credit_card_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (description, amount, transaction_date, category,
                             transaction_type.lower(), account_id, credit_card_id)
                        )

                        # If this is an expense using a credit card, update the credit card balance
                        if transaction_type.lower() == 'expense' and credit_card_id is not None:
                            cursor.execute(
                                "UPDATE credit_cards SET current_balance = current_balance + ? WHERE id = ?",
                                (amount, credit_card_id)
                            )

                        # If this is an expense using a bank account, update the bank account balance
                        if transaction_type.lower() == 'expense' and account_id is not None:
                            cursor.execute(
                                "UPDATE bank_accounts SET balance = balance - ? WHERE id = ?",
                                (amount, account_id)
                            )

                        # If this is income using a bank account, update the bank account balance
                        if transaction_type.lower() == 'income' and account_id is not None:
                            cursor.execute(
                                "UPDATE bank_accounts SET balance = balance + ? WHERE id = ?",
                                (amount, account_id)
                            )

                        conn.commit()
                        conn.close()
                        st.success(f"Transaction '{description}' successfully added!")
                        # Clear the form
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding transaction: {e}")
                else:
                    st.warning("Please enter a description and category.")

    # Tab 3: Update Transaction
    with tabs[2]:
        st.subheader("Update Transaction")

        # Get recent transactions for selection
        conn = get_db_connection()
        transactions = conn.execute("""
            SELECT a.*, ba.name as account_name, cc.name as card_name
            FROM actual_transactions a
            LEFT JOIN bank_accounts ba ON a.account_id = ba.id
            LEFT JOIN credit_cards cc ON a.credit_card_id = cc.id
            ORDER BY a.date DESC, a.id DESC
            LIMIT 100
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
                f"{t['date']} - {t['description']} (${t['amount']:.2f})": t['id']
                for t in transactions
            }

            selected_transaction_label = st.selectbox("Select Transaction to Update", options=list(transaction_options.keys()))
            selected_transaction_id = transaction_options[selected_transaction_label]

            # Find the selected transaction
            selected_transaction = next((t for t in transactions if t['id'] == selected_transaction_id), None)

            if selected_transaction:
                with st.form("update_actual_transaction_form"):
                    description = st.text_input("Description", value=selected_transaction['description'])

                    col1, col2 = st.columns(2)
                    with col1:
                        amount = st.number_input(
                            "Amount",
                            value=float(selected_transaction['amount']),
                            min_value=0.01,
                            format="%.2f",
                            step=10.0
                        )
                    with col2:
                        transaction_type = st.selectbox(
                            "Type",
                            ["Income", "Expense"],
                            index=0 if selected_transaction['type'] == 'income' else 1
                        )

                    col1, col2 = st.columns(2)
                    with col1:
                        # Parse date string if needed
                        date_value = (
                            datetime.strptime(selected_transaction['date'], '%Y-%m-%d').date()
                            if isinstance(selected_transaction['date'], str)
                            else selected_transaction['date']
                        )
                        transaction_date = st.date_input("Transaction Date", value=date_value)
                    with col2:
                        category = st.text_input("Category", value=selected_transaction['category'])

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

                    # Get original values for balance updates
                    original_amount = selected_transaction['amount']
                    original_type = selected_transaction['type']
                    original_account_id = selected_transaction['account_id']
                    original_credit_card_id = selected_transaction['credit_card_id']

                    update_button = st.form_submit_button("Update Transaction")

                    if update_button:
                        if description and category:
                            try:
                                conn = get_db_connection()
                                cursor = conn.cursor()

                                # First, reverse the effect of the original transaction on balances
                                if original_type == 'expense' and original_credit_card_id is not None:
                                    cursor.execute(
                                        "UPDATE credit_cards SET current_balance = current_balance - ? WHERE id = ?",
                                        (original_amount, original_credit_card_id)
                                    )

                                if original_type == 'expense' and original_account_id is not None:
                                    cursor.execute(
                                        "UPDATE bank_accounts SET balance = balance + ? WHERE id = ?",
                                        (original_amount, original_account_id)
                                    )

                                if original_type == 'income' and original_account_id is not None:
                                    cursor.execute(
                                        "UPDATE bank_accounts SET balance = balance - ? WHERE id = ?",
                                        (original_amount, original_account_id)
                                    )

                                # Update the transaction
                                cursor.execute(
                                    """UPDATE actual_transactions
                                    SET description = ?, amount = ?, date = ?, category = ?, type = ?, account_id = ?, credit_card_id = ?
                                    WHERE id = ?""",
                                    (description, amount, transaction_date, category, transaction_type.lower(),
                                     account_id, credit_card_id, selected_transaction_id)
                                )

                                # Apply the effect of the updated transaction on balances
                                if transaction_type.lower() == 'expense' and credit_card_id is not None:
                                    cursor.execute(
                                        "UPDATE credit_cards SET current_balance = current_balance + ? WHERE id = ?",
                                        (amount, credit_card_id)
                                    )

                                if transaction_type.lower() == 'expense' and account_id is not None:
                                    cursor.execute(
                                        "UPDATE bank_accounts SET balance = balance - ? WHERE id = ?",
                                        (amount, account_id)
                                    )

                                if transaction_type.lower() == 'income' and account_id is not None:
                                    cursor.execute(
                                        "UPDATE bank_accounts SET balance = balance + ? WHERE id = ?",
                                        (amount, account_id)
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
            st.info("No transactions available to update. Please add a transaction first.")

    # Tab 4: Delete Transaction
    with tabs[3]:
        st.subheader("Delete Transaction")
        st.warning("⚠️ Deleting a transaction will permanently remove it from your records. This action cannot be undone.")

        # Get recent transactions for selection
        conn = get_db_connection()
        transactions = conn.execute("""
            SELECT id, date, description, amount, type, account_id, credit_card_id
            FROM actual_transactions
            ORDER BY date DESC, id DESC
            LIMIT 100
        """).fetchall()
        conn.close()

        if transactions:
            # Create a descriptive label for each transaction
            transaction_options = {
                f"{t['date']} - {t['description']} (${t['amount']:.2f})": t['id']
                for t in transactions
            }

            selected_transaction_label = st.selectbox("Select Transaction to Delete", options=list(transaction_options.keys()))
            selected_transaction_id = transaction_options[selected_transaction_label]

            # Find the selected transaction
            selected_transaction = next((t for t in transactions if t['id'] == selected_transaction_id), None)

            if st.button("Delete Transaction", type="primary", use_container_width=True):
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()

                    # First, reverse the effect of the transaction on balances
                    if selected_transaction['type'] == 'expense' and selected_transaction['credit_card_id'] is not None:
                        cursor.execute(
                            "UPDATE credit_cards SET current_balance = current_balance - ? WHERE id = ?",
                            (selected_transaction['amount'], selected_transaction['credit_card_id'])
                        )

                    if selected_transaction['type'] == 'expense' and selected_transaction['account_id'] is not None:
                        cursor.execute(
                            "UPDATE bank_accounts SET balance = balance + ? WHERE id = ?",
                            (selected_transaction['amount'], selected_transaction['account_id'])
                        )

                    if selected_transaction['type'] == 'income' and selected_transaction['account_id'] is not None:
                        cursor.execute(
                            "UPDATE bank_accounts SET balance = balance - ? WHERE id = ?",
                            (selected_transaction['amount'], selected_transaction['account_id'])
                        )

                    # Delete the transaction
                    cursor.execute("DELETE FROM actual_transactions WHERE id = ?", (selected_transaction_id,))
                    conn.commit()
                    conn.close()
                    st.success(f"Transaction '{selected_transaction_label.split(' - ')[1].split(' (')[0]}' successfully deleted!")
                    # Refresh page
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting transaction: {e}")
        else:
            st.info("No transactions available to delete.")

    # Tab 5: Import Transactions
    with tabs[4]:
        st.subheader("Import Transactions")
        st.info("Upload a CSV file to bulk import transactions.")

        # File uploader
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

        if uploaded_file is not None:
            # Read the CSV file
            try:
                transactions_df = pd.read_csv(uploaded_file)
                st.write("Preview of uploaded data:")
                st.dataframe(transactions_df.head())

                # Identify columns
                st.subheader("Map Columns")
                st.write("Please map your CSV columns to the required transaction fields.")

                # Get column names
                columns = list(transactions_df.columns)
                none_option = "-- None --"
                columns_with_none = [none_option] + columns

                # Get bank accounts and credit cards
                conn = get_db_connection()
                bank_accounts = conn.execute("SELECT id, name FROM bank_accounts ORDER BY name").fetchall()
                credit_cards = conn.execute("SELECT id, name FROM credit_cards ORDER BY name").fetchall()
                conn.close()

                # Convert to dictionaries for easy selection
                bank_account_options = {account['name']: account['id'] for account in bank_accounts}
                bank_account_options["None"] = None

                credit_card_options = {card['name']: card['id'] for card in credit_cards}
                credit_card_options["None"] = None

                with st.form("import_mapping_form"):
                    # Required fields
                    date_col = st.selectbox("Date Column", columns_with_none, index=columns_with_none.index("date") if "date" in columns_with_none else 0)
                    description_col = st.selectbox("Description Column", columns_with_none, index=columns_with_none.index("description") if "description" in columns_with_none else 0)
                    amount_col = st.selectbox("Amount Column", columns_with_none, index=columns_with_none.index("amount") if "amount" in columns_with_none else 0)

                    # Optional fields
                    category_col = st.selectbox("Category Column (optional)", columns_with_none, index=columns_with_none.index("category") if "category" in columns_with_none else 0)
                    type_col = st.selectbox("Transaction Type Column (optional)", columns_with_none, index=columns_with_none.index("type") if "type" in columns_with_none else 0)

                    st.subheader("Default Values")
                    st.write("If your CSV doesn't include these fields, set default values:")

                    # Default category if not in CSV
                    if category_col == none_option:
                        default_category = st.text_input("Default Category", value="Uncategorized")

                    # Default type if not in CSV
                    if type_col == none_option:
                        default_type = st.selectbox("Default Transaction Type", ["Expense", "Income"], index=0)

                    # Default payment method
                    payment_method = st.radio("Default Payment Method", ["Bank Account", "Credit Card", "Other"])

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

                    # Date format
                    date_format = st.selectbox(
                        "Date Format in CSV",
                        options=[
                            "%Y-%m-%d",  # 2023-01-31
                            "%m/%d/%Y",  # 01/31/2023
                            "%d/%m/%Y",  # 31/01/2023
                            "%m-%d-%Y",  # 01-31-2023
                            "%d-%m-%Y",  # 31-01-2023
                            "%Y/%m/%d",  # 2023/01/31
                        ],
                        index=0
                    )

                    # Amount interpretation
                    amount_sign = st.radio(
                        "Amount Sign Interpretation",
                        options=[
                            "Positive=Income, Negative=Expense",
                            "All amounts are expenses",
                            "All amounts are income",
                            "Use Type column only"
                        ],
                        index=0
                    )

                    # Submit button
                    import_button = st.form_submit_button("Import Transactions")

                    if import_button:
                        if date_col == none_option or description_col == none_option or amount_col == none_option:
                            st.error("Date, Description, and Amount columns are required.")
                        else:
                            try:
                                # Convert date column
                                transactions_df[date_col] = pd.to_datetime(transactions_df[date_col], format=date_format)

                                # Connect to database
                                conn = get_db_connection()
                                cursor = conn.cursor()

                                # Counter for successful imports
                                success_count = 0
                                error_count = 0

                                # Process each row
                                for _, row in transactions_df.iterrows():
                                    try:
                                        # Get values from row
                                        date_value = row[date_col].strftime('%Y-%m-%d')
                                        description_value = str(row[description_col])
                                        amount_value = abs(float(row[amount_col]))  # Take absolute value, handle sign later

                                        # Get category
                                        if category_col != none_option:
                                            category_value = str(row[category_col])
                                        else:
                                            category_value = default_category

                                        # Determine transaction type
                                        if type_col != none_option:
                                            # Use type from CSV
                                            type_value = str(row[type_col]).lower()
                                            # Normalize type values
                                            if type_value in ['expense', 'debit', 'payment', 'purchase', 'withdraw', 'withdrawal']:
                                                type_value = 'expense'
                                            elif type_value in ['income', 'credit', 'deposit', 'refund', 'inflow']:
                                                type_value = 'income'
                                            else:
                                                # Default to expense if unclear
                                                type_value = 'expense'
                                        elif amount_sign == "Positive=Income, Negative=Expense":
                                            # Determine by amount sign in original data
                                            original_amount = float(row[amount_col])
                                            type_value = 'income' if original_amount > 0 else 'expense'
                                        elif amount_sign == "All amounts are expenses":
                                            type_value = 'expense'
                                        elif amount_sign == "All amounts are income":
                                            type_value = 'income'
                                        else:
                                            # Default from form
                                            type_value = default_type.lower()

                                        # Insert into database
                                        cursor.execute(
                                            """INSERT INTO actual_transactions
                                            (description, amount, date, category, type, account_id, credit_card_id)
                                            VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                            (description_value, amount_value, date_value, category_value,
                                             type_value, account_id, credit_card_id)
                                        )

                                        # Update balances based on transaction type
                                        if type_value == 'expense' and credit_card_id is not None:
                                            cursor.execute(
                                                "UPDATE credit_cards SET current_balance = current_balance + ? WHERE id = ?",
                                                (amount_value, credit_card_id)
                                            )

                                        if type_value == 'expense' and account_id is not None:
                                            cursor.execute(
                                                "UPDATE bank_accounts SET balance = balance - ? WHERE id = ?",
                                                (amount_value, account_id)
                                            )

                                        if type_value == 'income' and account_id is not None:
                                            cursor.execute(
                                                "UPDATE bank_accounts SET balance = balance + ? WHERE id = ?",
                                                (amount_value, account_id)
                                            )

                                        success_count += 1
                                    except Exception as e:
                                        error_count += 1
                                        st.error(f"Error processing row: {e}")

                                # Commit changes
                                conn.commit()
                                conn.close()

                                # Show results
                                st.success(f"Successfully imported {success_count} transactions.")
                                if error_count > 0:
                                    st.warning(f"Failed to import {error_count} transactions due to errors.")

                                # Refresh page
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error importing transactions: {e}")
            except Exception as e:
                st.error(f"Error reading CSV file: {e}")
                st.write("Please ensure your CSV file is formatted correctly.")

def show_visualizations():
    st.header("Financial Visualizations")

    # Create tabs for different visualizations
    tabs = st.tabs([
        "Cash Flow Overview",
        "Expected vs. Actual Spending",
        "Credit Card Utilization",
        "Spending by Category",
        "Balance Forecast"
    ])

    # Tab 1: Cash Flow Overview
    with tabs[0]:
        st.subheader("Cash Flow Overview")

        # Date range selection
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "From Date",
                value=(datetime.now() - timedelta(days=90)).date(),
                key="vis_cashflow_start_date"
            )
        with col2:
            end_date = st.date_input(
                "To Date",
                value=datetime.now().date(),
                key="vis_cashflow_end_date"
            )

        # Time period grouping
        period = st.selectbox(
            "Group By",
            ["Day", "Week", "Month"],
            index=1,  # Default to weekly
            key="vis_cashflow_period"
        )

        # Get transaction data
        conn = get_db_connection()
        actual_transactions = pd.read_sql_query(
            "SELECT date, type, amount FROM actual_transactions WHERE date BETWEEN ? AND ? ORDER BY date",
            conn,
            params=[start_date, end_date],
            parse_dates=["date"]
        )
        conn.close()

        if not actual_transactions.empty:
            # Process data for visualization
            if period == "Day":
                # Daily grouping
                actual_transactions['period'] = actual_transactions['date']
            elif period == "Week":
                # Weekly grouping (week starting Monday)
                actual_transactions['period'] = actual_transactions['date'].dt.to_period('W').dt.start_time
            else:
                # Monthly grouping
                actual_transactions['period'] = actual_transactions['date'].dt.to_period('M').dt.start_time

            # Group by period and type
            income_df = actual_transactions[actual_transactions['type'] == 'income'].groupby('period')['amount'].sum().reset_index()
            expense_df = actual_transactions[actual_transactions['type'] == 'expense'].groupby('period')['amount'].sum().reset_index()

            # Create a complete date range for consistent visualization
            all_periods = pd.date_range(start=start_date, end=end_date, freq='D' if period == "Day" else ('W' if period == "Week" else 'MS'))
            all_periods_df = pd.DataFrame(all_periods, columns=['period'])

            # Rename for clarity when merging
            income_df.rename(columns={'amount': 'income'}, inplace=True)
            expense_df.rename(columns={'amount': 'expense'}, inplace=True)

            # Merge all data, filling NaN with 0
            merged_df = all_periods_df.merge(income_df, on='period', how='left').merge(expense_df, on='period', how='left')
            merged_df.fillna(0, inplace=True)

            # Calculate net cash flow
            merged_df['net'] = merged_df['income'] - merged_df['expense']

            # Format period column for display
            if period == "Day":
                merged_df['period_str'] = merged_df['period'].dt.strftime('%Y-%m-%d')
            elif period == "Week":
                merged_df['period_str'] = merged_df['period'].dt.strftime('Week of %b %d, %Y')
            else:
                merged_df['period_str'] = merged_df['period'].dt.strftime('%b %Y')

            # Create visualization
            fig, ax = plt.subplots(figsize=(10, 6))

            # Plot bars
            x = range(len(merged_df))
            width = 0.35

            # Income bars
            income_bars = ax.bar([i - width/2 for i in x], merged_df['income'], width, label='Income', color='green', alpha=0.7)

            # Expense bars
            expense_bars = ax.bar([i + width/2 for i in x], merged_df['expense'], width, label='Expenses', color='red', alpha=0.7)

            # Net line
            ax.plot(x, merged_df['net'], color='blue', marker='o', linestyle='-', linewidth=2, label='Net Cash Flow')

            # Add zero line
            ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)

            # Labels and title
            ax.set_xlabel('Period')
            ax.set_ylabel('Amount ($)')
            ax.set_title('Income, Expenses and Net Cash Flow Over Time')

            # X-axis labels
            ax.set_xticks(x)
            ax.set_xticklabels(merged_df['period_str'], rotation=45, ha='right')

            # Limit the number of x-axis labels to prevent overcrowding
            if len(merged_df) > 10:
                # Show only every nth label
                n = len(merged_df) // 10 + 1
                for i, label in enumerate(ax.xaxis.get_ticklabels()):
                    if i % n != 0:
                        label.set_visible(False)

            ax.legend()

            # Format y-axis as currency
            import matplotlib.ticker as mtick
            fmt = '${x:,.0f}'
            tick = mtick.StrMethodFormatter(fmt)
            ax.yaxis.set_major_formatter(tick)

            # Adjust layout
            plt.tight_layout()

            # Show the plot
            st.pyplot(fig)

            # Summary metrics
            st.subheader("Summary")
            total_income = merged_df['income'].sum()
            total_expense = merged_df['expense'].sum()
            total_net = total_income - total_expense

            cols = st.columns(3)
            with cols[0]:
                st.metric("Total Income", f"${total_income:,.2f}")
            with cols[1]:
                st.metric("Total Expenses", f"${total_expense:,.2f}")
            with cols[2]:
                st.metric("Net Cash Flow", f"${total_net:,.2f}",
                         delta=None if total_net == 0 else f"{'Positive' if total_net > 0 else 'Negative'}",
                         delta_color="normal" if total_net >= 0 else "inverse")

            # Data table
            with st.expander("Show detailed data"):
                st.dataframe(
                    merged_df[['period_str', 'income', 'expense', 'net']],
                    column_config={
                        "period_str": "Period",
                        "income": st.column_config.NumberColumn(
                            "Income",
                            format="$%.2f",
                        ),
                        "expense": st.column_config.NumberColumn(
                            "Expenses",
                            format="$%.2f",
                        ),
                        "net": st.column_config.NumberColumn(
                            "Net Cash Flow",
                            format="$%.2f",
                        ),
                    },
                    hide_index=True
                )
        else:
            st.info("No transaction data available for the selected date range.")

    # Tab 2: Expected vs. Actual Spending
    with tabs[1]:
        st.subheader("Expected vs. Actual Spending")

        # Date range selection
        col1, col2 = st.columns(2)
        with col1:
            month_year = st.date_input(
                "Select Month",
                value=datetime.now().replace(day=1).date(),
                key="vis_exp_vs_act_date"
            )
        with col2:
            category_filter = st.selectbox(
                "Filter by Category",
                ["All Categories", "By Category"],
                index=0,
                key="vis_exp_vs_act_category"
            )

        # Calculate start and end of the selected month
        month_start = month_year.replace(day=1)
        if month_year.month == 12:
            month_end = month_year.replace(year=month_year.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month_year.replace(month=month_year.month + 1, day=1) - timedelta(days=1)

        # Get recurring transactions data
        conn = get_db_connection()
        recurring_transactions = pd.read_sql_query(
            """
            SELECT description, amount, category, frequency, type, start_date, end_date, is_active
            FROM recurring_transactions
            WHERE is_active = 1
            AND (start_date <= ? AND (end_date IS NULL OR end_date >= ?))
            AND type = 'expense'
            """,
            conn,
            params=[month_end, month_start],
            parse_dates=["start_date", "end_date"]
        )

        # Get actual transactions data
        actual_transactions = pd.read_sql_query(
            """
            SELECT description, amount, category, date, type
            FROM actual_transactions
            WHERE date BETWEEN ? AND ?
            AND type = 'expense'
            """,
            conn,
            params=[month_start, month_end],
            parse_dates=["date"]
        )
        conn.close()

        if not recurring_transactions.empty or not actual_transactions.empty:
            # Process recurring transactions to calculate expected monthly amount
            def calculate_monthly_amount(row):
                frequency = row['frequency'].lower()
                amount = row['amount']

                if frequency == 'monthly':
                    return amount
                elif frequency == 'semi-monthly':
                    return amount * 2  # Twice per month
                elif frequency == 'weekly':
                    return amount * 4.33  # Average weeks in a month
                elif frequency == 'bi-weekly':
                    return amount * 2.17  # Average bi-weekly periods in a month
                elif frequency == 'quarterly':
                    return amount / 3
                elif frequency == 'annually':
                    return amount / 12
                elif frequency == 'one-time':
                    # Check if one-time payment falls in this month
                    payment_date = row['start_date']
                    if month_start <= payment_date <= month_end:
                        return amount
                    else:
                        return 0
                else:
                    return amount  # Default to monthly

            recurring_transactions['monthly_amount'] = recurring_transactions.apply(calculate_monthly_amount, axis=1)

            if category_filter == "All Categories":
                # Aggregate data without breaking down by category
                expected_total = recurring_transactions['monthly_amount'].sum()
                actual_total = actual_transactions['amount'].sum() if not actual_transactions.empty else 0

                # Create bar chart
                fig, ax = plt.subplots(figsize=(10, 6))

                # Plot bars
                x = ['Expected', 'Actual']
                values = [expected_total, actual_total]
                bars = ax.bar(x, values, color=['blue', 'orange'], alpha=0.7)

                # Add data labels
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 5,
                            f'${height:,.2f}',
                            ha='center', va='bottom', rotation=0)

                # Labels and title
                month_name = month_year.strftime('%B %Y')
                ax.set_title(f'Expected vs Actual Spending for {month_name}')
                ax.set_ylabel('Amount ($)')

                # Format y-axis as currency
                import matplotlib.ticker as mtick
                fmt = '${x:,.0f}'
                tick = mtick.StrMethodFormatter(fmt)
                ax.yaxis.set_major_formatter(tick)

                # Calculate difference
                difference = actual_total - expected_total
                percent_diff = (difference / expected_total * 100) if expected_total > 0 else 0

                # Show the plot
                st.pyplot(fig)

                # Summary metrics
                st.subheader("Summary")
                cols = st.columns(3)
                with cols[0]:
                    st.metric("Expected Spending", f"${expected_total:,.2f}")
                with cols[1]:
                    st.metric("Actual Spending", f"${actual_total:,.2f}")
                with cols[2]:
                    st.metric("Difference", f"${difference:,.2f}",
                             delta=f"{percent_diff:.1f}%",
                             delta_color="inverse" if difference > 0 else "normal")
            else:
                # Aggregate data by category
                expected_by_category = recurring_transactions.groupby('category')['monthly_amount'].sum().reset_index()

                if not actual_transactions.empty:
                    actual_by_category = actual_transactions.groupby('category')['amount'].sum().reset_index()
                else:
                    actual_by_category = pd.DataFrame(columns=['category', 'amount'])

                # Merge expected and actual, filling NaN with 0
                all_categories = pd.DataFrame({'category': pd.concat([expected_by_category['category'], actual_by_category['category']]).unique()})
                merged_categories = all_categories.merge(expected_by_category, on='category', how='left').merge(actual_by_category, on='category', how='left')
                merged_categories.fillna(0, inplace=True)

                # Rename columns for clarity
                merged_categories.rename(columns={'monthly_amount': 'expected', 'amount': 'actual'}, inplace=True)

                # Calculate difference
                merged_categories['difference'] = merged_categories['actual'] - merged_categories['expected']
                merged_categories['percent_diff'] = merged_categories.apply(
                    lambda row: (row['difference'] / row['expected'] * 100) if row['expected'] > 0 else 0,
                    axis=1
                )

                # Sort by expected amount for better visualization
                merged_categories.sort_values('expected', ascending=False, inplace=True)

                # Create horizontal bar chart
                fig, ax = plt.subplots(figsize=(10, max(6, len(merged_categories) * 0.4)))

                # Plot bars
                y = range(len(merged_categories))
                width = 0.35

                # Expected bars
                expected_bars = ax.barh([i - width/2 for i in y], merged_categories['expected'], width, label='Expected', color='blue', alpha=0.7)

                # Actual bars
                actual_bars = ax.barh([i + width/2 for i in y], merged_categories['actual'], width, label='Actual', color='orange', alpha=0.7)

                # Labels and title
                month_name = month_year.strftime('%B %Y')
                ax.set_title(f'Expected vs Actual Spending by Category for {month_name}')
                ax.set_xlabel('Amount ($)')

                # Y-axis labels
                ax.set_yticks(y)
                ax.set_yticklabels(merged_categories['category'])

                ax.legend()

                # Format x-axis as currency
                import matplotlib.ticker as mtick
                fmt = '${x:,.0f}'
                tick = mtick.StrMethodFormatter(fmt)
                ax.xaxis.set_major_formatter(tick)

                # Adjust layout
                plt.tight_layout()

                # Show the plot
                st.pyplot(fig)

                # Summary table
                st.subheader("Category Breakdown")
                st.dataframe(
                    merged_categories,
                    column_config={
                        "category": "Category",
                        "expected": st.column_config.NumberColumn(
                            "Expected",
                            format="$%.2f",
                        ),
                        "actual": st.column_config.NumberColumn(
                            "Actual",
                            format="$%.2f",
                        ),
                        "difference": st.column_config.NumberColumn(
                            "Difference",
                            format="$%.2f",
                        ),
                        "percent_diff": st.column_config.NumberColumn(
                            "% Difference",
                            format="%.1f%%",
                        ),
                    },
                    hide_index=True
                )
        else:
            st.info("No data available for the selected month.")

    # Tab 3: Credit Card Utilization
    with tabs[2]:
        st.subheader("Credit Card Utilization")

        # Get credit card data
        conn = get_db_connection()
        credit_cards = pd.read_sql_query(
            """
            SELECT name, current_balance, credit_limit
            FROM credit_cards
            ORDER BY name
            """,
            conn
        )
        conn.close()

        if not credit_cards.empty:
            # Calculate utilization
            credit_cards['utilization'] = (credit_cards['current_balance'] / credit_cards['credit_limit']) * 100

            # Create bar chart
            fig, ax = plt.subplots(figsize=(10, 6))

            # Define colors based on utilization (green to red)
            def get_color(util_pct):
                if util_pct < 30:
                    return 'green'
                elif util_pct < 50:
                    return 'yellowgreen'
                elif util_pct < 70:
                    return 'orange'
                else:
                    return 'red'

            colors = [get_color(util) for util in credit_cards['utilization']]

            # Plot bars
            bars = ax.bar(credit_cards['name'], credit_cards['utilization'], color=colors, alpha=0.7)

            # Add data labels
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                        f'{height:.1f}%',
                        ha='center', va='bottom', rotation=0)

            # Add warning lines
            ax.axhline(y=30, color='green', linestyle='--', alpha=0.5, label='Good (30%)')
            ax.axhline(y=50, color='orange', linestyle='--', alpha=0.5, label='Warning (50%)')
            ax.axhline(y=70, color='red', linestyle='--', alpha=0.5, label='High (70%)')

            # Labels and title
            ax.set_title('Credit Card Utilization')
            ax.set_ylabel('Utilization (%)')
            ax.set_ylim(0, max(100, credit_cards['utilization'].max() * 1.2))

            # X-axis labels
            plt.xticks(rotation=45, ha='right')

            ax.legend()

            # Adjust layout
            plt.tight_layout()

            # Show the plot
            st.pyplot(fig)

            # Detailed information
            st.subheader("Credit Card Details")
            st.dataframe(
                credit_cards,
                column_config={
                    "name": "Card Name",
                    "current_balance": st.column_config.NumberColumn(
                        "Current Balance",
                        format="$%.2f",
                    ),
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

            # Credit utilization tips
            with st.expander("Credit Utilization Tips"):
                st.write("""
                ### Credit Utilization Tips

                - **Keep utilization below 30%** of your credit limit for the best impact on your credit score.
                - **Pay your statement balance in full** each month to avoid interest charges.
                - **Request credit limit increases** if you consistently stay near the limit.
                - **Consider spreading large purchases** across multiple cards to keep individual card utilization lower.
                - **Pay down high-utilization cards first** to improve your overall credit profile.
                """)
        else:
            st.info("No credit card data available. Add credit cards to see utilization metrics.")

    # Tab 4: Spending by Category
    with tabs[3]:
        st.subheader("Spending by Category")

        # Date range selection
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "From Date",
                value=(datetime.now() - timedelta(days=30)).date(),
                key="vis_category_start_date"
            )
        with col2:
            end_date = st.date_input(
                "To Date",
                value=datetime.now().date(),
                key="vis_category_end_date"
            )

        # Visualization type
        viz_type = st.radio(
            "Visualization Type",
            ["Pie Chart", "Bar Chart"],
            horizontal=True,
            key="vis_category_type"
        )

        # Get transaction data
        conn = get_db_connection()
        transactions = pd.read_sql_query(
            """
            SELECT category, amount
            FROM actual_transactions
            WHERE date BETWEEN ? AND ?
            AND type = 'expense'
            """,
            conn,
            params=[start_date, end_date]
        )
        conn.close()

        if not transactions.empty:
            # Group by category
            category_spending = transactions.groupby('category')['amount'].sum().reset_index()

            # Sort by amount for bar chart
            category_spending.sort_values('amount', ascending=False, inplace=True)

            # Calculate percentage of total
            total_spending = category_spending['amount'].sum()
            category_spending['percentage'] = (category_spending['amount'] / total_spending) * 100

            # Create visualization
            fig, ax = plt.subplots(figsize=(10, 6))

            if viz_type == "Pie Chart":
                # Create pie chart
                wedges, texts, autotexts = ax.pie(
                    category_spending['amount'],
                    labels=None,
                    autopct='',
                    startangle=90,
                    pctdistance=0.85,
                    explode=[0.05 if cat == category_spending['category'].iloc[0] else 0 for cat in category_spending['category']]
                )

                # Create legend with percentages
                legend_labels = [f"{cat} (${amt:.2f}, {pct:.1f}%)" for cat, amt, pct in
                                zip(category_spending['category'], category_spending['amount'], category_spending['percentage'])]

                # Limit legend items if too many
                if len(legend_labels) > 10:
                    # Create an "Other" category for small slices
                    top_categories = category_spending.head(9)
                    other_amount = total_spending - top_categories['amount'].sum()
                    other_percent = (other_amount / total_spending) * 100

                    legend_labels = [f"{cat} (${amt:.2f}, {pct:.1f}%)" for cat, amt, pct in
                                zip(top_categories['category'], top_categories['amount'], top_categories['percentage'])]

                    legend_labels.append(f"Other (${other_amount:.2f}, {other_percent:.1f}%)")

                ax.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))

                # Add center circle to make a donut chart
                centre_circle = plt.Circle((0, 0), 0.70, fc='white')
                fig.gca().add_artist(centre_circle)

                # Add title and total in center
                ax.text(0, 0, f"Total\n${total_spending:,.2f}", ha='center', va='center', fontsize=12)

                # Title
                date_range_str = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
                ax.set_title(f'Spending by Category ({date_range_str})')

                # Equal aspect ratio ensures that pie is drawn as a circle
                ax.set_aspect('equal')
            else:
                # Create horizontal bar chart
                bars = ax.barh(category_spending['category'], category_spending['amount'], color='skyblue')

                # Add data labels
                for bar in bars:
                    width = bar.get_width()
                    label_x_pos = width + total_spending * 0.01
                    ax.text(label_x_pos, bar.get_y() + bar.get_height()/2, f'${width:,.2f}',
                           va='center')

                # Format x-axis as currency
                import matplotlib.ticker as mtick
                fmt = '${x:,.0f}'
                tick = mtick.StrMethodFormatter(fmt)
                ax.xaxis.set_major_formatter(tick)

                # Title and labels
                date_range_str = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
                ax.set_title(f'Spending by Category ({date_range_str})')
                ax.set_xlabel('Amount ($)')

                # Adjust layout
                plt.tight_layout()

            # Show the plot
            st.pyplot(fig)

            # Detailed breakdown
            st.subheader("Category Breakdown")
            st.dataframe(
                category_spending,
                column_config={
                    "category": "Category",
                    "amount": st.column_config.NumberColumn(
                        "Amount",
                        format="$%.2f",
                    ),
                    "percentage": st.column_config.ProgressColumn(
                        "% of Total",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100,
                    ),
                },
                hide_index=True
            )
        else:
            st.info("No expense data available for the selected date range.")

    # Tab 5: Balance Forecast
    with tabs[4]:
        st.subheader("Balance Forecast")

        # Forecast settings
        forecast_months = st.slider("Forecast Months", min_value=1, max_value=12, value=3)

        # Get current bank balance
        conn = get_db_connection()
        bank_accounts = pd.read_sql_query(
            "SELECT id, name, balance FROM bank_accounts ORDER BY name",
            conn
        )

        # Get recurring transactions
        recurring = pd.read_sql_query(
            """
            SELECT description, amount, frequency, type, start_date, end_date, is_active
            FROM recurring_transactions
            WHERE is_active = 1
            """,
            conn,
            parse_dates=["start_date", "end_date"]
        )
        conn.close()

        if not bank_accounts.empty:
            # Calculate current total balance
            total_current_balance = bank_accounts['balance'].sum()

            # Create forecast dates (monthly)
            today = datetime.now().date()
            forecast_start = today.replace(day=1)  # Start of current month
            forecast_dates = []
            forecast_balances = []

            # Current balance is starting point
            current_balance = total_current_balance
            forecast_dates.append(forecast_start)
            forecast_balances.append(current_balance)

            # Generate monthly projections
            for i in range(1, forecast_months + 1):
                # Calculate next month date
                if (forecast_start.month + i) % 12 == 0:
                    next_month = forecast_start.replace(year=forecast_start.year + (forecast_start.month + i) // 12 - 1, month=12)
                else:
                    next_month = forecast_start.replace(year=forecast_start.year + (forecast_start.month + i - 1) // 12, month=(forecast_start.month + i - 1) % 12 + 1)

                # Start with previous month's balance
                next_balance = forecast_balances[-1]

                # Add effect of recurring transactions for this month

                # Process recurring transactions to add their effect
                for _, transaction in recurring.iterrows():
                    # Skip if transaction hasn't started yet
                    if transaction['start_date'] > next_month:
                        continue

                    # Skip if transaction has ended
                    if transaction['end_date'] is not pd.NaT and transaction['end_date'] < next_month:
                        continue

                    # Calculate amount for this month based on frequency
                    frequency = transaction['frequency'].lower()
                    amount = transaction['amount']

                    if frequency == 'monthly':
                        monthly_amount = amount
                    elif frequency == 'semi-monthly':
                        monthly_amount = amount * 2  # Twice per month
                    elif frequency == 'weekly':
                        monthly_amount = amount * 4.33  # Average weeks in a month
                    elif frequency == 'bi-weekly':
                        monthly_amount = amount * 2.17  # Average bi-weekly periods in a month
                    elif frequency == 'quarterly':
                        # Only add if this is a quarter month from the start_date
                        months_diff = ((next_month.year - transaction['start_date'].year) * 12 +
                                       next_month.month - transaction['start_date'].month)
                        if months_diff % 3 == 0:
                            monthly_amount = amount
                        else:
                            monthly_amount = 0
                    elif frequency == 'annually':
                        # Only add if this is the anniversary month
                        if (next_month.month == transaction['start_date'].month):
                            monthly_amount = amount
                        else:
                            monthly_amount = 0
                    elif frequency == 'one-time':
                        # Only count if the one-time payment is in this month
                        one_time_month = transaction['start_date'].replace(day=1)
                        if (next_month.year == one_time_month.year and next_month.month == one_time_month.month):
                            monthly_amount = amount
                        else:
                            monthly_amount = 0
                    else:
                        monthly_amount = amount  # Default to monthly
                    # Apply effect to balance based on type
                    if transaction['type'] == 'income':
                        next_balance += monthly_amount
                    else:  # expense
                        next_balance -= monthly_amount

                forecast_dates.append(next_month)
                forecast_balances.append(next_balance)

            # Create dataframe for visualization
            forecast_df = pd.DataFrame({
                'date': forecast_dates,
                'balance': forecast_balances
            })

            # Format dates for display
            forecast_df['date_str'] = forecast_df['date'].apply(lambda d: d.strftime('%b %Y'))

            # Create line chart
            fig, ax = plt.subplots(figsize=(10, 6))

            # Plot line
            ax.plot(range(len(forecast_df)), forecast_df['balance'], marker='o', linestyle='-', linewidth=2, color='blue')

            # Add data labels
            for i, (_, row) in enumerate(forecast_df.iterrows()):
                ax.text(i, row['balance'] + (max(forecast_balances) - min(forecast_balances)) * 0.02,
                        f"${row['balance']:,.2f}", ha='center')

            # Add zero line
            ax.axhline(y=0, color='red', linestyle='--', alpha=0.5)

            # X-axis labels
            ax.set_xticks(range(len(forecast_df)))
            ax.set_xticklabels(forecast_df['date_str'])

            # Labels and title
            ax.set_xlabel('Month')
            ax.set_ylabel('Projected Balance ($)')
            ax.set_title(f'{forecast_months}-Month Balance Forecast')

            # Format y-axis as currency
            import matplotlib.ticker as mtick
            fmt = '${x:,.0f}'
            tick = mtick.StrMethodFormatter(fmt)
            ax.yaxis.set_major_formatter(tick)

            # Adjust layout
            plt.tight_layout()

            # Show the plot
            st.pyplot(fig)

            # Show the forecast data
            st.subheader("Forecast Details")
            st.dataframe(
                forecast_df[['date_str', 'balance']],
                column_config={
                    "date_str": "Month",
                    "balance": st.column_config.NumberColumn(
                        "Projected Balance",
                        format="$%.2f",
                    ),
                },
                hide_index=True
            )

            # Analysis
            lowest_balance = forecast_df['balance'].min()
            lowest_month = forecast_df.loc[forecast_df['balance'].idxmin(), 'date_str']
            highest_balance = forecast_df['balance'].max()
            highest_month = forecast_df.loc[forecast_df['balance'].idxmax(), 'date_str']
            end_balance = forecast_df['balance'].iloc[-1]

            st.subheader("Forecast Analysis")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Starting Balance", f"${forecast_df['balance'].iloc[0]:,.2f}")
            with col2:
                st.metric("Ending Balance", f"${end_balance:,.2f}",
                         delta=f"${end_balance - forecast_df['balance'].iloc[0]:,.2f}",
                         delta_color="normal" if end_balance >= forecast_df['balance'].iloc[0] else "inverse")
            with col3:
                if lowest_balance < 0:
                    st.metric("Negative Balance Alert", f"${lowest_balance:,.2f} in {lowest_month}", delta="Action needed!", delta_color="inverse")
                else:
                    st.metric("Lowest Balance", f"${lowest_balance:,.2f} in {lowest_month}")

            # Recommendations
            if lowest_balance < 0:
                st.warning("""
                ### ⚠️ Cash Flow Alert

                Your forecast shows a negative balance in the future. Consider:
                - Reducing non-essential expenses
                - Finding additional income sources
                - Adjusting payment timing to better align with income
                - Building an emergency fund when your balance is positive
                """)
            elif end_balance < forecast_df['balance'].iloc[0]:
                st.info("""
                ### 💡 Cash Flow Trending Down

                Your forecast shows a declining balance trend. Consider:
                - Reviewing and reducing unnecessary expenses
                - Seeking ways to increase income
                - Setting up automatic savings to establish an emergency fund
                """)
            else:
                st.success("""
                ### 🎉 Positive Cash Flow

                Your forecast shows a growing balance. Great job! Consider:
                - Setting up automatic transfers to savings or investments
                - Accelerating debt payments
                - Planning for long-term financial goals
                """)
        else:
            st.info("No bank account data available. Add bank accounts to see balance forecasts.")

if __name__ == "__main__":
    main()
