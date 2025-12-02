import React, { useState, useEffect } from 'react';
import MachineCard from './components/MachineCard';
import './App.css';

function App() {
    const [machines, setMachines] = useState({});

    useEffect(() => {
        const ws = new WebSocket('ws://localhost:8000/ws/andons');

        ws.onopen = () => {
            console.log('Connected to WebSocket');
        };

        ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                if (message.type === 'telemetry') {
                    const { device_id, metrics } = message.data;
                    setMachines(prev => ({
                        ...prev,
                        [device_id]: { ...prev[device_id], ...metrics, last_seen: new Date().toLocaleTimeString() }
                    }));
                }
            } catch (e) {
                console.error('Error parsing message', e);
            }
        };

        return () => {
            ws.close();
        };
    }, []);

    return (
        <div className="App">
            <header className="App-header">
                <h1>Andon System Dashboard</h1>
            </header>
            <div className="grid-container" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '20px', padding: '20px' }}>
                {Object.entries(machines).map(([id, data]) => (
                    <MachineCard key={id} id={id} data={data} />
                ))}
            </div>
        </div>
    );
}

export default App;
