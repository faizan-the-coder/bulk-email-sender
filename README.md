# Bulk Email Sender

A desktop application for sending single or bulk emails from a spreadsheet of recipients, with attachments, templates, scheduled sending and send history.

## Overview

The app is built around four tabs — **Single Email**, **Bulk Email**, **Email History** and **Settings**. You import recipients from an Excel file, compose or reuse an HTML template, attach files by browsing or dragging them onto the window, and either send immediately or schedule the send for a specific date and time.

SMTP credentials are saved as sender profiles so you can switch between mail accounts. Sending runs on a background thread so the interface stays responsive.

## Features

- Single email and bulk email tabs
- Recipient import from Excel with a validated preview
- Attachments by file browser or drag and drop
- Reusable HTML email template
- Scheduled sending — pick a date and time and choose whether it applies to single, bulk, or both
- Email history
- Multiple sender profiles with saved SMTP settings
- Light and dark mode
- Sound feedback on completion and errors
- Demo licensing: a Fernet-encrypted expiry stored in `license.dat`, generated with `key.py`

## Screenshots

**Single email**

![Single email](screenshots/01-single-email.png)

**Recipient import**

![Recipients import](screenshots/02-recipients-import.png)

**Bulk email campaign**

![Bulk email campaign](screenshots/03-bulk-email-campaign.png)

**Attachments**

![Attachments](screenshots/04-attachments.png)

**Dark mode**

![Dark mode](screenshots/05-dark-mode.png)

## Tech Stack

| Layer | Technologies |
| --- | --- |
| Language / GUI | Python 3.10+, Tkinter with CustomTkinter |
| Recipient data | pandas with openpyxl (Excel) |
| Email | `smtplib` with `ssl`, `email` |
| Scheduling | `threading` and `time` |
| Licensing | `cryptography` (Fernet) |
| Other | tkinterdnd2 (drag and drop), tkcalendar (date picker), pygame (sound), requests (online time check) |

## Project Structure

```
bulk-email-sender/
├── main.py             # Application: tabs, sending, scheduling, profiles, history
├── key.py              # Demo licensing-key generator
├── setup.py            # Optional cx_Freeze packaging
├── setup_guide.md      # Step-by-step setup, including Gmail app passwords
├── sounds/             # Completion, success and error sound effects
├── screenshots/
├── requirements.txt
├── .env.example
└── .gitignore
```

## Installation

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

## Configuration

| Setting | Where it comes from | Notes |
| --- | --- | --- |
| `EMAIL_APP_FERNET_KEY` | Environment variable, read by `main.py` and `key.py` | Optional. If unset, an ephemeral demo key is generated and licensing keys will not verify across runs |
| SMTP host, port, email and app password | Entered in the app's **Settings** tab and saved as a sender profile | Not read from the environment |
| Scheduled send time | Optional online lookup via `timeapi.io`, falling back to the local clock | Used so scheduling is not fooled by a changed system clock |

`.env.example` lists `EMAIL_APP_FERNET_KEY`, `SMTP_EMAIL` and `SMTP_PASSWORD` as a reference. Only `EMAIL_APP_FERNET_KEY` is read from the environment; the SMTP credentials are configured in the Settings tab.

For Gmail you must use an **App Password**, not your normal account password. `setup_guide.md` walks through generating one.

## Running the Application

```bash
python main.py
```

Then open **Settings**, add a sender profile with your SMTP details, and import recipients on the **Bulk Email** tab.

## Demo Credentials

No inbox or SMTP credentials are shipped. Use your own test mailbox.

## Notes / Limitations

- Requires SMTP access. Most providers rate-limit bulk sending, so large campaigns will be throttled.
- The licensing layer is a demonstration Fernet check, not real DRM.
- Scheduling uses an in-process timer thread, so a scheduled send only fires while the app is running.
- Saved profiles (`email_profiles.json`, `selected_profile.json`) and `license.dat` are written to the working directory and are gitignored — they hold SMTP credentials and must never be committed.
- Development was AI-assisted: requirements, UI direction, debugging, testing and integration were done by the author; AI tooling assisted with scaffolding and boilerplate.
- Development dates are approximate. The project was published to GitHub as a single initial commit rather than being developed in public.

## Future Improvements

- Bounce handling and delivery analytics.
- Persist the schedule so pending sends survive an app restart.
