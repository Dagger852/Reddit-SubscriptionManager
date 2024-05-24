const express = require('express');
const axios = require('axios');
const bodyParser = require('body-parser');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = 3000;

app.use(bodyParser.json());
app.use(express.static('public'));

// Endpoint to get subscriptions (mocked for demonstration)
app.get('/api/subscriptions', (req, res) => {
    const subscriptions = [
        { name: 'r/javascript', type: 'subreddit', rename: 'javascript', add: 'Yes', tags: '', jdown: '', rank: '', ofVip: '', ofFree: '', rg: '', ph: '' },
        { name: 'u/someuser', type: 'user', rename: 'someuser', add: 'No', tags: '', jdown: '', rank: '', ofVip: '', ofFree: '', rg: '', ph: '' }
    ];
    res.json(subscriptions);
});

// Endpoint to save subscriptions (mocked for demonstration)
app.post('/api/subscriptions', (req, res) => {
    const subscriptions = req.body;
    // Save subscriptions to a file or database
    fs.writeFileSync('subscriptions.json', JSON.stringify(subscriptions, null, 2));
    res.status(200).send('Subscriptions saved');
});

app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});
