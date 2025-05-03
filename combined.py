import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import requests
import json
from typing import Dict, Any
import logging

class TransactionProcessor:
    def __init__(self, csv_path: str, api_url: str):
        self.api_url = api_url
        self.required_columns = [
            "owner_user_id",
            "amount",
            "updated_timestamp",
            "geolocation_latitude",
            "geolocation_longitude",
            "merchant_category_code"
        ]
        self.df = self.load_csv(csv_path)
        self.current_row_index = 0  # Keep track of current transaction

    def load_csv(self, csv_path: str) -> pd.DataFrame:
        try:
            df = pd.read_csv(csv_path)
            missing_cols = set(self.required_columns) - set(df.columns)
            if missing_cols:
                raise ValueError(f"Missing required columns in CSV: {missing_cols}")
            return df[self.required_columns]
        except Exception as e:
            logging.error(f"Error loading CSV: {str(e)}")
            raise

    def prepare_payload(self, row: pd.Series) -> Dict[str, Any]:
        return {
            "owner_user_id": int(row['owner_user_id']),
            "amount": float(row['amount']),
            "updated_timestamp": row['updated_timestamp'],
            "geolocation_latitude": float(row['geolocation_latitude']),
            "geolocation_longitude": float(row['geolocation_longitude']),
            "merchant_category_code": str(row['merchant_category_code'])
        }

    def get_next_transaction(self) -> Dict[str, Any]:
        """Get next transaction from CSV"""
        if self.current_row_index < len(self.df):
            row = self.df.iloc[self.current_row_index]
            payload = self.prepare_payload(row)
            self.current_row_index += 1
            return payload
        return None

    def send_transaction(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed: {str(e)}")
            return {"error": str(e)}

class TransactionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Transaction Monitor")
        self.root.geometry("800x600")

        # Initialize transaction processor
        self.processor = TransactionProcessor(
            csv_path="big_data.csv",  # Replace with your CSV path
            api_url="http://192.168.248.224:5000/predict"  # Replace with your API URL
        )

        # Initialize transactions list
        self.transactions = []
        self.create_widgets()

    def create_widgets(self):
        # Create button frame
        button_frame = tk.Frame(self.root)
        button_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Add buttons
        self.process_button = tk.Button(
            button_frame, 
            text="Process Next Transaction", 
            command=self.process_next_transaction
        )
        self.process_button.pack(side=tk.LEFT, padx=5)

        # Create transaction list
        self.tree = ttk.Treeview(
            self.root, 
            columns=('Date', 'ID', 'Amount', 'Status', 'ML Decision'),
            show='headings'
        )
        
        # Configure column widths
        self.tree.column('Date', width=150)
        self.tree.column('ID', width=100)
        self.tree.column('Amount', width=100)
        self.tree.column('Status', width=100)
        self.tree.column('ML Decision', width=150)
        
        # Define columns
        self.tree.heading('Date', text='Date')
        self.tree.heading('ID', text='User ID')
        self.tree.heading('Amount', text='Amount')
        self.tree.heading('Status', text='Status')
        self.tree.heading('ML Decision', text='ML Decision')

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        # Pack widgets
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add right-click menu
        self.create_context_menu()

    def process_next_transaction(self):
        """Process next transaction from CSV"""
        try:
            # Get next transaction
            transaction = self.processor.get_next_transaction()
            if not transaction:
                messagebox.showinfo("Info", "No more transactions to process!")
                return

            # Send to ML model
            response = self.processor.send_transaction(transaction)
            
            if "error" in response:
                messagebox.showerror("Error", f"API Error: {response['error']}")
                return

            # Check if transaction is suspicious
            is_suspicious = response.get("ae_action") == "warn"
            
            if is_suspicious:
                # Get reasons from response
                reasons = response.get("ae_reasons", "No specific reasons provided")
                
                # Create detailed message
                message = (
                    f"Transaction Details:\n"
                    f"------------------------\n"
                    f"User ID: {transaction['owner_user_id']}\n"
                    f"Amount: ${transaction['amount']:.2f}\n"
                    f"Date: {transaction['updated_timestamp']}\n\n"
                    f"This transaction appears suspicious for the following reasons:\n"
                    f"------------------------\n"
                    f"{reasons}\n\n"
                    f"Do you want to proceed with this transaction?"
                )

                # Show warning dialog
                user_confirm = self.show_warning_dialog(
                    title="⚠️ Suspicious Transaction",
                    message=message
                )
                
                if not user_confirm:
                    self.add_to_tree(
                        transaction, 
                        "Rejected", 
                        "Suspicious",
                        reasons
                    )
                    return

            # Add to transaction list
            self.add_to_tree(
                transaction, 
                "Approved", 
                "Suspicious" if is_suspicious else "Normal",
                response.get("ae_reasons", "") if is_suspicious else ""
            )

        except Exception as e:
            messagebox.showerror("Error", f"Processing failed: {str(e)}")
            logging.error(f"Transaction processing error: {str(e)}")

    def show_warning_dialog(self, title, message):
        """Custom dialog for suspicious transaction warning"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("500x400")
        
        # Make dialog modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Configure dialog
        dialog.configure(bg='#f0f0f0')
        dialog.grid_columnconfigure(0, weight=1)
        
        # Add warning icon
        warning_label = tk.Label(
            dialog,
            text="⚠️",
            font=("Arial", 48),
            bg='#f0f0f0'
        )
        warning_label.grid(row=0, pady=10)
        
        # Add scrolled text widget for message
        text_widget = tk.Text(
            dialog,
            wrap=tk.WORD,
            width=50,
            height=12,
            font=("Arial", 10),
            bg='white'
        )
        text_widget.grid(row=1, padx=20, pady=10, sticky='nsew')
        text_widget.insert('1.0', message)
        text_widget.configure(state='disabled')
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(dialog, orient='vertical', command=text_widget.yview)
        scrollbar.grid(row=1, column=1, sticky='ns')
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Button frame
        button_frame = tk.Frame(dialog, bg='#f0f0f0')
        button_frame.grid(row=2, pady=20)
        
        result = tk.BooleanVar()
        
        # Proceed button
        proceed_btn = tk.Button(
            button_frame,
            text="Proceed",
            command=lambda: self.close_dialog(dialog, result, True),
            bg='#4CAF50',
            fg='white',
            width=15
        )
        proceed_btn.pack(side=tk.LEFT, padx=10)
        
        # Reject button
        reject_btn = tk.Button(
            button_frame,
            text="Reject",
            command=lambda: self.close_dialog(dialog, result, False),
            bg='#f44336',
            fg='white',
            width=15
        )
        reject_btn.pack(side=tk.LEFT, padx=10)
        
        # Wait for user response
        dialog.wait_window()
        return result.get()

    def close_dialog(self, dialog, result_var, value):
        """Helper function to close dialog and set result"""
        result_var.set(value)
        dialog.destroy()

    def add_to_tree(self, transaction: Dict[str, Any], status: str, ml_decision: str, reasons: str = ""):
        """Add transaction to treeview with reasons"""
        # Add main transaction row
        item = self.tree.insert('', 0, values=(
            transaction['updated_timestamp'],
            transaction['owner_user_id'],
            f"${transaction['amount']:.2f}",
            status,
            ml_decision
        ))
        
        # If there are reasons, add them as a child row
        if reasons:
            self.tree.insert(item, tk.END, values=(
                "Reasons:", reasons, "", "", ""
            ))

    def create_context_menu(self):
        """Create right-click context menu"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="View Details", command=self.show_transaction_details)
        
        self.tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        """Show context menu on right-click"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def show_transaction_details(self):
        """Show detailed view of selected transaction"""
        selected_item = self.tree.selection()
        if not selected_item:
            return
            
        values = self.tree.item(selected_item)['values']
        if not values:
            return
            
        details_window = tk.Toplevel(self.root)
        details_window.title("Transaction Details")
        details_window.geometry("400x300")
        
        text_widget = tk.Text(details_window, wrap=tk.WORD, width=40, height=15)
        text_widget.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        details_text = (
            f"Date: {values[0]}\n"
            f"User ID: {values[1]}\n"
            f"Amount: {values[2]}\n"
            f"Status: {values[3]}\n"
            f"ML Decision: {values[4]}\n"
        )
        
        # Add reasons if available
        child_items = self.tree.get_children(selected_item)
        if child_items:
            reasons = self.tree.item(child_items[0])['values'][1]
            details_text += f"\nReasons:\n{reasons}"
        
        text_widget.insert('1.0', details_text)
        text_widget.configure(state='disabled')

def main():
    # Set up logging
    logging.basicConfig(
        filename='transaction_app.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Create and run app
    root = tk.Tk()
    app = TransactionApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()