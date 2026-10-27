# 💰 Personal Expense Tracker and Budget Management System

A simple, fast, and responsive full-stack web application built with **Python (Flask)**, **SQLite**, **HTML5**, **CSS3**, **JavaScript**, and **Chart.js**.

This project helps people track their daily income and expenses, monitor spending habits, set monthly budgets for different categories (like Food, Rent, Shopping), and see interactive charts and analytics.

---

## 📌 Table of Contents
1. [Why This Project? (Problem & Solution)](#-why-this-project)
2. [What Will You Learn & Gain?](#-what-will-you-learn--gain)
3. [How the Project Works (Under the Hood)](#-how-the-project-works)
4. [Step-by-Step Installation & Setup](#-step-by-step-installation--setup)
5. [How to Use the App (Adding Money & Expenses)](#-how-to-use-the-app)
6. [Core Features Explained](#-core-features-explained)
7. [Important Financial Formulas Used](#-important-financial-formulas-used)
8. [Project Folder Structure](#-project-folder-structure)
9. [How to Run Automated Tests](#-how-to-run-automated-tests)
10. [Pushing to Your GitHub Account](#-pushing-to-your-github-account)
11. [Common Interview Questions & Answers](#-common-interview-questions--answers)

---

## ❓ Why This Project?

Most students and working professionals in India struggle with:
- **No visibility of daily spending:** Money arrives at the start of the month (salary or pocket money), and by the 20th, we wonder where all the money went.
- **Budget overflow:** Spending too much on food delivery, UPI snacks, or shopping without realizing it has exceeded our monthly limit.
- **Excel sheet fatigue:** Maintaining Excel sheets on a laptop every day is boring and difficult on mobile phones.

### The Solution:
This web application gives you a clean personal dashboard:
- Shows your **Current Balance** (Net Cash Flow = Total Income − Total Expenses).
- Lets you set an **Overall Monthly Budget** and **Category Budgets** (e.g., ₹10,000 for Rent, ₹5,000 for Food).
- Gives you an **Amber warning at 80%** usage and a **Red alert when you cross 100%**.
- Generates **visual charts** using Chart.js so you can see your money habits at a glance.
- Works offline on your local computer using a lightweight SQLite database (no internet or paid APIs required).

---

## 🎯 What Will You Learn & Gain?

If you are an intermediate developer, student, or preparing for job interviews, this project gives you solid practical experience:

1. **Full-Stack Development with Python Flask:**
   - How to create routes, handle GET and POST requests, and use Jinja2 templates.
2. **Database Design & SQL Security:**
   - Writing clean SQLite tables with primary keys, constraints, and indexes.
   - Using parameterized queries (`?`) to 100% prevent SQL Injection.
3. **No Floating-Point Math Errors (Minor Units):**
   - In financial software, using standard `float` (like `0.1 + 0.2 = 0.30000000000000004`) causes money loss.
   - Here, we store money as **integers in minor units** (paise: ₹100.50 = `10050` paise) and convert only for display. This is how banks and fintech apps build software!
4. **Security & CSRF Protection:**
   - Every POST form has a unique CSRF token stored in the session to stop malicious attacks.
5. **Interactive UI & Charts:**
   - Chart.js integration with dynamic theme switching (Light Mode / Dark Mode).
6. **Resume Value:**
   - Demonstrates complete end-to-end knowledge: backend, database, client validation, testing, and modern UI.

---

## 🧠 How the Project Works (Architecture)

Here is the simple data flow when you use the app:

```
[User clicks "Add Transaction" in Browser]
                 │
                 ▼
[Frontend: Form validates amount > 0, dynamic category dropdown (Food, Salary, etc.)]
                 │  (HTTP POST with CSRF Token)
                 ▼
[Backend: app.py receives data -> validators.py validates fields on server]
                 │
                 ▼
[expense_manager.py converts ₹ to paise & executes parameterized SQL]
                 │
                 ▼
[SQLite: expense_tracker.db saves the transaction securely]
                 │
                 ▼
[Dashboard auto-calculates Balance, Budget % and updates Chart.js charts]
```

---

## 💻 Step-by-Step Installation & Setup

You can run this project in **5 minutes** on any Windows, Mac, or Linux computer.

### Step 1: Open the Project in VS Code
1. Open **Visual Studio Code**.
2. Click **File > Open Folder...** and select this project directory.

### Step 2: Open Terminal in VS Code
Press `Ctrl + ` ` (backtick) or go to **Terminal > New Terminal**.

### Step 3: Create a Virtual Environment (Recommended)
**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(If you see an execution policy error in PowerShell, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and then run the activate command again).*

**On Windows (Command Prompt - CMD):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**On Mac / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```
*(Only Flask is required; SQLite and datetime come built-in with Python!)*

### Step 5: (Optional) Seed Sample Demo Records
To instantly see the charts filled with realistic Indian Rupee transactions (Salary, Groceries, Rent, UPI expenses):
```bash
python seed_demo_data.py
```

### Step 6: Start the Application!
```bash
python app.py
```

You will see:
```text
Personal Expense Tracker starting at http://127.0.0.1:5000
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

Open your browser and visit: **http://127.0.0.1:5000**

---

## 💵 How to Use the App (Adding Money & Expenses)

### 1. Adding Income (Money Coming In):
1. Click **Add Transaction** in the sidebar or top bar.
2. Select **Income** (green button). Notice how the category dropdown automatically switches to income categories like **Salary, Freelancing, Business, Scholarship, Investment Income**.
3. Choose the **Date**, enter the **Amount** (e.g. `50000`), choose **Payment Method** (e.g. `Bank Transfer`), and enter a description (e.g. "Monthly Salary").
4. Click **Save Transaction**.
5. Your **Current Balance** and **Total Income** on the Dashboard immediately increase!

### 2. Adding Expenses (Money Going Out):
1. Click **Add Transaction**.
2. Select **Expense** (red button). The category dropdown switches to **Food, Rent, Utilities, Transportation, Shopping, Healthcare, etc.**
3. Enter the amount (e.g. `1200`), select **UPI**, and write "Supermarket groceries".
4. Click **Save Transaction**.
5. Your dashboard expenses increase, your balance adjusts, and your category doughnut chart updates instantly!

### 3. Setting Monthly and Category Budgets:
1. Go to **Budget Management** in the sidebar.
2. Set your **Total Monthly Spending Limit** (e.g. ₹40,000).
3. In the right-hand box, set specific limits for categories (e.g. Food: ₹8,000, Shopping: ₹5,000).
4. Watch the progress bar:
   - **Green/Teal:** Safe (< 80% used).
   - **Amber:** Warning (80% – 100% used).
   - **Red Alert:** Exceeded (> 100% used).

### 4. Viewing History & Filtering:
1. Go to **Transaction History**.
2. Search by keyword (e.g. "fuel"), filter by Income/Expense, or select a date range.
3. Edit any mistake with the **Edit** button.
4. Delete any unwanted transaction with the safe **Delete** modal.
5. Click **Export to CSV** to download an Excel-compatible spreadsheet of all matching transactions.

---

## 📊 Important Financial Formulas Used

All calculations are executed in Python with database records:

1. **Net Cash Flow (Current Balance):**
   $$\text{Balance} = \text{Total Income} - \text{Total Expenses}$$

2. **Remaining Budget:**
   $$\text{Remaining} = \text{Monthly Budget Limit} - \text{Eligible Monthly Expenses}$$

3. **Budget Utilization Percentage:**
   $$\text{Utilization \%} = \left(\frac{\text{Eligible Monthly Expenses}}{\text{Monthly Budget Limit}}\right) \times 100$$
   *(If budget is 0, it safely returns 0% without crashing).*

4. **Savings Rate:**
   $$\text{Savings Rate \%} = \left(\frac{\text{Net Cash Flow}}{\text{Total Income}}\right) \times 100 \quad (\text{only when Total Income} > 0)$$

---

## 📁 Project Folder Structure

```text
Personal Expense Tracker and Budget Management System/
│
├── app.py                  # Main Flask routes, CSRF middleware & Jinja2 filters
├── database.py             # SQLite connection, tables schema & indexes
├── expense_manager.py      # Core business logic: queries, calculations, CSV export
├── validators.py           # Validates input, checks positive amounts, handles paise conversion
├── seed_demo_data.py       # Helper script to populate demo data
├── requirements.txt        # Python library dependencies
├── README.md               # Complete documentation
├── .gitignore              # Files to exclude from git (databases, cache, venv)
│
├── templates/              # HTML Templates (Jinja2)
│   ├── base.html           # Main master layout (Sidebar, Navbar, Theme Toggle, Modals)
│   ├── dashboard.html      # Overview summary cards + Chart.js visual charts
│   ├── add_transaction.html# Add Income/Expense form with dynamic categories
│   ├── transactions.html   # Search, filter, pagination, and CSV export
│   ├── edit_transaction.html# Pre-filled edit form
│   ├── budgets.html        # Monthly spending limits & category progress bars
│   ├── reports.html        # Analytics, daily/weekly breakdowns, 12-month trends
│   ├── settings.html       # Change currency, default budget, view database info
│   └── 404.html            # Error page
│
├── static/                 # Static Assets
│   ├── css/
│   │   └── style.css       # Clean modern CSS with Light and Dark mode variables
│   ├── js/
│   │   ├── main.js         # Theme toggle, category switcher, modal logic
│   │   └── charts.js       # Chart.js rendering & theme auto-adapt
│   └── images/
│
├── data/
│   ├── .gitkeep            # Keeps folder in git
│   └── expense_tracker.db  # SQLite database (auto-generated)
│
└── tests/                  # Automated Unit & Route Tests
    ├── test_transactions.py# 12+ tests for CRUD, calculations, CSV, routes
    └── test_budgets.py     # 5+ tests for utilization, warnings, savings rate
```

---

## 🧪 How to Run Automated Tests

To verify that all calculations, routes, and security checks are 100% working, run Python's built-in test runner:

```bash
python -m unittest discover tests -v
```

All 17 tests will run in temporary in-memory databases without touching your real data and show:
```text
Ran 17 tests in 1.1s
OK
```

---

## 🚀 Pushing to Your GitHub Account

Run these commands in your VS Code terminal to upload this project to your GitHub profile:

```bash
# 1. Initialize git
git init

# 2. Stage all files
git add .

# 3. Create your first commit
git commit -m "feat: complete Personal Expense Tracker and Budget Management System"

# 4. Set main branch
git branch -M main

# 5. Link to your GitHub repo (replace with your GitHub repository link)
git remote add origin https://github.com/<your-github-username>/personal-expense-tracker.git

# 6. Push code to GitHub
git push -u origin main
```

---

## 💡 Common Interview Questions & Answers

If you are asked about this project in an interview or college viva:

**Q1: Why did you use SQLite instead of MySQL or PostgreSQL?**  
*Answer:* "For a personal desktop/local expense tracker, SQLite is lightweight, serverless, zero-configuration, and stores everything in a single portable file (`expense_tracker.db`). If needed in the future for multiple cloud users, the data access layer in `expense_manager.py` can easily be adapted to PostgreSQL."

**Q2: How do you handle financial precision and currency in your database?**  
*Answer:* "I avoid standard floating-point representation because binary floating points can introduce rounding errors. Instead, I store all amounts as **integer minor units** (paise: ₹1 = 100 paise). The application converts values to standard currency decimals strictly during display and input validation."

**Q3: How did you secure your application against common vulnerabilities?**  
*Answer:*  
1. **SQL Injection:** I used parameterized queries (`cursor.execute(sql, (param,))`) exclusively.  
2. **CSRF:** All state-modifying requests (POST) require a valid CSRF token generated in the user's session.  
3. **XSS:** Output is escaped using Jinja2 templates.  
4. **Validation:** Server-side validation rejects negative amounts, zero amounts, and invalid dates even if someone bypasses client-side checks.

**Q4: How do the Chart.js graphs update when data changes?**  
*Answer:* "When transactions are added, edited, or deleted, Flask recalculates the financial summaries and injects the updated data into the Jinja2 template. The JavaScript charts automatically re-render with the latest figures and adapt grid colors based on Light or Dark theme."

---

## 📜 License
This project is open-source and free to use for personal, educational, and portfolio purposes under the MIT License.
