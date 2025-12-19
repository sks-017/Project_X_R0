# 🏭 Industrial Production Control System

> Real-time Andon system for 8-cell injection molding lines. Handles 500+ tags/second via Mitsubishi MC Protocol. Built to replace manual logbooks.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## ✨ Features

- **Real-Time OEE Monitoring** - Track Availability × Performance × Quality metrics
- **48-Zone Thermal Heatmaps** - Interactive temperature monitoring for injection molding machines
- **PLC Integration Ready** - Mitsubishi R Series (MC Protocol), Modbus, OPC UA support
- **JWT Authentication** - Secure login with Role-Based Access Control (Admin, Manager, Operator)
- **Beautiful Dark UI** - Industrial-grade dashboard with Plotly visualizations
- **Data Export** - Export production data to CSV/Excel
- **Multi-Machine Support** - Monitor 30+ machines simultaneously
- **Invisible Airbag Facility** - Specialized monitoring for TCM (Cutting) & VWM (Welding)

### 🚀 Coming in V2.0
- Predictive Maintenance (AI-powered RUL predictions)
- TechMate AI Chat Assistant (Natural language queries)
- Digital Twin (3D factory visualization)

## 🎯 Who Is This For?

- Automotive component manufacturers
- Injection molding plants (8+ machines)
- Factory automation integrators
- Industrial IoT solution providers
- Manufacturing consultants

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Windows/Linux/macOS

### Installation

```bash
# Clone the repository
git clone https://github.com/sks-017/Project_X_R0.git
cd Project_X_R0

# Install dependencies
pip install -r ingress-api/requirements.txt
pip install -r dashboard/requirements.txt
pip install -r edge/requirements.txt
```

### Run Demo (3 Terminals)

**Terminal 1: API**
```bash
cd ingress-api
uvicorn app.main:app --reload --port 8000
```

**Terminal 2: Dashboard**
```bash
cd dashboard
streamlit run Home.py
```

**Terminal 3: Data Gateway (Simulation)**
```bash
cd edge
python gateway.py
```

**Login:** `admin` / `admin123`

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────┐      ┌───────────┐
│   PLCs      │─────▶│ Gateway  │─────▶│    API    │
│ (Machines)  │      │ (Edge)   │      │ (FastAPI) │
└─────────────┘      └──────────┘      └─────┬─────┘
                                              │
                                        ┌─────▼─────┐
                                        │ Dashboard │
                                        │(Streamlit)│
                                        └───────────┘
```

## 🔌 PLC Integration

### Supported Protocols

| Protocol | Status | Library | Use Case |
|----------|--------|---------|----------|
| **Mitsubishi R Series** | ✅ Ready | `pymcprotocol` | MC Protocol (binary) |
| **Modbus TCP/RTU** | ✅ Ready | `pymodbus` | Universal PLC support |
| **OPC UA** | ✅ Ready | `opcua-asyncio` | Modern industrial standard |
| **MQTT** | ✅ Ready | `paho-mqtt` | Cloud-native IoT / Edge |

### Implementation Details

#### Mitsubishi MC Protocol
```python
from pymcprotocol import PLCClient

plc = PLCClient("localhost", port=5007)
plc.connect()
cycle_time = plc.read("D100")  # Read data register
```

#### Modbus TCP
```python
from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient('192.168.1.100', port=502)
registers = client.read_holding_registers(0, 10)
```

#### OPC UA
```python
from asyncua import Client

client = Client("opc.tcp://localhost:4840")
await client.connect()
node = client.get_node("ns=2;i=2")
value = await node.read_value()
```

**📖 See [Integration Guide](docs/MITSUBISHI_PLC_INTEGRATION.md) for complete setup instructions.**

## 📊 Tech Stack

- **Backend:** FastAPI, SQLAlchemy, Pydantic
- **Frontend:** Streamlit, Plotly (3D charts, heatmaps)
- **Database:** SQLite (dev) / PostgreSQL (production)
- **Security:** JWT (python-jose), Password Hashing (passlib)
- **Edge:** Python requests (batch ingestion)

## 📁 Project Structure

```
├── ingress-api/       # FastAPI backend
│   ├── app/
│   │   ├── main.py           # API endpoints
│   │   ├── auth.py           # JWT authentication
│   │   ├── models.py         # Database models
│   │   └── database.py       # Database connection
│   └── requirements.txt
├── dashboard/         # Streamlit frontend
│   ├── Home.py               # Main dashboard
│   ├── pages/                # Multi-page app
│   └── utils/                # Alert system, exports
├── edge/              # Data gateway (PLC simulator)
│   └── gateway.py
└── docs/              # Integration guides
```

## 🐳 Docker Deployment (Optional)

```bash
docker-compose up
```

Includes PostgreSQL with TimescaleDB for production-grade time-series data.

## 📖 Documentation

- [Startup Guide](STARTUP_GUIDE.md) - First-time setup
- [Mitsubishi PLC Integration](docs/MITSUBISHI_R_SERIES_INTEGRATION.md)
- [Real Machine Integration](docs/REAL_MACHINE_INTEGRATION.md)
- [Demo Script](docs/DEMO_SCRIPT.md) - Sales presentation guide

## ⚠️ Known Limitations

- **3D Visualization:** Robot position rendering requires WebGL enabled in the browser.
- **Data Export:** Exporting >10,000 rows to CSV may cause browser lag on older machines.
- **Refresh Rate:** Default 5s polling may saturate low-bandwidth networks (configurable in settings).

## 💼 Commercial Use & Support

**Free for:**
- Personal projects
- Educational institutions
- Open-source projects

**Commercial License Required for:**
- Production deployments in factories
- Revenue-generating applications

**Services Available:**
- Custom PLC integrations - ₹25,000 per protocol
- Factory deployment & setup - ₹1,50,000 - ₹5,00,000 (Tentative)
- Training workshops - ₹50,000/day
- Annual support contracts

📧 Contact:sk.shukla27@outlook.com

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md)

## 📝 License

Dual licensed:
- MIT License (see [LICENSE](LICENSE)) for non-commercial use
- Commercial License available - contact for pricing

## 🙏 Acknowledgments

Built with modern industrial IoT best practices for the automotive manufacturing industry.

---

**⭐ Star this repo if you find it useful!**
