import React from 'react';

const MachineCard = ({ id, data }) => {
    const isRunning = data.cycle_time > 0; // Simple logic
    const statusColor = isRunning ? 'green' : 'red';

    return (
        <div style={{ border: `2px solid ${statusColor}`, borderRadius: '8px', padding: '16px', backgroundColor: '#f9f9f9' }}>
            <h3>{id}</h3>
            <p>Status: <span style={{ color: statusColor, fontWeight: 'bold' }}>{isRunning ? 'RUNNING' : 'STOPPED'}</span></p>
            <p>Cycle Time: {data.cycle_time?.toFixed(2)} s</p>
            <p>Mold Temp: {data.mold_temp?.toFixed(1)} °C</p>
            <p>Last Update: {data.last_seen}</p>
        </div>
    );
};

export default MachineCard;
