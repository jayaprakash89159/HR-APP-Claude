# WorkSphere HR Application: Features, Gaps, and Required Enhancements

**Assessment date:** 2026-09-09  
**Scope:** Django web application, REST API, Flutter mobile application, payroll and HR administration

## 1. Executive Summary

WorkSphere already has a broad HRMS foundation. The strongest current areas are employee records, authentication, attendance capture, leave applications, holiday data, approval workflows, and the underlying payroll database schema.

The largest gap is payroll execution. Salary structures, employee salary records, payroll periods, payslip records, earnings, deductions, Indian statutory fields, and PDF fields exist in the database models. However, the complete payroll business workflow is not implemented end to end.

The current version does **not** reliably provide all of the following:

- Admin screens to define reusable salary structures and components
- Admin screens to assign a salary structure and pay scale to an employee
- Payroll period creation and processing
- Calculation of payroll from approved attendance and approved leave
- Automated earnings and deductions calculation
- Payslip PDF generation
- Admin review and approval of a payroll period
- Admin release of approved payslips to employees
- Payroll payment marking and bank/payment reference management
- Mobile payslip listing, detail, PDF download, and release status

The database is prepared for many of these features, but database fields alone do not make the workflow operational.

## 2. What Is Currently Available

### 2.1 Authentication and Access Control

Implemented or partially implemented:

- JWT login API
- Refresh-token support
- Email-based authentication
- Role-based users
- Employee, manager, HR, payroll, and administrator roles
- Login history model
- Device-token model for push notifications
- User properties such as `can_manage_payroll`, `can_approve_leaves`, and `can_manage_employees`
- Protected API endpoints using authenticated permissions

Current limitation:

- The role properties exist, but every required admin workflow is not exposed through corresponding screens and APIs.

### 2.2 Employee Management

Implemented in the backend models and web administration areas:

- Employee identity and employee code
- Official and personal contact details
- Department
- Designation
- Reporting manager
- Location
- Cost center
- Employment type
- Joining date and confirmation details
- Probation and separation fields
- Employee status
- Profile photo
- Bank and statutory-related employee records
- Emergency contact, family, education, experience, and skill models

Needs improvement:

- A complete employee self-service profile in mobile
- Employee document upload and download in mobile
- Stronger validation for bank and statutory information
- Audit history visible to administrators

### 2.3 Attendance

Implemented:

- Mobile clock-in
- Mobile clock-out
- GPS latitude and longitude capture
- Reverse geocoding to an address
- Geo-fence validation against employee location
- Selfie capture at clock-in and clock-out
- Clock-in and clock-out source tracking
- Break-in and break-out backend endpoints
- Working-minute calculation
- Overtime-minute storage
- Late-minute calculation based on shift
- Attendance status such as present, absent, half-day, late mark, leave, holiday, and work from home
- Attendance history API
- Today attendance API
- Monthly summary endpoint in the backend
- Attendance approval status: pending, approved, rejected
- Admin/manager approval of attendance
- Attendance approval remarks
- Attendance regularization models
- Attendance reports based on approved attendance

Mobile implementation currently includes:

- Today clock card
- Clock-in and clock-out actions
- Monthly attendance list
- Location permission flow
- Camera/selfie flow

Current limitations:

- The mobile app does not yet expose break-in and break-out controls.
- Regularization request UI is not implemented in mobile.
- Work-from-home request and approval UI is not implemented in mobile.
- QR attendance flow is not implemented in the current mobile UI.
- Offline attendance queue and retry behavior are not implemented, despite offline-related package dependencies.
- The payroll engine does not yet consume approved attendance automatically.
- Attendance status and approval behavior need integration tests across payroll calculations.

### 2.4 Leave Management

Implemented:

- Leave types including casual, sick, earned, comp-off, maternity, paternity, bereavement, loss of pay, optional, and other leave
- Leave type configuration fields
- Leave balances by employee, leave type, and year
- Entitled, carried-forward, accrued, availed, lapsed, and encashed values
- Available balance calculation
- Leave applications
- From date and to date
- Reason
- Leave status: pending, approved, rejected, cancelled, and lapsed
- Manager and HR approval fields
- HR remarks
- Leave cancellation model
- Holiday calendar
- Holiday types and descriptions
- Leave types API
- Leave balances API
- Leave applications API
- Leave approval API
- Holidays API

Mobile implementation currently includes:

- Leave balances
- Leave type selection
- Leave application form
- Start and end date selection
- Reason entry
- Existing application list
- Application status
- Holiday calendar

Current limitations:

- The mobile form does not yet support half-day or first-half/second-half selection, although the model supports it.
- Leave document upload is not implemented in the mobile form.
- Leave balance validation is not enforced in the application API before creating an application.
- Business-day calculation does not currently exclude weekends and holidays; the current API counts calendar days.
- Multi-level manager and HR approval behavior needs a complete tested workflow.
- Leave approval/rejection screens are not implemented in the mobile application for managers or HR.

### 2.5 Holiday Calendar

Implemented:

- Holiday calendar model
- Holiday date, name, type, description, year, optional flag, location, and active flag
- Holidays API
- Mobile holiday display

Needs improvement:

- Admin CRUD screen for holidays should be clearly exposed.
- Holiday location filtering should be applied for employees in different locations.
- Holiday-aware leave-day calculation is required.
- Optional holiday selection workflow is not implemented.

### 2.6 Payroll Data Model

The backend currently contains models for:

- Salary structure
- Salary components
- Employee salary records
- Payroll period
- Payslip record
- Loan record

Salary component fields include:

- Earning or deduction type
- Fixed amount, percentage, percentage of CTC, or formula calculation type
- Taxable flag
- Statutory flag
- PF applicability
- ESI applicability
- Display order
- Active flag

Employee salary fields include:

- Employee
- Salary structure
- Annual CTC
- Monthly CTC
- Basic salary
- HRA
- Special allowance
- Medical allowance
- Conveyance allowance
- Other allowances
- Gross salary
- Effective dates
- Monthly, daily, or hourly salary type
- Revised-by user

Payroll period fields include:

- Month and year
- Period start and end dates
- Draft, processing, processed, approved, paid, and locked statuses
- Total employees
- Total gross
- Total deductions
- Total net
- Processed and approved users/timestamps
- Remarks

Payslip fields include:

- Attendance totals
- Present, absent, leave, LOP, and overtime values
- Earnings
- PF, ESI, professional tax, TDS, LWF, loan, advance, and other deductions
- Gross earnings
- Total deductions
- Net salary
- PDF file field
- Email-sent fields
- Draft, generated, approved, and paid statuses
- Payment date, payment mode, and bank reference

These models are a useful foundation, but the operational payroll workflow is missing or incomplete.

## 3. Payroll Features Currently Available

### Backend/API

Currently available:

- Employee payslip list API: `GET /api/v1/payroll/payslips/`
- Employee payslip detail API: `GET /api/v1/payroll/payslips/{id}/`
- Payroll summary API for payroll managers: `GET /api/v1/payroll/summary/`
- Payslip serialization with gross, deductions, net, attendance days, status, payment date, and PDF availability
- Admin visibility checks for payslip detail

### Web UI

Currently available or partially available:

- Payroll dashboard route
- Payroll summary cards
- Payslip listing section
- Payroll reports link
- Employee web payslip page
- Payslip detail modal
- Display of whether a PDF exists

## 4. Payroll Features Missing or Not Fully Functional

This is the most important gap list based on the reported issue.

### 4.1 Salary Structure Administration

Missing or incomplete:

- Admin UI to create a salary structure
- Admin UI to edit and deactivate a salary structure
- Admin UI to add salary components to a structure
- Admin UI to set component order
- Admin UI to choose fixed, percentage, CTC percentage, or formula calculation
- Validation that earning and deduction components are configured correctly
- Versioning of salary structures
- Effective-date history for structure changes
- Duplicate and overlap validation for salary assignments

Required capability:

An administrator or authorized payroll user should be able to define structures such as:

- Standard Monthly Employee
- Manager Grade A
- Contract Employee
- Intern
- Executive Grade B

Each structure should contain components such as Basic, HRA, Special Allowance, PF, ESI, Professional Tax, TDS, LWF, Bonus, and LOP.

### 4.2 Employee Pay Scale and Salary Assignment

Missing or incomplete:

- Admin screen to assign a salary structure to an employee
- Admin screen to set annual CTC
- Admin screen to set monthly CTC
- Admin screen to set basic salary and component values
- Admin screen to choose monthly, daily, or hourly salary type
- Effective-from date
- Effective-to date
- Salary revision history
- Promotion or increment workflow
- Bulk salary assignment/import
- Validation that every active employee has one active salary record
- Salary assignment audit trail

Required capability:

An authorized payroll administrator should open an employee profile and configure:

- Pay scale or salary structure
- Annual CTC
- Monthly gross salary
- Basic salary
- Allowances
- Statutory applicability
- Effective date
- Revision reason

### 4.3 Payroll Period Management

Missing or incomplete:

- Create payroll period screen
- Select month and year
- Configure payroll start and end date
- Prevent duplicate periods
- Lock attendance input while processing
- Display employees missing salary data
- Display employees missing bank/statutory data
- Reopen or cancel a draft period with permission
- Close and lock a paid period

Required statuses and transitions:

```text
draft -> processing -> processed -> approved -> paid -> locked
```

Each transition must record the user, time, and remarks.

### 4.4 Attendance-to-Payroll Calculation

Missing:

- Payroll calculation service
- Automatic reading of approved attendance only
- Working-day calculation
- Present-day calculation
- Absent-day calculation
- Approved leave-day calculation
- Loss-of-pay calculation
- Half-day calculation
- Late and early deduction rules
- Overtime calculation from approved attendance
- Holiday and weekly-off treatment
- Joining date and last-working-day proration
- New joiner salary proration
- Exit employee salary proration
- Unpaid leave integration
- Attendance correction recalculation
- Recalculation audit trail

Important rule:

Only approved attendance should affect payroll. Pending or rejected attendance must not silently be included in the salary calculation.

### 4.5 Earnings Calculation

Missing:

- Component calculation engine
- Basic salary calculation
- HRA calculation
- Fixed allowance calculation
- Percentage-of-basic calculation
- Percentage-of-CTC calculation
- Formula evaluation with a safe formula language
- Bonus calculation
- Arrears calculation
- Overtime amount calculation
- Other earning inputs
- Gross earnings calculation
- Component-level calculation explanation

### 4.6 Deductions and Indian Statutory Payroll

The model contains statutory fields, but calculation workflows are not complete.

Required:

- Employee PF calculation
- Employer PF calculation
- ESI employee calculation
- ESI employer calculation
- Professional tax by state
- TDS calculation by tax regime
- Labour Welfare Fund by state
- Loan deduction integration
- Salary advance deduction integration
- LOP deduction
- Other deduction inputs
- Statutory ceiling and threshold rules
- Employee statutory profile validation
- Calculation breakdown and audit log
- Financial-year configuration
- Tax declaration and proof collection

These rules must be configurable and tested against Indian payroll requirements instead of being hard-coded only in templates or manual admin actions.

### 4.7 Payslip Generation

Missing or incomplete:

- Automatic creation of payslip records for all eligible employees
- Payslip number generation as part of processing
- PDF template
- PDF generation service
- Company logo and company information
- Employee identity and bank information
- Pay period and payment date
- Attendance summary
- Earnings table
- Deductions table
- Employer contribution table
- Net salary in numbers and words
- Tax and statutory identifiers
- Secure PDF storage
- PDF download API
- PDF access authorization
- Regeneration rules when payroll is recalculated

The web template links to a PDF route, but the payroll API URL configuration does not currently expose a matching PDF endpoint. This is one reason employees cannot reliably download payslips.

### 4.8 Admin Review, Approval, and Release

This directly addresses the requested administrator workflow.

Missing:

- Payroll period review screen
- Employee-by-employee payslip review
- Validation error list before approval
- Preview payslip PDF
- Approve payroll period action
- Reject or send back for correction
- Release payslips action
- Release only selected employees
- Release timestamp and releasing user
- Employee notification after release
- Prevent employee visibility before release
- Unrelease or rollback control with strict permission
- Lock period after payment
- Approval audit trail

Recommended separation:

```text
Payroll preparer -> Payroll reviewer -> Payroll approver -> Release/payment
```

At minimum, the system should require an authorized payroll administrator to explicitly approve and release a payroll period before employees can see its payslips.

### 4.9 Payment and Bank Processing

Missing:

- Payment batch generation
- Bank transfer file export
- Employee bank account validation
- Payment status tracking
- Payment date
- Payment mode
- Bank reference
- Failed payment handling
- Reconciliation report
- Paid-period locking

### 4.10 Payroll Notifications

Missing or incomplete:

- Notification when payslip is generated
- Notification when payslip is approved
- Notification when payslip is released
- Email with secure payslip link or attachment
- Mobile push notification
- Failed-email retry tracking

## 5. Mobile Application Current State

### Available in mobile

- Login screen
- JWT token storage
- Home dashboard
- Today attendance display
- Clock-in with location and selfie
- Clock-out with location and selfie
- Attendance history
- Leave balances
- Leave types
- Leave application form
- Leave application history
- Holiday calendar
- Profile route
- Payslip route placeholder
- Payslip navigation item

### Missing in mobile

- Real payslip list
- Payslip detail view
- Payslip PDF download
- Payslip sharing/opening
- Payroll release status
- Payment status
- Salary breakdown
- Earnings and deduction breakdown
- Manager leave approval
- HR leave approval
- Attendance regularization request
- Break controls
- Work-from-home request
- Leave document upload
- Half-day leave selection
- Offline attendance queue
- Reliable token refresh retry in all API calls
- Notification inbox
- Push notification registration workflow
- Biometric login flow, despite biometric dependencies being listed
- Firebase configuration and verified push delivery

The current `mobile/lib/screens/payslip_screen.dart` only displays a placeholder screen, so payroll must be implemented there after the backend payroll workflow is completed.

## 6. Other Application Gaps

### Recruitment

Needs verification or completion of:

- Candidate pipeline
- Interview scheduling
- Offer letter generation
- Candidate-to-employee conversion
- Recruitment permissions
- Recruitment mobile support

### Performance

Needs verification or completion of:

- Goal setting
- Review cycles
- Manager ratings
- Employee self-review
- Appraisal history
- Salary revision integration

### Documents

Needs verification or completion of:

- Employee document upload
- Document verification
- Expiry reminders
- Secure employee document access
- Mobile document access

### Notifications

Needs verification or completion of:

- In-app notification list
- Read/unread state
- Push token registration
- Email retry behavior
- Notification preferences

### Reports

Needs verification or completion of:

- Attendance reports
- Leave reports
- Payroll reports
- Department and employee filters
- Export to Excel/PDF
- Report permissions
- Report reconciliation against approved payroll

### Security and Audit

Needs verification or completion of:

- Payroll action audit events
- Salary change audit events
- Payslip access audit events
- PDF authorization and non-guessable download URLs
- Rate limiting on payroll endpoints
- Strong production secret configuration
- HTTPS-only mobile API communication in production
- Backup and restore testing

## 7. Recommended Implementation Order

### Phase 1: Payroll foundation

1. Create payroll admin permissions and route protection.
2. Register payroll models in Django Admin or build dedicated payroll admin screens.
3. Build salary component CRUD.
4. Build salary structure CRUD.
5. Build employee salary assignment and revision history.
6. Add validation for missing salary, bank, and statutory information.

### Phase 2: Payroll calculation

1. Create payroll period workflow.
2. Implement approved-attendance aggregation.
3. Implement approved-leave and LOP aggregation.
4. Implement salary proration.
5. Implement earning calculations.
6. Implement deduction and statutory calculations.
7. Add calculation previews and audit records.
8. Add payroll calculation tests with known expected totals.

### Phase 3: Payslip generation and approval

1. Generate payslip records.
2. Generate PDF files.
3. Add payslip preview.
4. Add payroll review screen.
5. Add approve/reject workflow.
6. Add release workflow.
7. Hide unreleased payslips from employees.
8. Add email and push notification after release.
9. Add paid status and payment references.
10. Lock the payroll period after payment.

### Phase 4: Mobile payroll

1. Add payslip API service.
2. Replace the placeholder mobile payslip screen.
3. Add payslip list and year filter.
4. Add payslip detail and earnings/deduction breakdown.
5. Add PDF download and secure opening.
6. Display generated, approved, released, and paid statuses.
7. Add payroll notifications.

### Phase 5: HR operations and quality

1. Add mobile leave documents and half-day support.
2. Add attendance regularization.
3. Add break and work-from-home workflows.
4. Add offline synchronization.
5. Add integration tests across attendance, leave, and payroll.
6. Add payroll reconciliation reports.
7. Add security, audit, and backup testing.

## 8. Suggested Payroll Acceptance Test

A payroll release should not be considered complete until this scenario passes:

1. Admin creates a salary structure.
2. Admin creates earning and deduction components.
3. Admin assigns the structure to an employee.
4. Admin enters annual CTC, monthly CTC, basic salary, and effective date.
5. Employee clocks in and clocks out.
6. Manager or HR approves the attendance.
7. Employee applies for leave.
8. Manager or HR approves the leave.
9. Admin creates the payroll period.
10. System calculates approved attendance and approved leave.
11. System calculates earnings, deductions, LOP, and net salary.
12. System generates a payslip record and PDF.
13. Payroll reviewer checks the calculation.
14. Payroll approver approves the period.
15. Admin releases the payslip.
16. Employee sees the payslip in web and mobile.
17. Employee downloads the PDF.
18. Admin marks payment date, payment mode, and bank reference.
19. System locks the period.
20. Audit log contains every salary, calculation, approval, release, download, and payment action.

## 9. Priority Summary

### Critical

- Payroll calculation engine
- Salary structure administration
- Employee salary assignment
- Attendance and leave integration
- Payslip PDF generation
- Payroll approval and release workflow
- Mobile payslip implementation
- Secure PDF endpoint

### High

- Statutory payroll calculation
- Salary revision history
- Payroll period locking
- Payment batch and reconciliation
- Payroll audit trail
- Email and push release notifications

### Medium

- Leave documents and half-day support
- Attendance regularization mobile UI
- Break and work-from-home mobile UI
- Offline attendance synchronization
- Payroll reports and exports

### Lower Priority

- Advanced tax declarations
- Bank file integrations
- Multi-company payroll
- Multi-country payroll
- Advanced performance-to-pay integration

## 10. Final Assessment

WorkSphere is currently a good HRMS foundation and a usable attendance/leave prototype. It is **not yet a complete payroll product**.

The payroll models show that the intended design includes salary structures, employee pay scales, statutory deductions, payroll periods, payslips, loans, approval, payment, and PDF storage. The missing work is the service layer, admin workflows, APIs, PDF generation, release controls, and mobile presentation that turn those models into a real payroll process.

The next development priority should be payroll administration and calculation before adding more mobile polish. Once payroll periods can be calculated, reviewed, approved, released, and downloaded correctly, the mobile payslip experience can be connected to the same verified backend data.
