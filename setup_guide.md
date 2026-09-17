# Professional Email Sender - Setup & Usage Guide

## 📋 Quick Setup Instructions

### 1. Install Requirements
```bash
pip install -r requirements.txt
```

### 2. Gmail Setup (Recommended)
For Gmail accounts, you need to:
1. Enable 2-Factor Authentication in your Google Account
2. Generate an App Password:
   - Go to Google Account Settings > Security
   - Select "App passwords" (requires 2FA)
   - Generate password for "Mail" 
   - Use this password in the app (not your regular Gmail password)

### 3. Run the Application
```bash
python main.py
```

## 📧 Email Provider Settings

### Gmail
- SMTP Server: `smtp.gmail.com`
- Port: `587`
- Security: TLS/STARTTLS
- Password: Use App Password (not regular password)

### Outlook/Hotmail
- SMTP Server: `smtp-mail.outlook.com`
- Port: `587`
- Security: TLS/STARTTLS

### Yahoo
- SMTP Server: `smtp.mail.yahoo.com`
- Port: `587`
- Security: TLS/STARTTLS

## 📊 Excel File Format for Bulk Emails

Your Excel file should have a column with email addresses. The app will automatically detect columns named:
- `email`
- `emails`  
- `email_address`
- `email address`
- `recipient`
- `recipients`

### Example Excel Structure:
```
| Name          | email               | Company    |
|---------------|---------------------|------------|
| John Smith    | john@company.com    | ABC Corp   |
| Jane Doe      | jane@business.org   | XYZ Ltd    |
| Bob Johnson   | bob@startup.io      | Tech Inc   |
```

## 🔧 Usage Instructions

### Creating Email Profiles
1. Go to **Settings** tab
2. Click **"➕ Add New"** 
3. Fill in your email details:
   - Profile Name (e.g., "My Gmail")
   - Email Address
   - App Password
   - SMTP Server
4. Click **"💾 Save Profile"**

### Sending Single Emails
1. Select profile from dropdown
2. Fill in recipient, subject, message
3. Add attachments (browse)
4. Choose Plain Text or HTML format
5. Click **"🚀 Send Email"**

### Sending Bulk Emails
1. Upload Excel file with recipients
2. Select/deselect recipients as needed
3. Fill in subject and message
4. Monitor progress in real-time
5. View detailed logs

### Email History
- All sent emails are automatically logged
- Export history to CSV/Excel
- Auto-save enabled by default