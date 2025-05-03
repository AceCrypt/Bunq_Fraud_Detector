Bunq Hackathon - Transaction Fraud Detection UI 🔒
Project Overview 🎯
A desktop application built during the Bunq Hackathon that provides a user interface for monitoring and reviewing potentially fraudulent transactions. The application connects to a Machine Learning model via REST API to analyze transactions and alerts users when suspicious activity is detected.

Features ⭐
Real-time transaction processing and fraud detection
Interactive UI for reviewing suspicious transactions
Detailed transaction history with ML model decisions
Custom warning dialogs with detailed fraud detection reasoning
Transaction details view with right-click context menu
Chronological transaction display (newest first)
Automatic logging of all activities
Technical Stack 💻
Python 3.x
Tkinter (UI Framework)
Pandas (Data Processing)
Requests (API Communication)
Installation 🚀
1. Clone the repository
BASH

git clone https://github.com/your-username/bunq-hackathon.git
cd bunq-hackathon
2. Install required packages
BASH

pip install -r requirements.txt
3. Configure the application
Update the CSV path in main.py
Set the correct API endpoint URL
Usage 📖
1. Start the application
BASH

python main.py
2. Process transactions
Click "Process Next Transaction" to analyze the next transaction
Review suspicious transaction warnings when they appear
Choose to proceed or reject suspicious transactions
View transaction history in the main window
3. View transaction details
Right-click any transaction for additional details
Expand suspicious transactions to view ML model reasoning
Data Format 📋
Required CSV Columns
Python

required_columns = [
    "owner_user_id",
    "amount",
    "updated_timestamp",
    "geolocation_latitude",
    "geolocation_longitude",
    "merchant_category_code"
]
API Response Format
JSON

{
    "ae_action": "warn",  // or "normal"
    "ae_reasons": "Detailed reasons for suspicious activity"
}
Features in Detail 🔍
Transaction Processing
Reads transactions from CSV file
Sends transaction data to ML model via API
Processes ML model responses
Updates UI with results
User Interface
Clean and intuitive design
Transaction history table
Warning dialogs for suspicious transactions
Detailed transaction view
Right-click context menu
Error Handling
API communication error handling
Data validation
Comprehensive error logging
User-friendly error messages
Logging 📝
The application maintains detailed logs in transaction_app.log, including:

Transaction processing events
API communication
Error messages
User actions
Contributing 🤝
This project was created during the Bunq Hackathon. For contributions:

Fork the repository
Create a feature branch
Commit your changes
Push to the branch
Create a Pull Request
License 📄
[Your chosen license]

Acknowledgments 🙏
Bunq for organizing the hackathon
[Any other acknowledgments]
Contact 📧
[Your contact information]

Screenshots 📸
[Add screenshots of your application here]

Future Improvements 🚀
Add batch processing capability
Implement transaction search/filter
Add export functionality
Enhance visualization of transaction patterns
Add user authentication
Implement transaction categories
Add statistical analysis dashboard
This project was developed as part of the Bunq Hackathon [Year] 🏆


Requirements.txt 📋

pandas==2.0.0
requests==2.28.2
tkinter

Project Structure 📁

bunq-hackathon/
│
├── main.py                  # Main application file
├── requirements.txt         # Project dependencies
├── transaction_app.log      # Application logs
├── README.md               # Project documentation
│
└── data/
    └── transactions.csv     # Sample transaction data
Made with ❤️ during Bunq Hackathon
