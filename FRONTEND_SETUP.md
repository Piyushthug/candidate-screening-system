# Frontend Setup Guide

## React UI for Candidate Screening

A beautiful, interactive React dashboard for managing the screening workflow.

### Features Built

✅ **Job Selector** - Browse and select jobs to screen for  
✅ **Candidate Selection** - Check boxes to select candidates  
✅ **Screening Form** - View AI-generated results with fit score  
✅ **Approval Interface** - Approve/reject candidates  
✅ **Real-time Updates** - Live progress tracking  
✅ **Beautiful UI** - Modern gradient design  

### File Structure

```
frontend/
├── package.json              # Dependencies
├── vite.config.js            # Vite config
├── index.html                # Main HTML
├── src/
│   ├── main.jsx              # Entry point
│   ├── index.css             # Global styles
│   ├── App.jsx               # Main app component
│   ├── App.css               # App styles
│   ├── services/
│   │   └── api.js            # API client
│   └── components/
│       ├── JobSelector.jsx   # Job selection
│       ├── JobSelector.css
│       ├── CandidateList.jsx # Candidate selection
│       ├── CandidateList.css
│       ├── ScreeningForm.jsx # Screening interface
│       └── ScreeningForm.css
```

### Installation

**1. Install dependencies:**
```bash
cd frontend
npm install
```

This installs:
- React 18.2
- Vite (build tool)
- Axios (HTTP client)

**2. Start development server:**
```bash
npm run dev
```

Visit: **http://127.0.0.1:5173**

### Usage Flow

1. **Job Selection** → Select a job to screen candidates for
2. **Candidate Selection** → Check boxes to pick candidates
3. **Start Screening** → Begin the screening workflow
4. **Review Results** → See AI-generated scores and messages
5. **Approve/Reject** → Make hiring decisions
6. **Progress Tracking** → See your progress through candidates

### Backend Integration

The frontend connects to the FastAPI backend via API calls:

```javascript
// services/api.js
- GET /jobs - Fetch all jobs
- GET /candidates - Fetch candidates
- POST /screen/batch - Create screening batch
- POST /screen/{id}/start-workflow - Run workflow
- POST /screen/{id}/approve - Approve candidate
- POST /screen/{id}/reject - Reject candidate
```

**Base URL:** `http://127.0.0.1:8000`  
**CORS:** Configured in Vite proxy

### Building for Production

```bash
npm run build
```

Outputs to `dist/` folder. Deploy to:
- Vercel
- Netlify  
- GitHub Pages
- Static CDN

### Component Architecture

#### App.jsx (Main Container)
- Manages navigation between pages
- Loads jobs and candidates
- Handles state for screening workflow

#### JobSelector.jsx
- Displays available jobs
- Shows job details (requirements, level)
- Handles job selection

#### CandidateList.jsx
- Shows filterable candidate table
- Multi-select checkboxes
- Displays experience and skills

#### ScreeningForm.jsx
- Displays AI-generated fit score
- Shows personalized message
- Approve/reject buttons
- Progress bar
- Navigation between candidates

### Styling

- **Global Styles:** `index.css` (CSS variables, buttons, inputs)
- **Component Styles:** Each component has its own `.css` file
- **Theme:** Purple gradient (`#667eea` to `#764ba2`)
- **Responsive:** Mobile-friendly grid layout

### API Service (services/api.js)

Clean abstraction layer for all backend calls:

```javascript
// Example usage
const jobs = await screeningAPI.getJobs()
const response = await screeningAPI.createBatch(jobId, candidateIds)
await screeningAPI.startWorkflow(screeningId)
await screeningAPI.approve(screeningId, feedback)
```

### Environment

The frontend uses Vite's proxy to forward API calls:
- Frontend runs on `localhost:5173`
- Backend runs on `localhost:8000`
- Requests to `/api/*` are forwarded to backend

### Performance

- **Fast Refresh:** Instant UI updates during development
- **Code Splitting:** Components loaded on demand
- **Optimized Build:** Minified production bundle
- **CSS Variables:** Easy theme customization

### Troubleshooting

**API Connection Error**
- Ensure backend is running on `localhost:8000`
- Check CORS: backend should allow `localhost:5173`

**Modules Not Found**
- Run `npm install` again
- Delete `node_modules/` and reinstall

**Port Already in Use**
- Change port in `vite.config.js`
- Or kill the process: `lsof -i :5173`

### Next Steps

1. ✅ Install: `npm install`
2. ✅ Start backend: `python -m uvicorn backend.main:app --reload`
3. ✅ Start frontend: `npm run dev`
4. ✅ Open: http://127.0.0.1:5173
5. ✅ Start screening!

### Enhancement Ideas

- [ ] Dark mode toggle
- [ ] Candidate search/filter
- [ ] Message editing before approval
- [ ] Batch export results
- [ ] Analytics dashboard
- [ ] Email templates
- [ ] Multi-language support
- [ ] Keyboard shortcuts

---

**Status:** Ready to run ✅  
**Model:** React 18 + Vite  
**Styling:** CSS3 + CSS Variables  
**API:** Axios with Vite proxy
