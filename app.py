import streamlit as st

st.set_page_config(
    page_title="Banking Management System",
    page_icon="🏦",
    layout="wide"
)

from database import create_table
import pandas as pd
import matplotlib.pyplot as plt

create_table()

st.title("Banking Management System")

# Create login state if not exists
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


# If NOT logged in → show login
if not st.session_state.logged_in:
    st.subheader("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        import sqlite3

        conn = sqlite3.connect("bank.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM admins WHERE username=? AND password=?",
            (username, password)
        )

        user = cursor.fetchone()

        if user:
            st.session_state.logged_in = True
            st.success("Login Successful")
            st.rerun()
        else:
            st.error("Invalid Credentials")

        conn.close()


# If logged in → show dashboard
else:
    st.sidebar.title("Banking System")
    st.sidebar.caption("Admin Panel")
    st.sidebar.success("Logged in successfully")

    menu = st.sidebar.selectbox(
        "Navigation",
        ["Dashboard", "Customers", "Accounts", "Transactions", "Loans", "Admins"]
    )

    if menu == "Dashboard":

        import sqlite3

        st.title("Banking Dashboard")
        st.caption("Admin Control Panel")

        st.divider()

        conn = sqlite3.connect("bank.db")
        cursor = conn.cursor()

        # Total customers
        cursor.execute("SELECT COUNT(*) FROM customers")
        total_customers = cursor.fetchone()[0]

        # Total accounts
        cursor.execute("SELECT COUNT(*) FROM accounts")
        total_accounts = cursor.fetchone()[0]

        # Total balance
        cursor.execute("SELECT SUM(balance) FROM accounts")
        total_balance = cursor.fetchone()[0]

        if total_balance is None:
            total_balance = 0

        # Total loans
        cursor.execute("SELECT SUM(amount) FROM loans")
        total_loans = cursor.fetchone()[0]

        if total_loans is None:
            total_loans = 0

        conn.close()

        # Top metrics
        col1, col2 = st.columns(2)

        col1.metric(
            "Total Customers",
            total_customers
        )

        col2.metric(
            "Total Accounts",
            total_accounts
        )

        st.divider()

        # Bottom metrics
        col3, col4 = st.columns(2)

        col3.metric(
            "Total Balance",
            f"₹{total_balance}"
        )

        col4.metric(
            "Total Loans",
            f"₹{total_loans}"
        )

        st.divider()

        st.success("System Running Successfully")

        st.subheader("Transaction Analytics")

        # Reconnect DB
        conn = sqlite3.connect("bank.db")
        cursor = conn.cursor()

        # Fetch transaction totals
        cursor.execute("""
        SELECT type, SUM(amount)
        FROM transactions
        GROUP BY type
        """)

        data = cursor.fetchall()

        conn.close()

        # Convert to DataFrame
        df = pd.DataFrame(data, columns=["Type", "Amount"])

        # Create chart
        fig, ax = plt.subplots()

        ax.bar(df["Type"], df["Amount"])

        ax.set_xlabel("Transaction Type")
        ax.set_ylabel("Amount")

        # Show chart
        st.pyplot(fig)

    elif menu == "Customers":
        import sqlite3

        st.title("Customers")

        conn = sqlite3.connect("bank.db")
        cursor = conn.cursor()

        # Add Customer
        st.subheader("Add Customer")

        name = st.text_input("Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")

        if st.button("Add Customer"):
            cursor.execute(
                "INSERT INTO customers (name, email, phone) VALUES (?, ?, ?)",
                (name, email, phone)
            )
            conn.commit()
            st.success("Customer Added")

        # Show Customers
        st.subheader("All Customers")
        search = st.text_input("Search Customer by Name")

        cursor.execute(
            "SELECT * FROM customers WHERE name LIKE ?",
            ('%' + search + '%',)
        )
        data = cursor.fetchall()

        df = pd.DataFrame(
            data,
            columns=["ID", "Name", "Email", "Phone"]
        )

        st.dataframe(df, use_container_width=True)

        conn.close()

    elif menu == "Accounts":
        import sqlite3

        st.title("Accounts")

        conn = sqlite3.connect("bank.db")
        cursor = conn.cursor()

        # Fetch customers
        cursor.execute("SELECT id, name FROM customers")
        customers = cursor.fetchall()

        customer_dict = {f"{name} (ID: {id})": id for id, name in customers}

        st.subheader("Create Account")

        selected_customer = st.selectbox("Select Customer", list(customer_dict.keys()))
        balance = st.number_input("Initial Balance", min_value=0.0)
        account_type = st.selectbox("Account Type", ["Savings", "Current"])

        if st.button("Create Account"):
            customer_id = customer_dict[selected_customer]

            cursor.execute(
                "INSERT INTO accounts (customer_id, balance, account_type) VALUES (?, ?, ?)",
                (customer_id, balance, account_type)
            )
            conn.commit()
            st.success("Account Created")

        # Show accounts
        st.subheader("All Accounts")

        cursor.execute("""
        SELECT accounts.id, customers.name, accounts.balance, accounts.account_type
        FROM accounts
        JOIN customers ON accounts.customer_id = customers.id
        """)

        data = cursor.fetchall()
        st.table(data)

        conn.close()

    elif menu == "Transactions":
        import sqlite3

        st.title("Transactions")

        conn = sqlite3.connect("bank.db")
        cursor = conn.cursor()

        # Fetch accounts
        cursor.execute("""
        SELECT accounts.id, customers.name, accounts.balance
        FROM accounts
        JOIN customers ON accounts.customer_id = customers.id
        """)
        accounts = cursor.fetchall()

        account_dict = {
            f"Acc {acc_id} - {name}": acc_id
            for acc_id, name, balance in accounts
        }

        st.subheader("Make Transaction")

        selected_account = st.selectbox("Select Account", list(account_dict.keys()))

        acc_id = account_dict[selected_account]

        # Fetch latest balance from DB
        cursor.execute("SELECT balance FROM accounts WHERE id=?", (acc_id,))
        current_balance = cursor.fetchone()[0]
        st.info(f"Current Balance: ₹{current_balance}")

        transaction_type = st.selectbox("Type", ["Deposit", "Withdraw"])
        amount = st.number_input("Amount", min_value=0.0)

        if st.button("Submit"):

            if transaction_type == "Deposit":
                new_balance = current_balance + amount

            elif transaction_type == "Withdraw":
                if amount > current_balance:
                    st.error("Insufficient Balance")
                    conn.close()
                    st.stop()
                new_balance = current_balance - amount

            # Update balance
            cursor.execute(
                "UPDATE accounts SET balance=? WHERE id=?",
                (new_balance, acc_id)
            )

            # Insert transaction
            cursor.execute(
                "INSERT INTO transactions (account_id, type, amount) VALUES (?, ?, ?)",
                (acc_id, transaction_type, amount)
            )

            conn.commit()
            st.success("Transaction Successful")

        # Show transactions
        st.subheader("Transaction History")

        cursor.execute("""
        SELECT t.id, c.name, t.type, t.amount,
        datetime(t.date, 'localtime')
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        JOIN customers c ON a.customer_id = c.id
        """)

        data = cursor.fetchall()
        st.table(data)

        conn.close()

    elif menu == "Loans":
        import sqlite3

        st.title("Loans")

        conn = sqlite3.connect("bank.db")
        cursor = conn.cursor()

        # Fetch customers
        cursor.execute("SELECT id, name FROM customers")
        customers = cursor.fetchall()

        customer_dict = {f"{name} (ID: {id})": id for id, name in customers}

        st.subheader("Apply for Loan")

        selected_customer = st.selectbox("Select Customer", list(customer_dict.keys()))
        amount = st.number_input("Loan Amount", min_value=0.0)
        interest = st.number_input("Interest (%)", min_value=0.0)

        if st.button("Apply"):
            customer_id = customer_dict[selected_customer]

            cursor.execute(
                "INSERT INTO loans (customer_id, amount, interest, status) VALUES (?, ?, ?, ?)",
                (customer_id, amount, interest, "Pending")
            )
            conn.commit()
            st.success("Loan Application Submitted")

        # Show loans
        st.subheader("Loan Records")

        cursor.execute("""
        SELECT l.id, c.name, l.amount, l.interest, l.status
        FROM loans l
        JOIN customers c ON l.customer_id = c.id
        """)

        loans = cursor.fetchall()

        for loan in loans:
            loan_id, name, amount, interest, status = loan

            st.write(f"ID: {loan_id} | {name} | ₹{amount} | {interest}% | Status: {status}")

            col1, col2 = st.columns(2)

            # Approve button
            if col1.button(f"Approve {loan_id}"):
                cursor.execute(
                    "UPDATE loans SET status='Approved' WHERE id=?",
                    (loan_id,)
                )
                conn.commit()
                st.rerun()

            # Mark as Paid
            if col2.button(f"Mark Paid {loan_id}"):
                cursor.execute(
                    "UPDATE loans SET status='Paid' WHERE id=?",
                    (loan_id,)
                )
                conn.commit()
                st.rerun()
        
    elif menu == "Admins":
        import sqlite3

        st.title("Admin Management")

        conn = sqlite3.connect("bank.db")
        cursor = conn.cursor()

        st.subheader("Create New Admin")

        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")

        if st.button("Create Admin"):

            try:
                cursor.execute(
                    "INSERT INTO admins (username, password) VALUES (?, ?)",
                    (new_username, new_password)
                )

                conn.commit()

                st.success("New Admin Created")

            except:
                st.error("Username already exists")

        # Show admins
        st.subheader("Existing Admins")

        cursor.execute("SELECT id, username FROM admins")

        admins = cursor.fetchall()

        st.table(admins)

        conn.close()

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()