# Personalized Urban Daily Scheduling System using Deep Reinforcement Learning

## Overview
The **Personalized Urban Daily Scheduling System** is an intelligent itinerary recommendation platform that generates optimized daily schedules by considering Points of Interest (POIs), user preferences, travel constraints, and contextual factors such as time, distance, and weather conditions.  
The system leverages **Deep Reinforcement Learning (DRL)** to learn optimal scheduling policies that maximize schedule efficiency while minimizing travel time and constraint violations.

---

## Project Highlights
- Developed an intelligent daily schedule recommendation system using Deep Reinforcement Learning (DRL).
- Designed a custom Gymnasium reinforcement learning environment for itinerary optimization.
- Implemented priority-aware scheduling considering travel time, dwell time, and user constraints.
- Integrated real-time routing and contextual data sources to generate optimized and alternative daily plans.
- Built a modular REST API backend with scalable architecture for adaptive scheduling.

---

## Key Features
- Personalized daily schedule generation
- POI recommendation and prioritization
- Deep Reinforcement Learning–based itinerary optimization
- Travel time, dwell time, and constraint-aware planning
- Real-time routing integration using mapping APIs
- REST API backend with modular and scalable architecture
- Interactive visualization through a web-based frontend

---

## System Architecture
The system consists of:
- **Frontend:** Interactive web interface for schedule visualization
- **Backend:** FastAPI-based REST services for itinerary planning
- **Optimization Engine:** DRL-based scheduling optimizer using Gymnasium environments
- **Data Sources:** POI datasets, routing APIs, and contextual data providers
- **Database:** Local caching and user preference storage

---

## Technologies Used
- Python
- FastAPI
- Gymnasium (Custom RL Environment)
- Stable-Baselines3 (PPO Algorithm)
- TensorFlow / PyTorch
- OpenStreetMap / Google Maps APIs
- SQLite / MySQL
- TypeScript (Frontend)

---

## Project Structure
daily-schedule-planner/
├── app/                # Backend API modules
├── components/         # Frontend components
├── lib/                # Utility modules
├── public/             # Static assets
├── styles/             # Frontend styling
├── training/           # RL training scripts
├── requirements.txt    # Python dependencies
└── README.md


---

## Applications
- Smart urban travel planning
- Intelligent daily activity scheduling
- Personalized itinerary recommendation systems
- Smart city mobility optimization

---

## Future Enhancements
- Real-time adaptive learning based on user feedback
- Federated learning for privacy-preserving personalization
- Group scheduling optimization
- Multi-modal transportation planning
- Explainable AI-based scheduling recommendations

---

## Author
Bindhu S

## Team Members
- Bindhu S
- Levin K Varghese
- Santosh Reddy
- Tejashree M S
