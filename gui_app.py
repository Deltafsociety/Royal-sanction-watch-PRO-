"""
GUI Application for Comprehensive Sanction Checker
Provides both single entity and bulk checking interfaces
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import pandas as pd
import os
from datetime import datetime, timedelta
from typing import List, Dict
import json

from sanction_checker import SanctionChecker, SanctionMatch

class SanctionCheckerGUI:
    """Main GUI application for sanction checking"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Royal Sanction Watch")
        self.root.geometry("1200x800")
        
        # Initialize sanction checker
        self.checker = SanctionChecker()
        
        # Queue for thread-safe GUI updates
        self.update_queue = queue.Queue()
        
        # Setup GUI
        self.setup_gui()
        self.setup_styles()
        
        # Start update loop
        self.check_queue()
    
    def setup_styles(self):
        """Setup custom styles for the GUI"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Warning.TLabel', foreground='orange')
        style.configure('Error.TLabel', foreground='red')
    
    def setup_gui(self):
        """Setup the main GUI layout"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.single_tab = ttk.Frame(self.notebook)
        self.bulk_tab = ttk.Frame(self.notebook)
        self.results_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.single_tab, text="Single Check")
        self.notebook.add(self.bulk_tab, text="Bulk Check")
        self.notebook.add(self.results_tab, text="Results")
        self.notebook.add(self.settings_tab, text="Settings")
        
        # Setup each tab
        self.setup_single_tab()
        self.setup_bulk_tab()
        self.setup_results_tab()
        self.setup_settings_tab()
    
    def setup_single_tab(self):
        """Setup the single entity check tab"""
        # Title
        title_label = ttk.Label(self.single_tab, text="Single Entity Sanction Check", style='Title.TLabel')
        title_label.pack(pady=10)
        
        # Input frame
        input_frame = ttk.LabelFrame(self.single_tab, text="Entity Information", padding=10)
        input_frame.pack(fill='x', padx=10, pady=5)
        
        # Entity name
        ttk.Label(input_frame, text="Entity Name:").grid(row=0, column=0, sticky='w', pady=5)
        self.entity_name_var = tk.StringVar()
        self.entity_name_entry = ttk.Entry(input_frame, textvariable=self.entity_name_var, width=50)
        self.entity_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        
        # Entity type
        ttk.Label(input_frame, text="Entity Type:").grid(row=1, column=0, sticky='w', pady=5)
        self.entity_type_var = tk.StringVar(value="auto")
        entity_type_combo = ttk.Combobox(input_frame, textvariable=self.entity_type_var, 
                                       values=["auto", "vessel", "person", "company"], 
                                       state="readonly", width=20)
        entity_type_combo.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        # Configure grid weights
        input_frame.columnconfigure(1, weight=1)
        
        # Buttons frame
        button_frame = ttk.Frame(self.single_tab)
        button_frame.pack(pady=10)
        
        self.check_button = ttk.Button(button_frame, text="Check Entity", command=self.check_single_entity)
        self.check_button.pack(side='left', padx=5)
        
        self.clear_button = ttk.Button(button_frame, text="Clear", command=self.clear_single_form)
        self.clear_button.pack(side='left', padx=5)
        
        # Progress bar
        self.single_progress = ttk.Progressbar(self.single_tab, mode='indeterminate')
        self.single_progress.pack(fill='x', padx=10, pady=5)
        
        # Results frame
        results_frame = ttk.LabelFrame(self.single_tab, text="Results", padding=10)
        results_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Results text
        self.single_results_text = scrolledtext.ScrolledText(results_frame, height=15)
        self.single_results_text.pack(fill='both', expand=True)
    
    def setup_bulk_tab(self):
        """Setup the bulk check tab"""
        # Title
        title_label = ttk.Label(self.bulk_tab, text="Bulk Entity Sanction Check", style='Title.TLabel')
        title_label.pack(pady=10)
        
        # File input frame
        file_frame = ttk.LabelFrame(self.bulk_tab, text="Input File", padding=10)
        file_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(file_frame, text="Select File:").grid(row=0, column=0, sticky='w', pady=5)
        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=60)
        file_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        
        browse_button = ttk.Button(file_frame, text="Browse", command=self.browse_file)
        browse_button.grid(row=0, column=2, padx=5, pady=5)
        
        # File format info
        format_label = ttk.Label(file_frame, text="Supported formats: Excel (.xlsx, .xls), CSV (.csv)", 
                               font=('Arial', 9))
        format_label.grid(row=1, column=0, columnspan=3, sticky='w', pady=5)
        
        file_frame.columnconfigure(1, weight=1)
        
        # Options frame
        options_frame = ttk.LabelFrame(self.bulk_tab, text="Options", padding=10)
        options_frame.pack(fill='x', padx=10, pady=5)
        
        # Column selection
        ttk.Label(options_frame, text="Name Column:").grid(row=0, column=0, sticky='w', pady=5)
        self.name_column_var = tk.StringVar(value="name")
        name_column_entry = ttk.Entry(options_frame, textvariable=self.name_column_var, width=20)
        name_column_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        
        ttk.Label(options_frame, text="Type Column (optional):").grid(row=0, column=2, sticky='w', pady=5, padx=(20,0))
        self.type_column_var = tk.StringVar(value="type")
        type_column_entry = ttk.Entry(options_frame, textvariable=self.type_column_var, width=20)
        type_column_entry.grid(row=0, column=3, padx=5, pady=5, sticky='w')
        
        # Output format
        ttk.Label(options_frame, text="Output Format:").grid(row=1, column=0, sticky='w', pady=5)
        self.output_format_var = tk.StringVar(value="excel")
        output_format_combo = ttk.Combobox(options_frame, textvariable=self.output_format_var,
                                         values=["excel", "csv", "json"], state="readonly", width=20)
        output_format_combo.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        # Buttons frame
        button_frame = ttk.Frame(self.bulk_tab)
        button_frame.pack(pady=10)
        
        self.bulk_check_button = ttk.Button(button_frame, text="Start Bulk Check", command=self.start_bulk_check)
        self.bulk_check_button.pack(side='left', padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_bulk_check, state='disabled')
        self.stop_button.pack(side='left', padx=5)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(self.bulk_tab, text="Progress", padding=10)
        progress_frame.pack(fill='x', padx=10, pady=5)
        
        self.bulk_progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.bulk_progress.pack(fill='x', pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="Ready to start")
        self.progress_label.pack()
        
        # Log frame
        log_frame = ttk.LabelFrame(self.bulk_tab, text="Log", padding=10)
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.bulk_log_text = scrolledtext.ScrolledText(log_frame, height=10)
        self.bulk_log_text.pack(fill='both', expand=True)
    
    def setup_results_tab(self):
        """Setup the results tab"""
        # Title
        title_label = ttk.Label(self.results_tab, text="Check Results", style='Title.TLabel')
        title_label.pack(pady=10)
        
        # Results tree
        columns = ("Entity", "Type", "Sanction List", "Match Type", "Confidence", "Status")
        self.results_tree = ttk.Treeview(self.results_tab, columns=columns, show='headings', height=20)
        
        # Configure columns
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=150)
        
        # Scrollbars
        tree_scroll_y = ttk.Scrollbar(self.results_tab, orient='vertical', command=self.results_tree.yview)
        tree_scroll_x = ttk.Scrollbar(self.results_tab, orient='horizontal', command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        
        # Pack tree and scrollbars
        self.results_tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        tree_scroll_y.pack(side='right', fill='y')
        tree_scroll_x.pack(side='bottom', fill='x')
        
        # Buttons frame
        button_frame = ttk.Frame(self.results_tab)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Export Results", command=self.export_results).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Clear Results", command=self.clear_results).pack(side='left', padx=5)
        ttk.Button(button_frame, text="View Details", command=self.view_details).pack(side='left', padx=5)
    
    def setup_settings_tab(self):
        """Setup the settings tab"""
        # Title
        title_label = ttk.Label(self.settings_tab, text="Settings", style='Title.TLabel')
        title_label.pack(pady=10)
        
        # Settings frame
        settings_frame = ttk.LabelFrame(self.settings_tab, text="Configuration", padding=10)
        settings_frame.pack(fill='x', padx=10, pady=5)
        
        # Cache settings
        ttk.Label(settings_frame, text="Cache Duration (hours):").grid(row=0, column=0, sticky='w', pady=5)
        self.cache_duration_var = tk.StringVar(value="24")
        cache_entry = ttk.Entry(settings_frame, textvariable=self.cache_duration_var, width=10)
        cache_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        
        # Similarity threshold
        ttk.Label(settings_frame, text="Similarity Threshold:").grid(row=1, column=0, sticky='w', pady=5)
        self.similarity_threshold_var = tk.StringVar(value="0.7")
        similarity_entry = ttk.Entry(settings_frame, textvariable=self.similarity_threshold_var, width=10)
        similarity_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        # Buttons
        button_frame = ttk.Frame(self.settings_tab)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Save Settings", command=self.save_settings).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Clear Cache", command=self.clear_cache).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Test Connection", command=self.test_connection).pack(side='left', padx=5)
    
    def check_single_entity(self):
        """Check a single entity"""
        entity_name = self.entity_name_var.get().strip()
        entity_type = self.entity_type_var.get()
        
        if not entity_name:
            messagebox.showwarning("Input Error", "Please enter an entity name.")
            return
        
        # Disable button and start progress
        self.check_button.config(state='disabled')
        self.single_progress.start()
        
        # Run check in separate thread
        thread = threading.Thread(target=self._check_single_entity_thread, 
                                args=(entity_name, entity_type))
        thread.daemon = True
        thread.start()
    
    def _check_single_entity_thread(self, entity_name: str, entity_type: str):
        """Thread function for single entity check"""
        try:
            matches = self.checker.check_single_entity(entity_name, entity_type)
            
            # Update GUI through queue
            self.update_queue.put({
                'type': 'single_result',
                'entity_name': entity_name,
                'matches': matches
            })
            
        except Exception as e:
            self.update_queue.put({
                'type': 'error',
                'message': f"Error checking entity: {str(e)}"
            })
    
    def start_bulk_check(self):
        """Start bulk check process"""
        file_path = self.file_path_var.get()
        
        if not file_path or not os.path.exists(file_path):
            messagebox.showwarning("File Error", "Please select a valid input file.")
            return
        
        # Disable button and enable stop button
        self.bulk_check_button.config(state='disabled')
        self.stop_button.config(state='normal')
        
        # Clear log
        self.bulk_log_text.delete(1.0, tk.END)
        
        # Run bulk check in separate thread
        thread = threading.Thread(target=self._bulk_check_thread, args=(file_path,))
        thread.daemon = True
        thread.start()
    
    def _bulk_check_thread(self, file_path: str):
        """Thread function for bulk check"""
        try:
            # Load data from file
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Get column names
            name_column = self.name_column_var.get()
            type_column = self.type_column_var.get()
            
            if name_column not in df.columns:
                self.update_queue.put({
                    'type': 'error',
                    'message': f"Column '{name_column}' not found in file."
                })
                return
            
            # Prepare entities list
            entities = []
            for _, row in df.iterrows():
                entity = {'name': str(row[name_column])}
                if type_column in df.columns:
                    entity['type'] = str(row[type_column])
                entities.append(entity)
            
            # Update progress
            total_entities = len(entities)
            self.update_queue.put({
                'type': 'bulk_progress',
                'current': 0,
                'total': total_entities,
                'message': f"Starting bulk check of {total_entities} entities..."
            })
            
            # Perform bulk check
            results = {}
            for i, entity in enumerate(entities):
                if hasattr(self, 'stop_requested') and self.stop_requested:
                    break
                
                entity_name = entity['name']
                entity_type = entity.get('type', 'auto')
                
                # Update progress
                self.update_queue.put({
                    'type': 'bulk_progress',
                    'current': i + 1,
                    'total': total_entities,
                    'message': f"Checking {entity_name} ({i+1}/{total_entities})"
                })
                
                # Check entity
                matches = self.checker.check_single_entity(entity_name, entity_type)
                results[entity_name] = matches
                
                # Add to results tree
                if matches:
                    for match in matches:
                        self.update_queue.put({
                            'type': 'add_result',
                            'entity': entity_name,
                            'entity_type': match.entity_type,
                            'sanction_list': match.sanction_list,
                            'match_type': match.match_type,
                            'confidence': match.confidence,
                            'status': 'MATCH'
                        })
                else:
                    self.update_queue.put({
                        'type': 'add_result',
                        'entity': entity_name,
                        'entity_type': 'unknown',
                        'sanction_list': 'None',
                        'match_type': 'None',
                        'confidence': 0.0,
                        'status': 'CLEAR'
                    })
            
            # Generate report
            if results:
                output_format = self.output_format_var.get()
                report_file = self.checker.generate_report(results, output_format)
                
                self.update_queue.put({
                    'type': 'bulk_complete',
                    'message': f"Bulk check completed. Report saved as: {report_file}",
                    'results': results
                })
            
        except Exception as e:
            self.update_queue.put({
                'type': 'error',
                'message': f"Error during bulk check: {str(e)}"
            })
    
    def stop_bulk_check(self):
        """Stop bulk check process"""
        self.stop_requested = True
        self.bulk_check_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.update_queue.put({
            'type': 'bulk_stopped',
            'message': "Bulk check stopped by user."
        })
    
    def browse_file(self):
        """Browse for input file"""
        file_path = filedialog.askopenfilename(
            title="Select Input File",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.file_path_var.set(file_path)
    
    def clear_single_form(self):
        """Clear single check form"""
        self.entity_name_var.set("")
        self.entity_type_var.set("auto")
        self.single_results_text.delete(1.0, tk.END)
    
    def export_results(self):
        """Export results to file"""
        # Get all items from tree
        items = self.results_tree.get_children()
        if not items:
            messagebox.showinfo("No Results", "No results to export.")
            return
        
        # Prepare data
        data = []
        for item in items:
            values = self.results_tree.item(item)['values']
            data.append({
                'Entity': values[0],
                'Type': values[1],
                'Sanction List': values[2],
                'Match Type': values[3],
                'Confidence': values[4],
                'Status': values[5]
            })
        
        # Save file
        file_path = filedialog.asksaveasfilename(
            title="Export Results",
            defaultextension=".xlsx",
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("CSV files", "*.csv"),
                ("JSON files", "*.json")
            ]
        )
        
        if file_path:
            df = pd.DataFrame(data)
            if file_path.endswith('.csv'):
                df.to_csv(file_path, index=False)
            elif file_path.endswith('.json'):
                df.to_json(file_path, orient='records', indent=2)
            else:
                df.to_excel(file_path, index=False)
            
            messagebox.showinfo("Export Complete", f"Results exported to: {file_path}")
    
    def clear_results(self):
        """Clear results tree"""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
    
    def view_details(self):
        """View details of selected result"""
        selected_item = self.results_tree.selection()
        if not selected_item:
            messagebox.showinfo("No Selection", "Please select a result to view details.")
            return
        
        # Get selected item values
        values = self.results_tree.item(selected_item[0])['values']
        
        # Create details window
        details_window = tk.Toplevel(self.root)
        details_window.title("Result Details")
        details_window.geometry("600x400")
        
        # Display details
        details_text = scrolledtext.ScrolledText(details_window)
        details_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        details = f"""Entity: {values[0]}
Type: {values[1]}
Sanction List: {values[2]}
Match Type: {values[3]}
Confidence: {values[4]}
Status: {values[5]}
"""
        details_text.insert(tk.END, details)
    
    def save_settings(self):
        """Save application settings"""
        try:
            cache_duration = int(self.cache_duration_var.get())
            similarity_threshold = float(self.similarity_threshold_var.get())
            
            # Update checker settings
            self.checker.cache_duration = timedelta(hours=cache_duration)
            
            messagebox.showinfo("Settings Saved", "Settings have been saved successfully.")
            
        except ValueError as e:
            messagebox.showerror("Invalid Settings", f"Please enter valid numeric values: {str(e)}")
    
    def clear_cache(self):
        """Clear cached data"""
        try:
            import shutil
            if os.path.exists(self.checker.cache_dir):
                shutil.rmtree(self.checker.cache_dir)
                os.makedirs(self.checker.cache_dir, exist_ok=True)
            messagebox.showinfo("Cache Cleared", "Cache has been cleared successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear cache: {str(e)}")
    
    def test_connection(self):
        """Test connection to sanction sources"""
        def test_thread():
            try:
                # Test OFAC connection
                ofac_data = self.checker._fetch_ofac_data()
                if not ofac_data.empty:
                    self.update_queue.put({
                        'type': 'connection_test',
                        'message': "✓ OFAC connection successful"
                    })
                else:
                    self.update_queue.put({
                        'type': 'connection_test',
                        'message': "✗ OFAC connection failed"
                    })
                
                # Add more connection tests here
                
            except Exception as e:
                self.update_queue.put({
                    'type': 'connection_test',
                    'message': f"✗ Connection test failed: {str(e)}"
                })
        
        thread = threading.Thread(target=test_thread)
        thread.daemon = True
        thread.start()
    
    def check_queue(self):
        """Check for updates from worker threads"""
        try:
            while True:
                update = self.update_queue.get_nowait()
                
                if update['type'] == 'single_result':
                    self._handle_single_result(update)
                elif update['type'] == 'bulk_progress':
                    self._handle_bulk_progress(update)
                elif update['type'] == 'bulk_complete':
                    self._handle_bulk_complete(update)
                elif update['type'] == 'add_result':
                    self._handle_add_result(update)
                elif update['type'] == 'error':
                    messagebox.showerror("Error", update['message'])
                elif update['type'] == 'connection_test':
                    self._handle_connection_test(update)
                
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.check_queue)
    
    def _handle_single_result(self, update):
        """Handle single entity check result"""
        entity_name = update['entity_name']
        matches = update['matches']
        
        # Stop progress
        self.single_progress.stop()
        self.check_button.config(state='normal')
        
        # Display results
        self.single_results_text.delete(1.0, tk.END)
        
        if matches:
            result_text = f"Found {len(matches)} potential matches for '{entity_name}':\n\n"
            for i, match in enumerate(matches, 1):
                result_text += f"{i}. {match.sanction_list} - {match.match_type} match (confidence: {match.confidence:.2f})\n"
                result_text += f"   Details: {json.dumps(match.details, indent=2)}\n\n"
        else:
            result_text = f"No matches found for '{entity_name}' in any sanctions lists."
        
        self.single_results_text.insert(tk.END, result_text)
    
    def _handle_bulk_progress(self, update):
        """Handle bulk check progress update"""
        current = update['current']
        total = update['total']
        message = update['message']
        
        # Update progress bar
        if total > 0:
            progress = (current / total) * 100
            self.bulk_progress['value'] = progress
        
        # Update label
        self.progress_label.config(text=message)
        
        # Add to log
        self.bulk_log_text.insert(tk.END, f"{message}\n")
        self.bulk_log_text.see(tk.END)
    
    def _handle_bulk_complete(self, update):
        """Handle bulk check completion"""
        message = update['message']
        
        # Reset UI
        self.bulk_check_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.bulk_progress['value'] = 0
        self.progress_label.config(text="Ready to start")
        
        # Add completion message to log
        self.bulk_log_text.insert(tk.END, f"\n{message}\n")
        self.bulk_log_text.see(tk.END)
        
        # Show completion dialog
        messagebox.showinfo("Bulk Check Complete", message)
    
    def _handle_add_result(self, update):
        """Handle adding result to tree"""
        self.results_tree.insert("", "end", values=(
            update['entity'],
            update['entity_type'],
            update['sanction_list'],
            update['match_type'],
            f"{update['confidence']:.2f}",
            update['status']
        ))
    
    def _handle_connection_test(self, update):
        """Handle connection test result"""
        # Add to log in settings tab
        # This could be enhanced to show results in a dedicated area
        pass

def main():
    """Main function to run the GUI application"""
    root = tk.Tk()
    app = SanctionCheckerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 