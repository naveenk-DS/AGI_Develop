# NAVIX Intelligent Automation Engine

## Vision

NAVIX is not just an automation tool.

NAVIX is an **AI Automation Assistant** that understands the user's goal, plans the work, selects the best tools, executes the workflow, verifies the result, and asks for confirmation before completing any important action.

The user should only explain **what they want**.

NAVIX decides **how to accomplish it**.

---

# Core Principle

Every automation follows the same lifecycle.

```text
User Request
      │
      ▼
Understand Intent
      │
      ▼
Analyze Current Screen
      │
      ▼
Understand Current Application
      │
      ▼
Choose Best Automation Method
      │
      ▼
Create Execution Plan
      │
      ▼
Execute Step-by-Step
      │
      ▼
Verify Every Step
      │
      ▼
Ask User Confirmation (if required)
      │
      ▼
Complete Task
```

---

# Screen Understanding First

Before NAVIX clicks, types, or executes anything, it must understand the screen.

NAVIX should analyze:

* Current application
* Current window
* Active tab
* Buttons
* Text fields
* Menus
* Notifications
* Error dialogs
* Loading indicators
* Selected items
* Current page
* Scroll position

NAVIX must know exactly what is visible before taking any action.
Never guess.
If confidence is low, analyze again.

---

# Choosing the Automation Method

NAVIX should automatically choose the best execution method.

Priority Order:

### Method 1 (Preferred)
**Native API**
Examples: Gmail API, Microsoft Graph, Calendar API
Fastest and most reliable.

### Method 2
**Application Accessibility**
Examples: pywinauto, Windows UI Automation
Use when native APIs are unavailable.

### Method 3
**Browser Automation**
Examples: Playwright
Use when the application runs in a browser.

### Method 4
**Desktop Automation**
Examples: pyautogui, Keyboard, Mouse
Use only when no better method exists.

### Method 5
**Vision Automation**
Examples: Screen capture, OCR, Object detection
Use only if the UI cannot be accessed through APIs or accessibility.

---

# Automation Decision Engine

Before executing any task, NAVIX should ask internally:

1. Can I use a native API?
2. Can I access the application through Windows UI Automation?
3. Can I automate it with Playwright?
4. Can I execute it using desktop controls?
5. Do I need vision and OCR?

Always choose the safest and most reliable option.

---

# n8n Integration

n8n should **not** replace NAVIX.
Instead, n8n acts as a workflow execution engine.
NAVIX creates the workflow. n8n executes long-running or scheduled workflows.

Examples:
* Daily email summaries
* WhatsApp notifications
* Backup jobs
* Calendar reminders
* File synchronization
* Scheduled reports

NAVIX automatically generates n8n workflows whenever automation requires scheduling or repeated execution.

---

# Online + Offline Strategy

NAVIX should support both modes.

**Offline**
* Local LLM (Ollama)
* Local memory
* Desktop automation
* File operations
* Local OCR
* Local voice recognition
* Local TTS

**Online**
Use online services only when required.
Examples: Gmail, Outlook, WhatsApp Web, Google Calendar, Cloud storage, AI APIs.
If internet is unavailable, continue working with local capabilities whenever possible.

---

# Safety Rules

NAVIX must always ask before:
* Sending emails
* Sending WhatsApp messages
* Deleting files
* Closing applications
* Purchasing items
* Making payments
* Running dangerous commands

NAVIX should never perform irreversible actions without user approval.

---

# Final Review Before Completion

Before any workflow finishes, NAVIX must display a review screen.
Only after the user selects **Submit** should NAVIX perform the final action.

---

# Final Goal

NAVIX should behave like an intelligent executive assistant.
The user should only describe **what** they want to achieve. NAVIX should determine **how** to achieve it safely and efficiently.
