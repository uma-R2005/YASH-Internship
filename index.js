// Simple Node.js Express Server
// (Simulating Copilot generated code)

const express = require('express');
const app = express();
const PORT = 3000;

app.get('/', (req, res) => {
    res.json({ message: 'Hello from Git AI test project!' });
});

app.get('/users', (req, res) => {
    const users = [
        { id: 1, name: 'Alice', role: 'developer' },
        { id: 2, name: 'Bob', role: 'designer' }
    ];
    res.json(users);
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
