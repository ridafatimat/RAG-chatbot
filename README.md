# RAG-chatbot

A deployed full-stack RAG-based document chatbot that allows users to upload documents and ask questions from their own files. The system extracts text, chunks document content, stores document metadata, retrieves relevant context, and generates document-grounded answers with source/citation chunks.

## Live Demo

- Live Website: https://rag-assistant-chatbot-seven.vercel.app/
- Demo Video: https://drive.google.com/file/d/1nUOzyAW3QK5_ceAog9hSFCSBr6aRR2rV/view?usp=sharing
- GitHub Repository: https://github.com/ridafatimat/RAG-chatbot

---

## Project Overview

RAG Document Chatbot is a full-stack AI application built to make document understanding easier. Users can upload supported document files, view their saved document history, and ask questions based on the uploaded content.

The chatbot uses a Retrieval-Augmented Generation approach where the system first retrieves the most relevant document chunks and then generates an answer using that retrieved context. This helps produce answers that are more grounded in the uploaded documents instead of relying only on general AI knowledge.

---

## Key Features

- User authentication with login and registration
- Protected user-specific document workflows
- Multi-format document upload support
- Document text extraction and preview generation
- Saved document history
- Chat with uploaded documents
- Chat history per document
- Source/citation chunks shown with answers
- File type and file size validation
- Loading states and error handling
- Deployed frontend and backend
- Clean demo video for project walkthrough

---

## Supported File Types

The application supports text extraction from:

- PDF
- TXT
- DOCX
- PPTX
- CSV
- XLSX

---

## Tech Stack

### Frontend

- React
- Vite
- JavaScript
- CSS
- REST API integration
- Vercel deployment

### Backend

- FastAPI
- Python
- MongoDB
- ChromaDB / Vector Search concepts
- JWT Authentication
- HTTPOnly Cookie
- Password hashing
- Railway deployment

### Document Processing

- pypdf
- python-docx
- python-pptx
- pandas
- openpyxl

---

## How the RAG Pipeline Works

1. The user uploads a document.
2. The backend validates the file type and size.
3. Text is extracted from the uploaded document.
4. Extracted text is divided into smaller chunks.
5. Chunks are prepared for vector-based retrieval.
6. The user asks a question related to the uploaded document.
7. The system retrieves the most relevant document chunks.
8. The chatbot generates an answer using the retrieved context.
9. Source/citation chunks are displayed with the response.

---

## Main Pages

- Login Page
- Register Page
- Dashboard
- Upload Document Page
- Document History Page
- Document Chat Page

---

## API Features

The backend includes API routes for:

- User registration
- User login
- Document upload
- Fetching saved documents
- Deleting documents
- Chatting with selected documents
- Retrieving document-based responses

---

## Project Purpose

The purpose of this project was to build a practical AI-powered document assistant using full-stack development and RAG concepts. It helped me understand how frontend interfaces, backend APIs, authentication, databases, document parsing, vector search, and AI-based response generation work together in a real application.

---

## What I Learned

Through this project, I gained hands-on experience with:

- Building a full-stack AI-integrated web application
- Designing protected backend routes
- Implementing authentication workflows
- Handling file uploads and validations
- Extracting text from multiple document formats
- Working with document chunking and retrieval concepts
- Connecting a React frontend with a FastAPI backend
- Deploying frontend and backend separately
- Managing user-specific data and document history

---

## Installation and Setup

Follow these steps to run the project locally.

### 1. Clone the Repository

```bash
git clone https://github.com/ridafatimat/RAG-chatbot.git
cd RAG-chatbot
```

### 2. Setup Backend

Go to the backend folder:

```bash
cd backend
```

Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

Install backend dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file inside the backend folder and add:

```env
MONGO_URI=your_mongodb_connection_string
JWT_SECRET_KEY=your_secret_key
```

Run the backend server:

```bash
uvicorn app:app --reload
```

The backend will run on:

```text
http://localhost:8000
```

### 3. Setup Frontend

Open a new terminal and go to the frontend folder:

```bash
cd frontend
```

Install frontend dependencies:

```bash
npm install
```

Create a `.env` file inside the frontend folder and add:

```env
VITE_API_URL=http://localhost:8000
```

Run the frontend:

```bash
npm run dev
```

The frontend will run on:

```text
http://localhost:5173
```

---

## Deployment

The project is deployed using:

- Frontend: Vercel
- Backend: Railway
- Database: MongoDB

Live Website: https://rag-assistant-chatbot-seven.vercel.app/

---

## Future Improvements

- Add stronger API rate limiting
- Add admin dashboard
- Add advanced document analytics
- Add semantic search across all uploaded documents
- Add more detailed answer evaluation
- Add Docker support
- Add automated backend testing with pytest
- Add GitHub Actions CI workflow

---

## Author

Rida Fatima Tanvir and Easha Javed 
Computer Science Undergraduate  
FAST-NUCES Lahore  

Portfolio: https://ridafatimatanvir.netlify.app/  
GitHub: https://github.com/ridafatimat  
LinkedIn: linkedin.com/in/rida-fatima-tanvir-797759283
