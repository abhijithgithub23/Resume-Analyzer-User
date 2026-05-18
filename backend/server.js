const express = require('express');
const cors = require('cors');
const multer = require('multer');
const axios = require('axios');
const FormData = require('form-data');

const app = express();
const port = 4000;

// Setup CORS and JSON parsing
app.use(cors());
app.use(express.json());

// Setup Multer for handling file uploads (stored in memory for quick forwarding)
const storage = multer.memoryStorage();
const upload = multer({ storage: storage });

app.post('/api/analyze', upload.single('resume'), async (req, res) => {
    try {
        if (!req.file || !req.body.jobDescription) {
            return res.status(400).json({ error: 'Resume and Job Description are required.' });
        }

        // Prepare data to send to Python service
        const formData = new FormData();
        formData.append('resume', req.file.buffer, {
            filename: req.file.originalname,
            contentType: req.file.mimetype,
        });
        formData.append('job_description', req.body.jobDescription);

        // Call the Python NLP Service
        const pythonServiceUrl = 'http://127.0.0.1:5000/analyze';
        
        const response = await axios.post(pythonServiceUrl, formData, {
            headers: {
                ...formData.getHeaders(),
            },
        });

        // Send the Python response back to the React frontend
        res.json(response.data);

    } catch (error) {
        console.error('Error communicating with NLP service:', error.message);
        res.status(500).json({ error: 'Failed to analyze resume. Ensure Python service is running.' });
    }
});

app.listen(port, () => {
    console.log(`Node backend running on http://localhost:${port}`);
});