from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Create the database if it doesn't exist
def init_db():
    print("Initializing the database...")
    try:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            try:
                with open('database.sql', 'r') as f:
                    sql_script = f.read()
                cursor.executescript(sql_script)
                conn.commit()
                print("Database initialized successfully.")
            except Exception as e:
                print(f"Error executing SQL script: {e}")
    except Exception as e:
        print(f"Error initializing the database: {e}")

# Route for homepage
@app.route('/')
def index():
    print("Fetching data for homepage...")

    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        try:
            # Fetch all expenses
            cursor.execute('SELECT * FROM expenses ORDER BY date DESC')
            expenses = cursor.fetchall()
        except Exception as e:
            print(f"Error fetching expenses: {e}")
            expenses = []

        # Get all unique categories
        cursor.execute('SELECT DISTINCT category FROM expenses')
        categories = [row[0] for row in cursor.fetchall()]

        # Calculate total expenses
        total_expenses = sum(exp[2] for exp in expenses)

        # Prepare data for the chart (category and corresponding total amounts)
        category_amounts = {category: 0 for category in categories}
        for exp in expenses:
            category_amounts[exp[1]] += exp[2]

        # Ensure the order of categories and amounts matches
        chart_categories = list(category_amounts.keys())
        chart_amounts = list(category_amounts.values())

    return render_template(
        'index.html',
        expenses=expenses,
        total=total_expenses,
        categories=categories,
        chart_categories=chart_categories,
        chart_amounts=chart_amounts
    )

# Route to filter expenses
@app.route('/filter', methods=['GET'])
def filter_expenses():
    category = request.args.get('category', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    print(f"Filtering with category: {category}, start_date: {start_date}, end_date: {end_date}")

    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        try:
            # Build SQL query dynamically based on filters
            query = 'SELECT * FROM expenses WHERE 1=1'
            params = []
            if category:
                query += ' AND category LIKE ?'
                params.append(f'%{category}%')
            if start_date:
                query += ' AND date >= ?'
                params.append(start_date)
            if end_date:
                query += ' AND date <= ?'
                params.append(end_date)

            cursor.execute(query, params)
            expenses = cursor.fetchall()
        except Exception as e:
            print(f"Error filtering expenses: {e}")
            expenses = []

        # Calculate total expenses for filtered results
        total_expenses = sum(exp[2] for exp in expenses)

        # Get all unique categories
        cursor.execute('SELECT DISTINCT category FROM expenses')
        categories = [row[0] for row in cursor.fetchall()]

        # Prepare data for the chart
        category_amounts = {category: 0 for category in categories}
        for exp in expenses:
            category_amounts[exp[1]] += exp[2]

        # Ensure the order of categories and amounts matches
        chart_categories = list(category_amounts.keys())
        chart_amounts = list(category_amounts.values())

    return render_template(
        'index.html',
        expenses=expenses,
        total=total_expenses,
        categories=categories,
        chart_categories=chart_categories,
        chart_amounts=chart_amounts
    )

# Route to add expense
@app.route('/add', methods=['POST'])
def add_expense():
    category = request.form['category']
    amount = float(request.form['amount'])
    date = request.form['date']

    try:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO expenses (category, amount, date) VALUES (?, ?, ?)', (category, amount, date))
            conn.commit()
            print(f"Added expense: {category}, {amount}, {date}")
    except Exception as e:
        print(f"Error adding expense: {e}")

    return redirect('/')

# Route to edit expense
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_expense(id):
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()

        if request.method == 'POST':
            category = request.form['category']
            amount = request.form['amount']
            date = request.form['date']

            try:
                cursor.execute("UPDATE expenses SET category=?, amount=?, date=? WHERE id=?", (category, amount, date, id))
                conn.commit()
                print(f"Updated expense ID {id}: {category}, {amount}, {date}")
            except Exception as e:
                print(f"Error updating expense: {e}")

            return redirect(url_for('index'))

        cursor.execute("SELECT * FROM expenses WHERE id=?", (id,))
        expense = cursor.fetchone()

    return render_template('edit_expense.html', expense=expense)

# Route to delete expense
@app.route('/delete/<int:id>', methods=['GET'])
def delete_expense(id):
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()

        try:
            # Delete the selected expense
            cursor.execute("DELETE FROM expenses WHERE id=?", (id,))
            conn.commit()
            print(f"Deleted expense with ID: {id}")

            # Reset the primary key sequence
            cursor.execute("""
                UPDATE sqlite_sequence 
                SET seq = (SELECT MAX(id) FROM expenses) 
                WHERE name = 'expenses'
            """)
            conn.commit()

            # Reorganize IDs if needed
            cursor.execute("SELECT id FROM expenses ORDER BY id ASC")
            rows = cursor.fetchall()
            for idx, row in enumerate(rows, start=1):
                cursor.execute("UPDATE expenses SET id = ? WHERE id = ?", (idx, row[0]))
            conn.commit()

            # Reset the primary key sequence again
            cursor.execute("""
                UPDATE sqlite_sequence 
                SET seq = (SELECT MAX(id) FROM expenses) 
                WHERE name = 'expenses'
            """)
            conn.commit()

        except Exception as e:
            print(f"Error deleting expense: {e}")

    return redirect('/')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
