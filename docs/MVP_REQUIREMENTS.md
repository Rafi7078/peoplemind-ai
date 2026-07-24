# PeopleMind AI — MVP Requirements
## 1. Product Goal
PeopleMind AI is a local-first HR intelligence and management assistant for a single company.
The MVP helps an HR/Admin user:
- Ask questions from HR policy documents
- Screen and compare CVs
- Manage attendance records
- Draft HR emails with human approval
- View all modules from a React dashboard
## 2. MVP User
The MVP has one user type:
- HR/Admin
The MVP does not include:
- Employee login
- Multiple companies
- Multiple HR roles
- Public user registration
- Automatic HR decisions
## 3. MVP Modules
### 3.1 Document Assistant
The HR/Admin can:
- Upload PDF documents
- View uploaded documents
- Process PDF text page by page
- Index documents using local embeddings
- Search document content semantically
- Ask questions using a local LLM
- Receive page-level citations
- Receive a safe fallback when reliable evidence is unavailable
Fallback message:
`আপলোড করা document-এ এই প্রশ্নের নির্ভরযোগ্য উত্তর পাওয়া যায়নি।`
### 3.2 CV Screening
The HR/Admin will be able to:
- Upload job descriptions
- Upload multiple CVs
- Extract candidate information
- Compare candidates against job requirements
- View candidate match scores
- View strengths, gaps, and evidence
- Manually review all recommendations
AI scores are advisory only.
The system must not automatically reject candidates.
### 3.3 Attendance Management
The HR/Admin will be able to:
- Add employee attendance records
- View daily and monthly attendance
- Track present, absent, late, leave, and remote-work status
- View basic attendance summaries
- Export attendance reports later
### 3.4 Email Assistant
The HR/Admin will be able to:
- Generate HR email drafts
- Edit generated drafts
- Review recipients and content
- Approve before sending
The system must never send an AI-generated email without explicit human approval.
### 3.5 React Dashboard
The dashboard will provide:
- Secure admin login
- Navigation between modules
- Document Assistant interface
- CV Screening interface
- Attendance interface
- Email Assistant interface
- Basic system status and summaries
## 4. Technical Requirements
### Backend
- Python 3.11
- FastAPI
- SQLAlchemy
- SQLite for MVP
- JWT authentication
- Argon2 password hashing
- Pytest
### Frontend
- React
- TypeScript
- Vite
- Tailwind CSS
- Axios
- React Router
### Local AI
- Ollama
- Chat model: `qwen3:4b-instruct`
- Embedding model: `embeddinggemma`
- ChromaDB for vector storage
## 5. Security Requirements
- `.env` must never be committed
- JWT secrets must remain private
- Passwords must be hashed
- Uploaded files must be validated
- Duplicate PDFs must be detected
- Uploaded documents and databases must remain outside Git
- Protected API endpoints require authentication
- AI output must be treated as decision support
## 6. Current MVP Scope
Included:
- Single company
- One HR/Admin account
- Local AI processing
- PDF document assistant
- Manual human review
- Local development environment
Not included in the first MVP:
- Multi-company SaaS
- Employee self-service portal
- Payroll
- Biometric device integration
- Automatic recruitment rejection
- Automatic email sending
- Cloud deployment
- PostgreSQL migration
- Docker deployment
- OCR for scanned PDFs
## 7. Document Assistant Acceptance Criteria
The Document Assistant is considered complete when:
- Admin can log in
- Admin can upload a valid PDF
- Invalid and duplicate files are rejected
- Text is extracted page by page
- Documents can be indexed
- Semantic search returns relevant chunks
- Supported questions return grounded answers
- Answers contain valid page citations
- Unsupported questions return the exact fallback message
- Automated backend tests pass
Current status: Complete.
## 8. Development Order
1. Requirements definition
2. Environment and project foundation
3. Document Assistant backend
4. Document Assistant React frontend
5. CV Screening
6. Attendance Management
7. Email Assistant
8. Dashboard integration and final testing
## 9. Git Workflow
Every completed feature must follow:
1. Run tests
2. Review `git status`
3. Stage only safe source files
4. Commit with a meaningful message
5. Push to `origin/main`
6. Confirm the working tree is clean
