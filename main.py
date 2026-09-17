import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import smtplib
import ssl
import pandas as pd
import re
import json
from datetime import datetime
import time
from tkinterdnd2 import DND_FILES, TkinterDnD
import pygame
import threading
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from tkcalendar import DateEntry
from cryptography.fernet import Fernet
import requests
import sys

SECRET_KEY_RAW = os.environ.get("EMAIL_APP_FERNET_KEY")
if not SECRET_KEY_RAW:
    # Ephemeral demo key so the app runs out of the box; set
    # EMAIL_APP_FERNET_KEY to a stable key for real licensing.
    SECRET_KEY_RAW = Fernet.generate_key().decode()
cipher = Fernet(SECRET_KEY_RAW.encode())
LICENSE_FILE = "license.dat"

current_dt = None  # global cache for time

def get_online_datetime():
    global current_dt
    try:
        r = requests.get("https://www.timeapi.io/api/Time/current/zone?timeZone=Asia/Kolkata", timeout=5)
        data = r.json()
        current_dt = datetime(
            data["year"], data["month"], data["day"],
            data["hour"], data["minute"], data["seconds"]
        )
    except:
        current_dt = datetime.now()

def get_cached_datetime():
    if current_dt:
        return current_dt
    return datetime.now()

def verify_license_key(key):
    try:
        decrypted = cipher.decrypt(key.encode()).decode()
        expiry_time = datetime.strptime(decrypted, "%Y-%m-%d %H:%M:%S")
        return get_cached_datetime() < expiry_time, expiry_time
    except Exception:
        return False, None

def save_license_encrypted(expiry_time):
    expiry_str = expiry_time.strftime("%Y-%m-%d %H:%M:%S")
    encrypted = cipher.encrypt(expiry_str.encode())
    with open(LICENSE_FILE, "wb") as f:
        f.write(encrypted)

def load_license_encrypted():
    if not os.path.exists(LICENSE_FILE):
        return None
    try:
        with open(LICENSE_FILE, "rb") as f:
            encrypted = f.read()
        decrypted = cipher.decrypt(encrypted).decode()
        return datetime.strptime(decrypted, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

def activate_window():
    root = ctk.CTk()
    root.title("🔑 Software Activation")
    root.geometry("400x200")
    root.resizable(False, False)

    ctk.CTkLabel(root, text="Enter Activation Key:", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=20)
    key_entry = ctk.CTkEntry(root, width=320, placeholder_text="Paste your activation key here")
    key_entry.pack(pady=10)

    result = {"activated": False, "expiry": None}

    def on_activate():
        key = key_entry.get().strip()
        valid, expiry_time = verify_license_key(key)
        if valid:
            save_license_encrypted(expiry_time)
            messagebox.showinfo("Activated", f"✅ Activated till {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}")
            result["activated"] = True
            result["expiry"] = expiry_time
            root.destroy()
        else:
            messagebox.showerror("Invalid", "❌ Invalid or Expired Key")

    ctk.CTkButton(root, text="Activate", command=on_activate, width=120).pack(pady=15)
    root.mainloop()
    return result

def check_expiry_once(expiry):
    if get_cached_datetime() >= expiry:
        root = ctk.CTk()
        root.withdraw()
        messagebox.showerror('Oops', 'Your Software Has Expired')
        if os.path.exists(LICENSE_FILE):
            os.remove(LICENSE_FILE)
        sys.exit()

pygame.mixer.init()

# Set CustomTkinter appearance
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class EmailSenderApp:
    def __init__(self):
        # Initialize main window with drag-drop support
        self.root = TkinterDnD.Tk()
        self.root.title("📧 Professional Email Sender")
        self.root.geometry("800x600+100+50")
        self.root.configure(bg='#f0f8ff')

        # Variables for email functionality
        self.sender_profiles = self.load_profiles()
        self.current_profile = None
        self.email_queue = []
        self.sent_count = 0
        self.failed_count = 0
        self.total_emails = 0
        self.is_sending = False
        self.cancel_sending = False
        self.single_attached_files = []
        self.bulk_attached_files = []
        self.recipient_data = []
        self.selected_recipients = []

        # Email history
        self.email_history = []

        self.template_html = """
        <!DOCTYPE html>
            <html lang="en">
            <head>
            <meta charset="UTF-8">
            <title>Dummy Email with Inline Images</title>
            <style>
              body {
                font-family: Arial, sans-serif;
                background-color: #f2f2f2;
                margin: 0;
                padding: 20px;
              }
              .container {
                background-color: #ffffff;
                max-width: 600px;
                margin: auto;
                padding: 25px;
                border-radius: 8px;
                border: 1px solid #ddd;
                color: #333333;
              }
              h1 {
                color: #4a90e2;
                text-align: center;
              }
              p {
                font-size: 16px;
                line-height: 1.6;
              }
              a.link {
                color: #e94e77;
                text-decoration: underline;
              }
              a.button {
                display: inline-block;
                padding: 12px 24px;
                background-color: #4a90e2;
                color: #ffffff !important;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                margin-top: 15px;
              }
              .highlight {
                background-color: #fff3cd;
                padding: 5px 10px;
                border-radius: 4px;
                color: #856404;
                display: inline-block;
              }
              .custom-bg {
                background-color: #d1f7c4;
                padding: 10px;
                border-radius: 5px;
                color: #256029;
              }
              img.img-center {
                display: block;
                margin: 15px auto;
                max-width: 100%;
                height: auto;
                border-radius: 6px;
              }
              .footer {
                font-size: 12px;
                color: #777777;
                margin-top: 30px;
                text-align: center;
              }
            </style>
            </head>
            <body>
              <div class="container">
                <h1>Welcome to Our Dummy Email</h1>

                <p>Hello <b>Friend</b>,</p>

                <p>This email demonstrates <b>bold</b>, <i>italic</i>, and <u>underlined</u> text with inline images attached to the email.</p>

                <p>Visit our 
                  <a href="https://www.example.com" class="link" target="_blank">website link</a> 
                  for more details.
                </p>

                <p class="highlight">This is highlighted text with a soft background color.</p>

                <p class="custom-bg">This block shows a different background and custom text color.</p>

                <p style="color:#e94e77;">This paragraph uses a custom pink text color.</p>


                <p>Attached images will appear below (attach them as attachments):</p>
                <img src="cid:image1" alt="Image 1" class="img-center" />
                <img src="cid:image2" alt="Image 2" class="img-center" />
                <img src="cid:image3" alt="Image 3" class="img-center" />
                <p>To add more images, simply attach them and follow the same pattern<p>
                <img src="cid:image4" alt="Image 4" class="img-center" />

                <p style="text-align:center;">
                  <a href="https://www.example.com/action" class="button" target="_blank">Click Here</a>
                </p>

                <div class="footer">
                  © 2025 Dummy Company • 
                </div>
              </div>
            </body>
        </html>

        """

        # Create the UI
        self.create_ui()

        # Load saved profiles
        self.load_saved_profiles()
        self.load_email_history()
        self.refresh_history()

        try:
            with open("selected_profile.json", "r") as f:
                data = json.load(f)
                saved_profile = data.get("selected_profile")
                if saved_profile and saved_profile in self.sender_profiles:
                    self.current_profile_name = saved_profile
                    self.current_profile = self.sender_profiles[saved_profile]
                    # Update dropdown or UI display with this saved profile
                    self.settings_profile_var.set(saved_profile)
                    self.load_profile_settings(saved_profile)
        except Exception:
            self.current_profile_name = None
            self.current_profile = None

    def create_ui(self):
        """Create the main user interface"""

        # Main container with gradient background
        main_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color=["#e6f3ff", "#1a1a2e"])
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Header with title and theme toggle
        header_frame = ctk.CTkFrame(main_frame, height=80, corner_radius=15,
                                    fg_color=["#4a90e2", "#2d3748"])
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        header_frame.pack_propagate(False)

        # App title
        title_label = ctk.CTkLabel(header_frame, text="📧 Professional Email Sender",
                                   font=ctk.CTkFont(size=24, weight="bold"),
                                   text_color=["white", "white"])
        title_label.pack(side="left", padx=30, pady=20)

        # Theme toggle button
        self.theme_button = ctk.CTkButton(header_frame, text="🌙 Dark Mode",
                                          command=self.toggle_theme,
                                          width=120, height=35,
                                          corner_radius=20,
                                          fg_color=["#ff6b35", "#ff6b35"],
                                          hover_color=["#e55a2b", "#e55a2b"])
        self.theme_button.pack(side="right", padx=30, pady=22)

        # Tabbed interface
        self.notebook = ctk.CTkTabview(main_frame, corner_radius=15, height=650)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=10)

        # Create tabs
        self.notebook.add("Single Email")
        self.notebook.add("Bulk Email")
        self.notebook.add("Email History")
        self.notebook.add("Settings")

        # Setup each tab
        self.setup_single_email_tab()
        self.setup_bulk_email_tab()
        self.setup_history_tab()
        self.setup_settings_tab()

    # The callback to show/hide the template button
    def on_email_format_change(self, *args):
        if self.email_format.get() == "HTML":
            self.message_body.delete("0.0", "end")  # Clear current content
            self.message_body.insert("0.0", self.template_html)
        else:
            self.message_body.delete("0.0", "end")

    def on_bulk_format_change(self, *args):
        if self.bulk_format_var.get() == "HTML":
            self.bulk_message.delete("0.0", "end")
            self.bulk_message.insert("0.0", self.template_html)
        else:
            self.bulk_message.delete("0.0", "end")

    def setup_single_email_tab(self):
        """Setup the single email sending tab"""
        single_tab = self.notebook.tab("Single Email")

        # Scrollable frame for single email tab
        scroll_frame = ctk.CTkScrollableFrame(single_tab, corner_radius=10)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Email Details Section
        email_frame = ctk.CTkFrame(scroll_frame, corner_radius=10)
        email_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(email_frame, text="✉ Email Details",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))

        # Create two columns for email fields
        fields_frame = ctk.CTkFrame(email_frame, fg_color="transparent")
        fields_frame.pack(fill="x", padx=20, pady=(0, 15))

        left_column = ctk.CTkFrame(fields_frame, fg_color="transparent")
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right_column = ctk.CTkFrame(fields_frame, fg_color="transparent")
        right_column.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # Left column fields
        ctk.CTkLabel(left_column, text="To Email:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        self.to_email = ctk.CTkEntry(left_column, placeholder_text="recipient@example.com", height=35, corner_radius=10)
        self.to_email.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(left_column, text="CC:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        self.cc_entry = ctk.CTkEntry(left_column, placeholder_text="cc@example.com", height=35, corner_radius=10)
        self.cc_entry.pack(fill="x", pady=(0, 15))



        ctk.CTkLabel(left_column, text="Subject:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        self.subject_entry = ctk.CTkEntry(left_column, placeholder_text="Email Subject", height=35, corner_radius=10)
        self.subject_entry.pack(fill="x", pady=(0, 15))

        # Right column fields
        format_frame = ctk.CTkFrame(right_column, fg_color="transparent")
        format_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(format_frame, text="Email Format:", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.email_format_var = ctk.StringVar(value="Plain Text")
        self.email_format = ctk.CTkSegmentedButton(format_frame, values=["Plain Text", "HTML"],
                                                   corner_radius=10, height=35, variable=self.email_format_var)
        self.email_format.pack(fill="x", pady=5)

        # Add trace callback on the variable inside CTkSegmentedButton
        self.email_format._variable.trace_add("write", self.on_email_format_change)

        ctk.CTkLabel(right_column, text="BCC:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        self.bcc_entry = ctk.CTkEntry(right_column, placeholder_text="bcc@example.com", height=35, corner_radius=10)
        self.bcc_entry.pack(fill="x", pady=(0, 15))

        # Test email button
        ctk.CTkButton(right_column, text="📧 Send Test Email", command=self.send_test_email,
                      height=35, corner_radius=10,
                      fg_color=["#17a2b8", "#17a2b8"]).pack(fill="x", pady=(27, 0))

        # Message body
        ctk.CTkLabel(scroll_frame, text="📝 Message Body:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(20, 5))

        self.message_body = ctk.CTkTextbox(scroll_frame, height=200, corner_radius=10,
                                           font=ctk.CTkFont(size=12))
        self.message_body.pack(fill="x", padx=10, pady=(0, 15))

        # Attachments Section
        attach_frame = ctk.CTkFrame(scroll_frame, corner_radius=10)
        attach_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(attach_frame, text="📎 Attachments",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))

        # Drag and drop area
        self.drop_frame = ctk.CTkFrame(attach_frame, height=80, corner_radius=10,
                                       fg_color=["#f8f9fa", "#2d3748"],
                                       border_width=2, border_color=["#dee2e6", "#4a5568"])
        self.drop_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.drop_frame.pack_propagate(False)

        # Setup drag and drop
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.on_file_drop_single)

        drop_label = ctk.CTkLabel(self.drop_frame, text="📁 Drag & Drop Files Here or Click Browse",
                                  font=ctk.CTkFont(size=14), text_color=["#6c757d", "#a0aec0"])
        drop_label.pack(expand=True)

        # Browse and clear buttons
        attach_buttons = ctk.CTkFrame(attach_frame, fg_color="transparent")
        attach_buttons.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkButton(attach_buttons, text="📂 Browse Files", command=self.browse_files_single,
                      width=120, height=35, corner_radius=10).pack(side="left", padx=(0, 10))

        ctk.CTkButton(attach_buttons, text="🗑 Clear All", command=self.clear_attachments_single,
                      width=120, height=35, corner_radius=10,
                      fg_color=["#dc3545", "#dc3545"]).pack(side="left")

        # Attached files list
        self.single_files_listbox = tk.Listbox(attach_frame, height=4, font=("Arial", 10),
                                        selectmode=tk.SINGLE, relief=tk.FLAT)
        self.single_files_listbox.pack(fill="x", padx=20, pady=(0, 15))

        # Send button
        self.send_single_button = ctk.CTkButton(scroll_frame, text="🚀 Send Email",
                                                command=self.on_single_send_clicked,
                                                height=50, corner_radius=15,
                                                font=ctk.CTkFont(size=16, weight="bold"),
                                                fg_color=["#28a745", "#28a745"],
                                                hover_color=["#218838", "#218838"])
        self.send_single_button.pack(fill="x", padx=10, pady=20)

    def setup_bulk_email_tab(self):
        """Setup the bulk email sending tab"""
        bulk_tab = self.notebook.tab("Bulk Email")

        # Scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(bulk_tab, corner_radius=10)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # File Upload Section
        upload_frame = ctk.CTkFrame(scroll_frame, corner_radius=10)
        upload_frame.pack(fill="x", padx=10, pady=15)

        ctk.CTkLabel(upload_frame, text="📊 Upload Recipients Excel File",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))

        upload_controls = ctk.CTkFrame(upload_frame, fg_color="transparent")
        upload_controls.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkButton(upload_controls, text="📁 Browse Excel File", command=self.browse_excel_file,
                      width=150, height=40, corner_radius=10,
                      fg_color=["#007bff", "#007bff"]).pack(side="left", padx=(0, 15))

        self.excel_file_label = ctk.CTkLabel(upload_controls, text="No file selected",
                                             font=ctk.CTkFont(size=12))
        self.excel_file_label.pack(side="left")

        # Recipients Preview Section
        preview_frame = ctk.CTkFrame(scroll_frame, corner_radius=10)
        preview_frame.pack(fill="x", padx=10, pady=15)

        preview_header = ctk.CTkFrame(preview_frame, fg_color="transparent")
        preview_header.pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkLabel(preview_header, text="👥 Recipients Preview",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        # Select/Deselect all buttons
        select_buttons = ctk.CTkFrame(preview_header, fg_color="transparent")
        select_buttons.pack(side="right")

        ctk.CTkButton(select_buttons, text="✅ Select All", command=self.select_all_recipients,
                      width=100, height=30, corner_radius=8).pack(side="left", padx=5)

        ctk.CTkButton(select_buttons, text="❌ Deselect All", command=self.deselect_all_recipients,
                      width=100, height=30, corner_radius=8,
                      fg_color=["#dc3545", "#dc3545"]).pack(side="left")

        # Recipients table
        self.recipients_frame = ctk.CTkScrollableFrame(preview_frame, height=200, corner_radius=10)
        self.recipients_frame.pack(fill="both", padx=20, pady=(0, 15))

        # Bulk Email Content Section
        content_frame = ctk.CTkFrame(scroll_frame, corner_radius=10)
        content_frame.pack(fill="x", padx=10, pady=15)

        ctk.CTkLabel(content_frame, text="✉ Bulk Email Content",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))

        # Subject and format
        bulk_controls = ctk.CTkFrame(content_frame, fg_color="transparent")
        bulk_controls.pack(fill="x", padx=20, pady=(0, 15))

        left_bulk = ctk.CTkFrame(bulk_controls, fg_color="transparent")
        left_bulk.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right_bulk = ctk.CTkFrame(bulk_controls, fg_color="transparent")
        right_bulk.pack(side="right", fill="both", expand=True, padx=(10, 0))

        ctk.CTkLabel(left_bulk, text="Subject:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        self.bulk_subject = ctk.CTkEntry(left_bulk, placeholder_text="Bulk Email Subject",
                                         height=35, corner_radius=10)
        self.bulk_subject.pack(fill="x")

        ctk.CTkLabel(right_bulk, text="Format:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        self.bulk_format_var = ctk.StringVar(value="Plain Text")
        self.bulk_format = ctk.CTkSegmentedButton(right_bulk, values=["Plain Text", "HTML"],
                                                  corner_radius=10, height=35, variable=self.bulk_format_var)
        self.bulk_format.pack(fill="x")
        self.bulk_format_var.trace_add("write", self.on_bulk_format_change)

        # Message body
        ctk.CTkLabel(content_frame, text="Message:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20,
                                                                                           pady=(15, 5))
        self.bulk_message = ctk.CTkTextbox(content_frame, height=150, corner_radius=10,
                                           font=ctk.CTkFont(size=12))
        self.bulk_message.pack(fill="x", padx=20)

        # Attachments Section
        attach_frame = ctk.CTkFrame(scroll_frame, corner_radius=10)
        attach_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(attach_frame, text="📎 Attachments",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))

        # Drag and drop area
        self.drop_frame = ctk.CTkFrame(attach_frame, height=80, corner_radius=10,
                                       fg_color=["#f8f9fa", "#2d3748"],
                                       border_width=2, border_color=["#dee2e6", "#4a5568"])
        self.drop_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.drop_frame.pack_propagate(False)

        # Setup drag and drop
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.on_file_drop_bulk)

        drop_label = ctk.CTkLabel(self.drop_frame, text="📁 Drag & Drop Files Here or Click Browse",
                                  font=ctk.CTkFont(size=14), text_color=["#6c757d", "#a0aec0"])
        drop_label.pack(expand=True)

        # Browse and clear buttons
        attach_buttons = ctk.CTkFrame(attach_frame, fg_color="transparent")
        attach_buttons.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkButton(attach_buttons, text="📂 Browse Files", command=self.browse_files_bulk,
                      width=120, height=35, corner_radius=10).pack(side="left", padx=(0, 10))

        ctk.CTkButton(attach_buttons, text="🗑️ Clear All", command=self.clear_attachments_bulk,
                      width=120, height=35, corner_radius=10,
                      fg_color=["#dc3545", "#dc3545"]).pack(side="left")

        # Attached files list
        self.bulk_files_listbox = tk.Listbox(attach_frame, height=4, font=("Arial", 10),
                                        selectmode=tk.SINGLE, relief=tk.FLAT)
        self.bulk_files_listbox.pack(fill="x", padx=20, pady=(0, 15))

        # Progress Section
        progress_frame = ctk.CTkFrame(scroll_frame, corner_radius=10)
        progress_frame.pack(fill="x", padx=10, pady=15)

        ctk.CTkLabel(progress_frame, text="📈 Sending Progress",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))

        # Progress stats
        stats_frame = ctk.CTkFrame(progress_frame, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.sent_label = ctk.CTkLabel(stats_frame, text="✅ Sent: 0",
                                       font=ctk.CTkFont(size=14, weight="bold"),
                                       text_color=["#28a745", "#28a745"])
        self.sent_label.pack(side="left", padx=20)

        self.pending_label = ctk.CTkLabel(stats_frame, text="⏳ Pending: 0",
                                          font=ctk.CTkFont(size=14, weight="bold"),
                                          text_color=["#ffc107", "#ffc107"])
        self.pending_label.pack(side="left", padx=20)

        self.failed_label = ctk.CTkLabel(stats_frame, text="❌ Failed: 0",
                                         font=ctk.CTkFont(size=14, weight="bold"),
                                         text_color=["#dc3545", "#dc3545"])
        self.failed_label.pack(side="left", padx=20)

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=20, corner_radius=10)
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 15))
        self.progress_bar.set(0)

        # Log area
        ctk.CTkLabel(progress_frame, text="📋 Sending Log:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(0, 5))

        self.log_text = ctk.CTkTextbox(progress_frame, height=120, corner_radius=10,
                                       font=ctk.CTkFont(size=10))
        self.log_text.pack(fill="x", padx=20, pady=(0, 15))

        # Bulk send buttons
        bulk_buttons = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        bulk_buttons.pack(fill="x", padx=10, pady=20)

        self.send_bulk_button = ctk.CTkButton(bulk_buttons, text="🚀 Send Bulk Emails",
                                              command=self.on_bulk_send_clicked,
                                              height=50, corner_radius=15,
                                              font=ctk.CTkFont(size=16, weight="bold"),
                                              fg_color=["#28a745", "#28a745"])
        self.send_bulk_button.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.cancel_button = ctk.CTkButton(bulk_buttons, text="⏹️ Cancel",
                                           command=self.cancel_bulk_sending,
                                           height=50, corner_radius=15, width=120,
                                           font=ctk.CTkFont(size=16, weight="bold"),
                                           fg_color=["#dc3545", "#dc3545"],
                                           state="disabled")
        self.cancel_button.pack(side="right")

    def get_scheduled_datetime(self):
        """
        Combines the date and time inputs into a datetime object.
        Returns None if invalid or empty.
        """
        try:
            date_str = self.date_entry.get()  # e.g., '2025-09-20'
            hour_str = self.hour_var.get()
            minute_str = self.minute_var.get()
            ampm = self.ampm_var.get()

            # Validate time inputs are digits within valid ranges
            if not (hour_str.isdigit() and minute_str.isdigit()):
                return None

            hour = int(hour_str)
            minute = int(minute_str)

            if hour < 1 or hour > 12 or minute < 0 or minute > 59:
                return None

            # Convert 12-hour time to 24-hour time
            if ampm == "PM" and hour != 12:
                hour += 12
            if ampm == "AM" and hour == 12:
                hour = 0

            # Combine date and time to datetime
            scheduled_dt = datetime.strptime(date_str, "%Y-%m-%d")
            scheduled_dt = scheduled_dt.replace(hour=hour, minute=minute, second=0, microsecond=0)

            return scheduled_dt
        except Exception:
            return None

    def schedule_email_send(self, send_type, send_callback, scheduled_target_options):
        """
        General method to handle scheduling logic for sending emails,
        avoiding code duplication for single and bulk send.

        :param send_type: "Single" or "Bulk" for user message display.
        :param send_callback: function to call for sending email immediately.
        :param scheduled_target_options: list of schedule_target values triggering scheduling.
        """
        schedule_target = self.schedule_target_var.get()
        scheduled_dt = self.get_scheduled_datetime()

        if schedule_target == "None":
            send_callback()
            return

        if not scheduled_dt:
            messagebox.showerror("Error", "Invalid date or time format")
            return

        delay = (scheduled_dt - datetime.now()).total_seconds()
        if delay <= 0:
            messagebox.showerror("Invalid time", "Scheduled time must be in the future")
            return

        if schedule_target in scheduled_target_options:
            # Start a new thread that sleeps for delay then calls send_callback
            threading.Thread(target=self._delayed_send, args=(delay, send_callback), daemon=True).start()
            messagebox.showinfo("Scheduling", f"{send_type} email scheduled for {scheduled_dt}")
        else:
            send_callback()
            messagebox.showinfo("Scheduling Not Applied", f"Scheduling not enabled for {schedule_target}")

    def _delayed_send(self, delay_seconds, send_callback):
        time.sleep(delay_seconds)
        send_callback()

    def on_single_send_clicked(self):
        self.schedule_email_send(
            send_type="Single",
            send_callback=self.send_single_email,
            scheduled_target_options=["Single Emails", "Both"]
        )

    def on_bulk_send_clicked(self):
        count = len(self.selected_recipients)  # Or the count of recipients to send to

        # Confirmation dialog
        if not messagebox.askyesno("Confirm Bulk Send",
                                   f"Are you sure you want to send {count} emails?"):
            return  # User cancelled sending
        self.schedule_email_send(
            send_type="Bulk",
            send_callback=self.send_bulk_emails,
            scheduled_target_options=["Bulk Emails", "Both"]
        )

    def setup_schedule_section(self, parent_frame):
        """Centered UI for Email Scheduling Section (Pack Layout)"""

        # ---- Header ----
        header = ctk.CTkLabel(
            parent_frame,
            text="📅 Email Scheduling",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header.pack(pady=(10, 20))  # Centered by default

        # ---- Target Selection ----
        target_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        target_frame.pack(pady=(0, 20))  # Center section

        ctk.CTkLabel(
            target_frame,
            text="Schedule For:",
            font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=(0, 15))

        self.schedule_target_var = ctk.StringVar(value="None")
        self.schedule_target_dropdown = ctk.CTkComboBox(
            target_frame,
            values=["None", "Single Emails", "Bulk Emails", "Both"],
            variable=self.schedule_target_var,
            width=200,  # slightly wider for balance
            state="readonly"
        )
        self.schedule_target_dropdown.pack(side="left")

        # ---- Date & Time Picker ----
        datetime_frame = ctk.CTkFrame(parent_frame, corner_radius=12)
        datetime_frame.pack(pady=(0, 20))  # Centered frame

        # Date row
        date_row = ctk.CTkFrame(datetime_frame, fg_color="transparent")
        date_row.pack(pady=12)

        ctk.CTkLabel(
            date_row,
            text="Select Date:",
            font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=(0, 15))


        self.date_entry = DateEntry(
            date_row,
            date_pattern="yyyy-mm-dd",
            width=20,  # increased width
            font=("Arial", 12)  # larger font gives more height
        )
        self.date_entry.pack(side="left")

        # Time row
        time_row = ctk.CTkFrame(datetime_frame, fg_color="transparent")
        time_row.pack(pady=12)

        ctk.CTkLabel(
            time_row,
            text="Select Time:",
            font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=(0, 15))

        time_inner = ctk.CTkFrame(time_row, fg_color="transparent")
        time_inner.pack(side="left")

        self.hour_var = ctk.StringVar(value="01")
        self.hour_entry = ctk.CTkEntry(
            time_inner, width=55, height=40,  # slightly larger height
            textvariable=self.hour_var, justify="center"
        )
        self.hour_entry.pack(side="left")

        ctk.CTkLabel(time_inner, text=":", font=ctk.CTkFont(size=20)).pack(side="left", padx=6)

        self.minute_var = ctk.StringVar(value="00")
        self.minute_entry = ctk.CTkEntry(
            time_inner, width=55, height=40,
            textvariable=self.minute_var, justify="center"
        )
        self.minute_entry.pack(side="left", padx=(0, 8))

        self.ampm_var = ctk.StringVar(value="AM")
        self.ampm_button = ctk.CTkSegmentedButton(
            time_inner, values=["AM", "PM"],
            variable=self.ampm_var, width=100
        )
        self.ampm_button.pack(side="left")

    def on_add_profile_clicked(self):
        self.clear_profile_form()
        self.settings_profile_var.set("Select Profile")

    def setup_settings_tab(self):
        """Setup the settings and profiles tab"""
        settings_tab = self.notebook.tab("Settings")

        scroll_frame = ctk.CTkScrollableFrame(settings_tab, corner_radius=10)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Sender Profiles Section
        profiles_frame = ctk.CTkFrame(scroll_frame, corner_radius=10)
        profiles_frame.pack(fill="x", padx=10, pady=15)

        ctk.CTkLabel(profiles_frame, text="👤 Sender Profiles",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))

        # Profile management
        profile_mgmt = ctk.CTkFrame(profiles_frame, fg_color="transparent")
        profile_mgmt.pack(fill="x", padx=20, pady=(0, 15))

        self.settings_profile_var = ctk.StringVar(value="Select Profile")
        self.settings_profile_dropdown = ctk.CTkComboBox(profile_mgmt,
                                                         values=list(self.sender_profiles.keys()),
                                                         variable=self.settings_profile_var,
                                                         command=self.load_profile_settings,
                                                         width=200, height=35, corner_radius=10)
        self.settings_profile_dropdown.pack(side="left", padx=(0, 15))

        ctk.CTkButton(profile_mgmt, text="🗑 Delete", command=self.delete_profile,
                      width=100, height=35, corner_radius=10,
                      fg_color=["#dc3545", "#dc3545"]).pack(side="left", padx=5)

        # Profile form
        form_frame = ctk.CTkFrame(profiles_frame, fg_color="transparent")
        form_frame.pack(fill="x", padx=20, pady=(0, 15))

        left_form = ctk.CTkFrame(form_frame, fg_color="transparent")
        left_form.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right_form = ctk.CTkFrame(form_frame, fg_color="transparent")
        right_form.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # Left form fields
        ctk.CTkLabel(left_form, text="Profile Name:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        self.profile_name_entry = ctk.CTkEntry(left_form, placeholder_text="My Gmail Account",
                                               height=35, corner_radius=10)
        self.profile_name_entry.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(left_form, text="Email Address:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        self.sender_email_entry = ctk.CTkEntry(left_form, placeholder_text="your.email@gmail.com",
                                               height=35, corner_radius=10)
        self.sender_email_entry.pack(fill="x", pady=(0, 15))



        ctk.CTkLabel(right_form, text="SMTP Server:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        self.smtp_server_var = ctk.StringVar(value="smtp.gmail.com")
        self.smtp_server_combobox = ctk.CTkComboBox(right_form,
                                                    values=[
                                                        "smtp.gmail.com",
                                                        "smtp.mail.yahoo.com",
                                                        "smtp.office365.com",
                                                        "smtp.live.com",
                                                        "smtp.mail.com"
                                                    ],
                                                    variable=self.smtp_server_var,
                                                    height=35,
                                                    corner_radius=10)
        self.smtp_server_combobox.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(right_form, text="App Password:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        self.sender_password_entry = ctk.CTkEntry(right_form, placeholder_text="App Specific Password",
                                                  height=35, corner_radius=10, show="*")
        self.sender_password_entry.pack(fill="x", pady=(0, 15))

        # Create a frame to hold save and add profile buttons
        buttons_frame = ctk.CTkFrame(profiles_frame, fg_color="transparent")
        buttons_frame.pack(padx=20, pady=(0, 15))

        # Save Profile button
        ctk.CTkButton(buttons_frame, text="💾 Save Profile", command=self.save_profile,
                      height=40, corner_radius=10,
                      fg_color=["#007bff", "#007bff"]).pack(side="left", padx=(0, 10))

        # Add Profile button
        ctk.CTkButton(buttons_frame, text="➕ Add Profile", command=self.on_add_profile_clicked,
                      height=40, corner_radius=10,
                      fg_color=["#28a745", "#28a745"]).pack(side="left")

        # Application Settings
        app_settings_frame = ctk.CTkFrame(scroll_frame, corner_radius=10)
        app_settings_frame.pack(fill="x", padx=10, pady=15)

        ctk.CTkLabel(app_settings_frame, text="⚙️ Application Settings",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))

        # Theme and notification settings
        settings_grid = ctk.CTkFrame(app_settings_frame, fg_color="transparent")
        settings_grid.pack(fill="x", padx=20, pady=(0, 15))

        # Sound notifications
        sound_frame = ctk.CTkFrame(settings_grid, fg_color="transparent")
        sound_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(sound_frame, text="🔔 Sound Notifications:",
                     font=ctk.CTkFont(weight="bold")).pack(side="left")

        self.sound_notifications = ctk.CTkSwitch(sound_frame, text="Enable")
        self.sound_notifications.pack(side="right")
        self.sound_notifications.select()  # Default enabled

        # Auto-save history
        autosave_frame = ctk.CTkFrame(settings_grid, fg_color="transparent")
        autosave_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(autosave_frame, text="💾 Auto-save History:",
                     font=ctk.CTkFont(weight="bold")).pack(side="left")

        self.auto_save_history = ctk.CTkSwitch(autosave_frame, text="Enable")
        self.auto_save_history.pack(side="right")
        self.auto_save_history.select()  # Default enabled

        # Create a container frame for schedule UI but initially not packed
        self.scheduling_section_frame = ctk.CTkFrame(settings_grid, fg_color="transparent")
        self.setup_schedule_section(self.scheduling_section_frame)
        self.scheduling_section_frame.pack(fill="x", padx=10, pady=10)

    def setup_history_tab(self):
        """Setup the email history tab"""
        history_tab = self.notebook.tab("Email History")

        # History controls
        history_controls = ctk.CTkFrame(history_tab, height=60, corner_radius=10)
        history_controls.pack(fill="x", padx=10, pady=15)
        history_controls.pack_propagate(False)

        ctk.CTkLabel(history_controls, text="📜 Email History & Logs",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=20, pady=15)

        history_buttons = ctk.CTkFrame(history_controls, fg_color="transparent")
        history_buttons.pack(side="right", padx=20, pady=10)

        ctk.CTkButton(history_buttons, text="🔄 Refresh", command=self.refresh_history,
                      width=100, height=35, corner_radius=10).pack(side="left", padx=5)

        ctk.CTkButton(history_buttons, text="💾 Export CSV", command=self.export_history,
                      width=100, height=35, corner_radius=10,
                      fg_color=["#17a2b8", "#17a2b8"]).pack(side="left", padx=5)

        ctk.CTkButton(history_buttons, text="🗑️ Clear History", command=self.clear_history,
                      width=100, height=35, corner_radius=10,
                      fg_color=["#dc3545", "#dc3545"]).pack(side="left", padx=5)

        # History table
        self.history_frame = ctk.CTkScrollableFrame(history_tab, corner_radius=10)
        self.history_frame.pack(fill="both", expand=True, padx=10, pady=(0, 15))

    # Theme Functions
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        current_mode = ctk.get_appearance_mode()
        if current_mode == "Light":
            ctk.set_appearance_mode("dark")
            self.theme_button.configure(text="☀️ Light Mode")
        else:
            ctk.set_appearance_mode("light")
            self.theme_button.configure(text="🌙 Dark Mode")

    # Profile Management Functions
    def load_profiles(self):
        """Load saved email profiles"""
        try:
            if os.path.exists("email_profiles.json"):
                with open("email_profiles.json", "r") as f:
                    return json.load(f)
        except:
            pass
        return {}

    def save_profiles(self):
        """Save email profiles to file"""
        try:
            with open("email_profiles.json", "w") as f:
                json.dump(self.sender_profiles, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save profiles: {str(e)}")

    def load_saved_profiles(self):
        """Load saved profiles into dropdowns"""
        profile_names = list(self.sender_profiles.keys())
        if hasattr(self, 'profile_dropdown'):
            self.profile_dropdown.configure(values=profile_names)
        if hasattr(self, 'settings_profile_dropdown'):
            self.settings_profile_dropdown.configure(values=profile_names)

    def on_profile_selected(self, selection):
        """Handle profile selection"""
        if selection in self.sender_profiles:
            self.current_profile = self.sender_profiles[selection]
            messagebox.showinfo("Profile Selected", f"Selected profile: {selection}")

    def load_profile_settings(self, selection):
        """Load profile data into settings form"""
        if selection in self.sender_profiles:
            profile = self.sender_profiles[selection]
            self.current_profile = profile
            self.current_profile_name = selection  # Track profile name

            # Save selected profile name persistently
            try:
                with open("selected_profile.json", "w") as f:
                    json.dump({"selected_profile": selection}, f)
            except Exception as e:
                print(f"Error saving selected profile: {e}")

            self.profile_name_entry.delete(0, tk.END)
            self.profile_name_entry.insert(0, selection)

            self.sender_email_entry.delete(0, tk.END)
            self.sender_email_entry.insert(0, profile["email"])

            self.sender_password_entry.delete(0, tk.END)
            self.sender_password_entry.insert(0, profile["password"])

            # Set the SMTP server combo box variable instead of entry
            self.smtp_server_var.set(profile.get("smtp_server", "smtp.gmail.com"))

    def save_profile(self):
        """Save or update profile"""
        profile_name = self.profile_name_entry.get().strip()
        email = self.sender_email_entry.get().strip()
        password = self.sender_password_entry.get().strip()
        smtp_server = self.smtp_server_var.get().strip()  # combo box variable, not entry

        # Port is fixed
        smtp_port = 587

        if not all([profile_name, email, password, smtp_server]):
            messagebox.showerror("Error", "All fields are required!")
            return

        if not self.validate_email(email):
            messagebox.showerror("Error", "Invalid email address format!")
            return

        self.sender_profiles[profile_name] = {
            "email": email,
            "password": password,
            "smtp_server": smtp_server,
            "smtp_port": smtp_port  # fixed port
        }

        self.save_profiles()
        self.load_saved_profiles()
        messagebox.showinfo("Success", f"Profile '{profile_name}' saved successfully!")

    def delete_profile(self):
        """Delete selected profile"""
        selected = self.settings_profile_var.get()
        if selected and selected != "Select Profile":
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete profile '{selected}'?"):
                del self.sender_profiles[selected]
                self.save_profiles()
                self.load_saved_profiles()
                self.clear_profile_form()
                # Reset combo box text to default 'Select Profile'
                self.settings_profile_var.set("Select Profile")
                messagebox.showinfo("Success", f"Profile '{selected}' deleted successfully!")

    def clear_profile_form(self):
        """Clear profile form fields"""
        self.profile_name_entry.delete(0, tk.END)
        self.sender_email_entry.delete(0, tk.END)
        self.sender_password_entry.delete(0, tk.END)
        self.smtp_server_var.set("smtp.gmail.com")  # reset to default SMTP server

    def on_file_drop_single(self, event):
        """Handle file drop event for single email attachments"""
        files = self.root.tk.splitlist(event.data)
        for file_path in files:
            if os.path.isfile(file_path) and file_path not in self.single_attached_files:
                self.single_attached_files.append(file_path)
                self.single_files_listbox.insert(tk.END, os.path.basename(file_path))

    def on_file_drop_bulk(self, event):
        """Handle file drop event for bulk email attachments"""
        files = self.root.tk.splitlist(event.data)
        for file_path in files:
            if os.path.isfile(file_path) and file_path not in self.bulk_attached_files:
                self.bulk_attached_files.append(file_path)
                self.bulk_files_listbox.insert(tk.END, os.path.basename(file_path))

    def browse_files_single(self):
        files = filedialog.askopenfilenames(title="Select Files for Single Email", filetypes=[("All Files", "*.*")])
        for file_path in files:
            if file_path not in self.single_attached_files:
                self.single_attached_files.append(file_path)
                self.single_files_listbox.insert(tk.END, os.path.basename(file_path))

    def clear_attachments_single(self):
        self.single_attached_files.clear()
        self.single_files_listbox.delete(0, tk.END)

    def browse_files_bulk(self):
        files = filedialog.askopenfilenames(title="Select Files for Bulk Email", filetypes=[("All Files", "*.*")])
        for file_path in files:
            if file_path not in self.bulk_attached_files:
                self.bulk_attached_files.append(file_path)
                self.bulk_files_listbox.insert(tk.END, os.path.basename(file_path))

    def clear_attachments_bulk(self):
        self.bulk_attached_files.clear()
        self.bulk_files_listbox.delete(0, tk.END)

    def browse_excel_file(self):
        """Browse and select Excel file for bulk emails"""
        file_path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel Files", "*.xlsx *.xls *.csv")]

        )

        if file_path:
            try:
                if file_path.lower().endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)

                # Find email column (look for common column names)
                email_column = None
                common_names = ['email', 'emails', 'email_address', 'email address', 'recipient', 'recipients']

                for col in df.columns:
                    if col.lower() in common_names:
                        email_column = col
                        break

                if not email_column:
                    # If no common name found, use first column
                    email_column = df.columns[0]

                # Extract and validate emails
                emails = df[email_column].dropna().astype(str).tolist()
                valid_emails = [email for email in emails if self.validate_email(email)]

                # Remove duplicates while preserving order
                seen = set()
                unique_emails = []
                for email in valid_emails:
                    if email.lower() not in seen:
                        seen.add(email.lower())
                        unique_emails.append(email)

                self.recipient_data = unique_emails
                self.selected_recipients = unique_emails.copy()  # Initially all selected

                # Update UI
                self.excel_file_label.configure(text=f"Loaded: {len(unique_emails)} valid unique emails")
                self.update_recipients_preview()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read Excel file: {str(e)}")

    def update_recipients_preview(self):
        """Update the recipients preview table"""
        # Clear existing widgets
        for widget in self.recipients_frame.winfo_children():
            widget.destroy()

        if not self.recipient_data:
            ctk.CTkLabel(self.recipients_frame, text="No recipients loaded",
                         font=ctk.CTkFont(size=14)).pack(pady=20)
            return

        # Create header
        header_frame = ctk.CTkFrame(self.recipients_frame, fg_color=["#e9ecef", "#343a40"])
        header_frame.pack(fill="x", padx=5, pady=(5, 10))

        ctk.CTkLabel(header_frame, text="Select", font=ctk.CTkFont(weight="bold"),
                     width=80).pack(side="left", padx=10, pady=5)
        ctk.CTkLabel(header_frame, text="Email Address", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10,
                                                                                               pady=5)

        # Create recipient rows (limit to first 20 for performance)
        self.recipient_checkboxes = {}
        display_count = min(len(self.recipient_data), 20)

        for i, email in enumerate(self.recipient_data[:display_count]):
            row_frame = ctk.CTkFrame(self.recipients_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=5, pady=2)

            # Checkbox
            var = ctk.BooleanVar(value=email in self.selected_recipients)
            checkbox = ctk.CTkCheckBox(row_frame, text="", variable=var, width=80,
                                       command=lambda e=email, v=var: self.toggle_recipient(e, v))
            checkbox.pack(side="left", padx=10, pady=2)

            # Email label
            ctk.CTkLabel(row_frame, text=email, font=ctk.CTkFont(size=12)).pack(side="left", padx=10, pady=2)

            self.recipient_checkboxes[email] = var

        if len(self.recipient_data) > 20:
            ctk.CTkLabel(self.recipients_frame,
                         text=f"... and {len(self.recipient_data) - 20} more recipients",
                         font=ctk.CTkFont(size=12, style="italic")).pack(pady=10)

    def toggle_recipient(self, email, var):
        """Toggle recipient selection"""
        if var.get():
            if email not in self.selected_recipients:
                self.selected_recipients.append(email)
        else:
            if email in self.selected_recipients:
                self.selected_recipients.remove(email)

    def select_all_recipients(self):
        """Select all recipients"""
        self.selected_recipients = self.recipient_data.copy()
        for email, var in self.recipient_checkboxes.items():
            var.set(True)

    def deselect_all_recipients(self):
        """Deselect all recipients"""
        self.selected_recipients.clear()
        for email, var in self.recipient_checkboxes.items():
            var.set(False)

    # Email Validation and Sending Functions
    def validate_email(self, email):
        """Validate email address format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email.strip()) is not None

    def send_test_email(self):
        """Send a test email to sender's own address"""
        if not self.current_profile:
            messagebox.showerror("Error", "Please select a sender profile first!")
            return

        subject = self.subject_entry.get() or "Test Email"
        message = self.message_body.get("1.0", tk.END).strip() or "This is a test email."

        # Send to sender's own email
        recipient = self.current_profile["email"]

        threading.Thread(target=self._send_test_email_thread,
                         args=(recipient, subject, message), daemon=True).start()

    def _send_test_email_thread(self, recipient, subject, message):
        """Thread function for sending test email"""
        try:
            cc_list = [addr.strip() for addr in self.cc_entry.get().split(",") if addr.strip()]
            bcc_list = [addr.strip() for addr in self.bcc_entry.get().split(",") if addr.strip()]
            success = self.send_email(recipient, subject, message, self.single_attached_files, cc=cc_list, bcc=bcc_list)

            if success:
                self.root.after(0, lambda: messagebox.showinfo("Success",
                                                               f"Test email sent successfully to {recipient}!"))
            else:
                self.root.after(0, lambda: messagebox.showerror("Error",
                                                                "Failed to send test email!"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Test email failed: {str(e)}"))

    def send_single_email(self):
        """Send a single email"""
        if not self.current_profile:
            messagebox.showerror("Error", "Please select a sender profile first!")
            return

        recipient = self.to_email.get().strip()
        subject = self.subject_entry.get().strip()
        message = self.message_body.get("1.0", tk.END).strip()

        if not all([recipient, subject, message]):
            messagebox.showerror("Error", "Please fill in all required fields!")
            return

        if not self.validate_email(recipient):
            messagebox.showerror("Error", "Invalid recipient email address!")
            return

        # Disable send button during sending
        self.send_single_button.configure(state="disabled", text="Sending...")

        threading.Thread(target=self._send_single_email_thread,
                         args=(recipient, subject, message), daemon=True).start()

    def _send_single_email_thread(self, recipient, subject, message):
        """Thread function for sending single email"""
        try:
            cc_list = [addr.strip() for addr in self.cc_entry.get().split(",") if addr.strip()]
            bcc_list = [addr.strip() for addr in self.bcc_entry.get().split(",") if addr.strip()]
            success = self.send_email(recipient, subject, message, self.single_attached_files, cc=cc_list, bcc=bcc_list)


            # Log the email
            self.log_email(recipient, subject, "Sent" if success else "Failed", attachments=self.single_attached_files)

            self.root.after(0, self.refresh_history)

            if success:
                self.root.after(0, lambda: messagebox.showinfo("Success",
                                                               f"Email sent successfully to {recipient}!"))
                if self.sound_notifications.get():
                    self.play_sound("success")
            else:
                self.root.after(0, lambda: messagebox.showerror("Error",
                                                                f"Failed to send email to {recipient}!"))
                if self.sound_notifications.get():
                    self.play_sound("error")

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Email sending failed: {str(e)}"))
        finally:
            # Re-enable send button
            self.root.after(0, lambda: self.send_single_button.configure(state="normal", text="🚀 Send Email"))

    def send_bulk_emails(self):
        """Start bulk email sending process"""
        if not self.current_profile:
            messagebox.showerror("Error", "Please select a sender profile first!")
            return

        if not self.selected_recipients:
            messagebox.showerror("Error", "No recipients selected!")
            return

        subject = self.bulk_subject.get().strip()
        message = self.bulk_message.get("1.0", tk.END).strip()

        if not all([subject, message]):
            messagebox.showerror("Error", "Please fill in subject and message!")
            return

        # Confirm before sending
        count = len(self.selected_recipients)
        # Initialize progress tracking
        self.sent_count = 0
        self.failed_count = 0
        self.total_emails = count
        self.is_sending = True
        self.cancel_sending = False

        # Update UI
        self.send_bulk_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.log_text.delete("1.0", tk.END)

        # Start sending thread
        threading.Thread(target=self._send_bulk_emails_thread,
                         args=(subject, message), daemon=True).start()

    def _send_bulk_emails_thread(self, subject, message):
        """Thread function for sending bulk emails"""
        try:
            for i, recipient in enumerate(self.selected_recipients):
                if self.cancel_sending:
                    break

                try:
                    success = self.send_email(recipient, subject, message, self.bulk_attached_files)

                    if success:
                        self.sent_count += 1
                        status = "Sent"
                        if self.sound_notifications.get():
                            self.play_sound("sent")
                    else:
                        self.failed_count += 1
                        status = "Failed"

                    # Log the email
                    self.log_email(recipient, subject, status, attachments=self.bulk_attached_files)

                    # Update UI
                    self.root.after(0, self.update_bulk_progress, recipient, status)

                    # Small delay between emails
                    time.sleep(1)

                except Exception as e:
                    self.failed_count += 1
                    self.root.after(0, self.update_bulk_progress, recipient, f"Error: {str(e)}")

            # Finish
            self.root.after(0, self.finish_bulk_sending)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Bulk sending failed: {str(e)}"))
            self.root.after(0, self.finish_bulk_sending)

    def update_bulk_progress(self, recipient, status):
        """Update bulk sending progress in UI"""
        # Update progress bar
        progress = (self.sent_count + self.failed_count) / self.total_emails
        self.progress_bar.set(progress)

        # Update statistics
        pending = self.total_emails - self.sent_count - self.failed_count
        self.sent_label.configure(text=f"✅ Sent: {self.sent_count}")
        self.pending_label.configure(text=f"⏳ Pending: {pending}")
        self.failed_label.configure(text=f"❌ Failed: {self.failed_count}")

        # Add to log
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {recipient} - {status}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)

    def finish_bulk_sending(self):
        """Finish bulk email sending process"""
        self.is_sending = False
        self.send_bulk_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")

        # Play completion sound immediately
        if self.sound_notifications.get():
            self.play_sound("complete")

        # Show completion message
        message = f"Bulk sending completed!\n\nSent: {self.sent_count}\nFailed: {self.failed_count}\nTotal: {self.total_emails}"
        messagebox.showinfo("Bulk Send Complete", message)

    def cancel_bulk_sending(self):
        """Cancel bulk email sending"""
        self.cancel_sending = True
        self.cancel_button.configure(state="disabled")
        messagebox.showinfo("Cancelled", "Bulk sending has been cancelled.")

    def send_email(self, to_email, subject, message, attachments=None, cc=None, bcc=None):
        """Core email sending function"""
        try:
            # Ensure cc and bcc are lists
            cc = cc or []
            bcc = bcc or []
            to_addrs = [to_email] if isinstance(to_email, str) else list(to_email)
            all_recipients = to_addrs + cc + bcc

            # Create a multipart/related message for HTML with inline images
            msg = MIMEMultipart('related')
            msg['From'] = self.current_profile['email']
            msg['To'] = ', '.join(to_addrs)
            msg['Subject'] = subject
            if cc:
                msg['Cc'] = ', '.join(cc)

            # Create an alternative part for plain text and html
            alternative_part = MIMEMultipart('alternative')
            msg.attach(alternative_part)

            # Plain text fallback
            alternative_part.attach(MIMEText("This email contains HTML content.", 'plain'))

            # Attach HTML message
            alternative_part.attach(MIMEText(message, 'html'))

            # Attach images inline and other files as attachments
            if attachments:
                for i, file_path in enumerate(attachments):
                    if os.path.isfile(file_path):
                        ext = os.path.splitext(file_path)[1].lower()
                        with open(file_path, 'rb') as f:
                            content = f.read()
                            if ext in ['.jpg', '.jpeg', '.png', '.gif']:
                                img = MIMEImage(content)
                                cid = f'image{i + 1}'
                                img.add_header('Content-ID', f'<{cid}>')
                                img.add_header('Content-Disposition', 'inline', filename=os.path.basename(file_path))
                                msg.attach(img)
                            else:
                                part = MIMEBase('application', 'octet-stream')
                                part.set_payload(content)
                                encoders.encode_base64(part)
                                part.add_header('Content-Disposition',
                                                f'attachment; filename={os.path.basename(file_path)}')
                                msg.attach(part)

            # Send email as before
            context = ssl.create_default_context()
            with smtplib.SMTP(self.current_profile['smtp_server'], self.current_profile['smtp_port']) as server:
                server.starttls(context=context)
                server.login(self.current_profile['email'], self.current_profile['password'])
                server.sendmail(self.current_profile['email'], all_recipients, msg.as_string())

            return True

        except Exception as e:
            print(f"Email sending error: {e}")
            return False

    def load_email_history(self):
        try:
            if os.path.exists("email_history.csv"):
                df = pd.read_csv("email_history.csv")
                self.email_history = df.to_dict('records')
            else:
                self.email_history = []
        except Exception as e:
            print(f"Failed to load email history: {e}")
            self.email_history = []

    # Logging and History Functions
    def log_email(self, recipient, subject, status, attachments=None):
        if not self.auto_save_history.get():
            return
        log_entry = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "recipient": recipient,
            "subject": subject,
            "status": status,
            "sender": self.current_profile['email'] if self.current_profile else "Unknown",
            "attachments": ", ".join([os.path.basename(f) for f in attachments]) if attachments else ""
        }
        self.email_history.append(log_entry)


        self.save_history_to_csv()

    def save_history_to_csv(self):
        """Save email history to CSV file"""
        try:
            if self.email_history:
                df = pd.DataFrame(self.email_history)
                df.to_csv("email_history.csv", index=False)
        except Exception as e:
            print(f"Failed to save history: {e}")


    def refresh_history(self):
        """Refresh the history display with scrollable, well-formatted table"""
        # Clear previous content
        for widget in self.history_frame.winfo_children():
            widget.destroy()

        if not self.email_history:
            ctk.CTkLabel(self.history_frame,
                         text="No email history available",
                         font=ctk.CTkFont(size=14)).pack(pady=20)
            return

        # ---------- Scrollable Container ----------
        container = ctk.CTkFrame(self.history_frame, corner_radius=10)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # Scrollbars
        vsb = tk.Scrollbar(container, orient="vertical")
        hsb = tk.Scrollbar(container, orient="horizontal")
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")

        # ---------- Treeview Table ----------
        columns = ["Date", "Time", "Recipient", "Subject", "Status", "Sender", "Attachments"]
        tree = ttk.Treeview(container,
                            columns=columns,
                            show="headings",
                            yscrollcommand=vsb.set,
                            xscrollcommand=hsb.set,
                            height=20)

        tree.pack(side="left", fill="both", expand=False)
        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)

        # Style
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"))
        style.configure("Treeview", rowheight=28, font=("Arial", 10))

        # Column widths & wrapping strategy
        col_widths = {
            "Date": 90, "Time": 80,
            "Recipient": 180, "Subject": 200,
            "Status": 80, "Sender": 180,
            "Attachments": 350  # give more width for long file names
        }

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col,
                        width=col_widths.get(col, 120),
                        anchor="w", stretch=False)

        # Latest first (limit 50)
        recent = self.email_history[-50:] if len(self.email_history) > 50 else self.email_history

        for entry in reversed(recent):
            attachments = entry.get("attachments", "")
            if not attachments or str(attachments).lower() == "nan":
                attachments = "None"

            # Truncate overly long attachment list for visual clarity
            max_len = 50
            if len(attachments) > max_len:
                attachments = attachments[:max_len] + "…"

            tree.insert("", "end", values=(
                entry["date"],
                entry["time"],
                entry["recipient"],
                entry["subject"],
                entry["status"],
                entry["sender"],
                attachments
            ))

        # Color rows by status
        def tag_rows():
            for row in tree.get_children():
                status = tree.item(row)["values"][4]
                if status == "Sent":
                    tree.item(row, tags=("sent",))
                else:
                    tree.item(row, tags=("failed",))
            tree.tag_configure("sent", background="#d4edda")  # light green
            tree.tag_configure("failed", background="#f8d7da")  # light red

        tag_rows()

    def export_history(self):
        """Export email history to CSV"""
        if not self.email_history:
            messagebox.showinfo("No Data", "No email history to export!")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Email History",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("Excel Files", "*.xlsx")]
        )

        if file_path:
            try:
                df = pd.DataFrame(self.email_history)
                if file_path.endswith('.xlsx'):
                    df.to_excel(file_path, index=False)
                else:
                    df.to_csv(file_path, index=False)
                messagebox.showinfo("Success", f"Email history exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export history: {str(e)}")

    def clear_history(self):
        """Clear email history"""
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all email history?"):
            self.email_history.clear()
            try:
                if os.path.exists("email_history.csv"):
                    os.remove("email_history.csv")
            except:
                pass
            self.refresh_history()
            messagebox.showinfo("Success", "Email history cleared successfully!")

    def play_sound(self, sound_type):
        sound_files = {
            "success": "sounds/success.mp3",
            "sent": "sounds/success.mp3",
            "error": "sounds/error.mp3",
            "complete": "sounds/complete.mp3"
        }
        sound_file = sound_files.get(sound_type)
        if sound_file and os.path.exists(sound_file):
            def play():
                try:
                    pygame.mixer.music.load(sound_file)
                    pygame.mixer.music.play()
                    # Wait until the sound finishes playing
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)
                except Exception as e:
                    print(f"Error playing sound: {e}")

            threading.Thread(target=play, daemon=True).start()

    def run(self):
        """Start the application"""
        self.root.mainloop()


if __name__ == "__main__":
    # Start fetching online time in background
    threading.Thread(target=get_online_datetime, daemon=True).start()

    expiry = load_license_encrypted()
    if expiry:
        if get_cached_datetime() < expiry:
            activation_info = {"activated": True, "expiry": expiry}
        else:
            messagebox.showerror("Expired", "Your Software License Has Expired")
            if os.path.exists(LICENSE_FILE):
                os.remove(LICENSE_FILE)
            activation_info = activate_window()
    else:
        activation_info = activate_window()

    if not activation_info["activated"]:
        sys.exit()

    check_expiry_once(activation_info["expiry"])

    app = EmailSenderApp()
    app.run()















