# ICT Zoho Recruit - Documentation

## Overview

ICT Zoho Recruit is a Frappe application that integrates ERPNext with Zoho Recruit API to automate job posting workflows. The primary functionality is to automatically create and post job openings in Zoho Recruit when employees leave the company, using the employee's role and related job details.

## Project Structure

```
ict_zoho_recruit/
├── ict_zoho_recruit/
│   ├── api/                          # API endpoints
│   │   ├── ZohoRecruit.py           # Main API for job posting and sync
│   │   ├── RoleProfile.py           # Role profile data retrieval
│   │   ├── Address.py               # Address utilities
│   │   └── test.py                  # API testing
│   ├── config/                       # Configuration files
│   ├── doc_events/                   # Document event hooks
│   │   ├── file/                    # File attachment events
│   │   └── zoho_job_openings/       # Job opening events
│   ├── fixtures/                     # Data fixtures
│   │   └── email_template.json      # Email template for notifications
│   ├── hooks.py                      # Frappe hooks configuration
│   ├── patches/                      # Database migration patches
│   ├── public/                       # Public assets (JS, CSS)
│   ├── templates/                    # Jinja templates
│   ├── utils/                        # Utility modules
│   │   ├── ZohoService.py           # Zoho Recruit API service
│   │   ├── ZohoToken.py             # OAuth token management
│   │   ├── ZohoRequest.py           # Base HTTP request handler
│   │   ├── Template.py              # Job opening payload templates
│   │   ├── EmailService.py          # Email notification service
│   │   └── EventScheduler.py        # Scheduled job processor
│   └── ict_zoho_recruit/
│       └── doctype/                  # Custom DocTypes
│           ├── zoho_job_openings/   # Job opening document
│           └── zoho_recruit_settings/ # Settings document
├── pyproject.toml                    # Python project configuration
├── README.md                        # Basic project information
└── license.txt                      # MIT License
```

## How It Works

### Core Workflow

1. **Employee Exit Detection**: The system monitors employees with status "Left" and today's relieving date
2. **Auto Job Creation**: Automatically creates a "Zoho Job Openings" document using the employee's role profile
3. **Zoho Sync**: Syncs the job opening to Zoho Recruit API
4. **Attachment Upload**: Uploads attached files to Zoho Recruit
5. **Email Notification**: Sends notification email to configured contact

### Key Components

#### 1. DocTypes

**Zoho Recruit Settings** (`zoho_recruit_settings`)
- Single document type for app configuration
- Stores OAuth credentials and integration settings
- Controls feature toggles (auto-posting, email notifications, etc.)

**Zoho Job Openings** (`zoho_job_openings`)
- Document representing a job posting
- Contains job details, requirements, benefits, skills
- Tracks sync status with Zoho Recruit
- Naming pattern: `ZR.-.#####`

#### 2. API Endpoints

**`auto_job_posting(employee, vacancy=1)`**
- Creates a job opening from an exiting employee
- Fetches role profile details and skills
- Populates job opening with employee's designation, department, etc.

**`sync_zoho_recruit(document_ids, operation="create")`**
- Syncs job openings to Zoho Recruit API
- Supports create and update operations
- Handles attachment uploads
- Sends email notifications on successful creation

**`get_designation_skills(designation, list_format=False)`**
- Retrieves skills associated with a designation/role profile
- Returns as comma-separated string or list

#### 3. Utility Services

**ZohoToken Service**
- Manages OAuth 2.0 authentication with Zoho
- Handles access token refresh
- Stores tokens securely in settings

**ZohoRecruit Service**
- Main API service for Zoho Recruit operations
- Creates/updates job openings
- Uploads/deletes attachments
- Validates configuration

**Event Scheduler**
- Scheduled task running daily at 2 AM
- Detects employees who left today
- Triggers auto job posting for each employee

**Email Service**
- Sends notification emails when job openings are created
- Uses configurable email template

## Configuration

### Required Settings

Navigate to **Zoho Recruit Settings** in ERPNext to configure:

#### Authentication Configuration

1. **Enable Zoho Recruit Job Posting** (Checkbox)
   - Master toggle for the entire integration
   - Must be enabled for all features to work

2. **Applications Client ID** (Data)
   - Zoho Recruit OAuth Client ID
   - Obtain from Zoho Developer Console

3. **Applications Client Secret** (Password)
   - Zoho Recruit OAuth Client Secret
   - Obtain from Zoho Developer Console
   - Stored securely as password field

4. **Applications Code** (Data)
   - Authorization code from Zoho OAuth flow
   - Required for initial token generation

5. **Refresh Token** (Password - Auto-generated)
   - OAuth refresh token
   - Automatically populated after initial authentication

6. **Access Token** (Password - Auto-generated)
   - OAuth access token
   - Automatically refreshed using refresh token

#### Feature Toggles

7. **Enable Manual Job Posting** (Checkbox)
   - Allows manual creation of job openings
   - Users can manually create and sync job openings

8. **Enable Auto Job Posting** (Checkbox)
   - Enables automatic job posting on employee exit
   - Requires scheduler to be enabled

9. **Enable Auto Attachment Remover** (Checkbox)
   - Automatically deletes attachments from Zoho when deleted locally
   - Hooks into File document on_trash event

10. **Enable Notify Email** (Checkbox)
    - Sends email notifications when job openings are created
    - Requires contact email to be configured

#### Company & Default Settings

11. **Default Job Post Company** (Link to Company)
    - Company to use for auto job postings
    - Filters employees by this company for auto-posting

12. **Default Target Date Range** (Data)
    - Number of days to add to today for target date
    - Used when no specific target date is provided
    - Default: 30 days

13. **Default Job Post Benefits** (Text Editor)
    - Default benefits text for job postings
    - Used when role profile doesn't specify benefits

#### Email Configuration

14. **Job Publish Contact Email** (Data)
    - Email address to receive job opening notifications
    - Required when email notifications are enabled

### Role Profile Configuration

Each **Role Profile** should be configured with:

- **Designation**: Link to Designation document
- **Posting Title**: Custom title for job postings
- **Job Category**: IT, Admin, Sales, Design, HR
- **Custom Department**: Link to Department
- **Custom Industry Type**: Link to Industry Type
- **Custom Salary**: Salary amount
- **Custom Work Experience**: Experience level
- **Description**: Job description (HTML)
- **Custom Requirements**: Requirements (HTML)
- **Custom Benefits**: Benefits (HTML)
- **Skills**: Table of Designation Skills
- **Parent Role Profile**: For inheritance of missing fields

### Employee Configuration

Each **Employee** should have:

- **Custom Role Profile**: Link to Role Profile
- **Designation**: Employee's designation
- **Department**: Employee's department
- **Employment Type**: Full-time, Part-time, etc.
- **Company**: Company (must match default job post company for auto-posting)

## Installation

### Prerequisites

- Frappe Bench setup
- ERPNext installed
- Python 3.10+

### Installation Steps

```bash
# Navigate to your bench directory
cd $PATH_TO_YOUR_BENCH

# Get the app
bench get-app $URL_OF_THIS_REPO --branch develop

# Install the app
bench install-app ict_zoho_recruit

# Build assets
bench build

# Restart bench
bench restart
```

### Initial Setup

1. **Configure Zoho Recruit Settings**
   - Go to Zoho Recruit Settings in ERPNext
   - Enable "Enable Zoho Recruit Job Posting"
   - Enter Client ID, Client Secret, and App Code
   - Save to generate access and refresh tokens

2. **Configure Role Profiles**
   - Navigate to Role Profile list
   - Add custom fields to Role Profile if not present
   - Configure job-related fields (designation, salary, benefits, etc.)
   - Add skills to each role profile

3. **Configure Employees**
   - Ensure employees have custom_role_profile field
   - Link appropriate role profile to each employee

4. **Enable Scheduler** (for auto job posting)
   - Ensure Frappe scheduler is running
   - Auto job posting runs daily at 2 AM

## Usage

### Manual Job Posting

1. Navigate to **Zoho Job Openings** list
2. Click "New" to create a job opening
3. Fill in job details:
   - Link Role Profile to auto-populate many fields
   - Or manually enter designation, department, etc.
   - Add skills, requirements, benefits
   - Attach job summary or other documents
4. Save the document
5. Click "Sync to Zoho Recruit" button (custom action)
6. Job opening is created in Zoho Recruit
7. Email notification is sent (if enabled)

### Auto Job Posting

1. Configure Zoho Recruit Settings with:
   - Enable Auto Job Posting: Checked
   - Default Job Post Company: Set to your company
2. When an employee's status changes to "Left" with today's relieving date:
   - System automatically creates a Zoho Job Opening
   - Populates from employee's role profile
   - Syncs to Zoho Recruit at next scheduler run (2 AM)
3. Email notification sent to configured contact

### Syncing Existing Job Openings

1. Go to Zoho Job Openings list
2. Select job openings to sync
3. Use bulk action "Sync to Zoho Recruit"
4. System creates/updates records in Zoho

### Managing Attachments

- **Upload**: Attach files to Job Opening document
- **Sync**: Attachments automatically uploaded to Zoho on job sync
- **Delete**: If "Enable Auto Attachment Remover" is on, deleting local attachment also deletes from Zoho

## API Reference

### Endpoints

#### `auto_job_posting(employee, vacancy=1)`
- **Method**: POST
- **Access**: allow_guest=True
- **Parameters**:
  - `employee`: Employee ID (required)
  - `vacancy`: Number of positions (default: 1)
- **Returns**: Creates Zoho Job Opening document

#### `sync_zoho_recruit(document_ids, operation="create")`
- **Method**: POST
- **Access**: Whitelisted
- **Parameters**:
  - `document_ids`: List of job opening IDs (JSON array)
  - `operation`: "create" or "update"
- **Returns**: JSON with sync results for each document

#### `get_designation_skills(designation, list_format=False)`
- **Method**: GET
- **Access**: allow_guest=True
- **Parameters**:
  - `designation`: Role Profile or Designation name
  - `list_format`: Return as list (default: False, returns string)
- **Returns**: Skills as comma-separated string or list

## Troubleshooting

### Common Issues

**"Zoho Recruit integration is disabled"**
- Enable "Enable Zoho Recruit Job Posting" in settings

**"Zoho Recruit Client ID is missing"**
- Configure Client ID, Client Secret, and App Code in settings

**"Employee is not configured with a Role Profile"**
- Set custom_role_profile field on Employee document

**Job opening not syncing to Zoho**
- Check if is_complete is already set (already synced)
- Verify Zoho credentials are valid
- Check error logs for API errors

**Auto job posting not working**
- Ensure "Enable Auto Job Posting" is checked
- Verify "Default Job Post Company" is set
- Check that Frappe scheduler is running
- Verify employee's relieving_date is today

**Email notifications not sending**
- Enable "Enable Notify Email" in settings
- Configure "Job Publish Contact Email"
- Check email configuration in ERPNext

### Error Logs

Check Frappe error logs for detailed error messages:
- Go to Error Log in ERPNext
- Filter by "Zoho Recruit" for related errors

## Development

### Code Style

The project uses pre-commit for code quality:
- ruff (Python linting)
- eslint (JavaScript linting)
- prettier (JavaScript formatting)
- pyupgrade (Python syntax upgrading)

Enable pre-commit:
```bash
cd apps/ict_zoho_recruit
pre-commit install
```

### Adding New Features

1. **New DocType Fields**: Add to JSON config in doctype folder
2. **API Endpoints**: Add to api/ folder
3. **Utilities**: Add to utils/ folder
4. **Hooks**: Update hooks.py for events, schedulers, etc.
5. **Patches**: Add to patches/ folder for database migrations

### Testing

Run tests:
```bash
bench --site [site-name] run-tests --app ict_zoho_recruit
```

## License

MIT License - See license.txt for details

## Support

For issues and questions:
- Email: info@increatech.com
- Publisher: Increatech Business Solution Pvt Ltd
