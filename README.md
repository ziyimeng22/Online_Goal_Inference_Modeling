

````markdown
# Online Goal Inference Modeling

<div align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg"  alt="Python Version"/>
  <img src="https://img.shields.io/badge/framework-flask-green.svg" alt="Framework"/>
  <img src="https://img.shields.io/badge/socketio-4.7.5-orange.svg" alt="SocketIO Version"/>
  <img src="https://img.shields.io/badge/license-MIT-lightgrey.svg" alt="License"/>
</div>

<p align="center">
  <img src="https://raw.githubusercontent.com/ziyimeng22/Online_Goal_Inference_Modeling/main/public/assets/demo.gif"
       alt="Demo Animation" width="600"/>
</p>

## 🔍 Overview
This repository implements a **real‑time Bayesian framework** for inferring human goals from observed actions in interactive environments.  
Beliefs about user intentions are updated on‑the‑fly as they navigate, demonstrating how AI can reason about human behavior in real time.

The approach combines **Markov Decision Processes (MDPs)**, **Value Iteration**, and **Bayesian inference** to model human decision‑making—even when that behavior is boundedly rational.

---

## ✨ Key Features
- **Online Bayesian Inference** – live posterior updates as actions stream in  
- **Bounded Rationality** – softmax temperature captures sub‑optimal decisions  
- **Interactive Visualization** – web UI shows evolving belief states  
- **Flexible Maps** – drop‑in support for custom goals and obstacle layouts  
- **Real‑time Comms** – Flask + SocketIO for bidirectional server‑client updates  

---

## 🧠 The Science Behind It

### Bayesian Goal Inference
\[
P(\text{goal}\mid\text{actions}) \;\propto\; P(\text{actions}\mid\text{goal}) \times P(\text{goal})
\]

| Term | Meaning |
| ---- | -------- |
| **\(P(\text{goal}\mid\text{actions})\)** | Posterior over goals |
| **\(P(\text{actions}\mid\text{goal})\)** | Likelihood of observed actions given a goal |
| **\(P(\text{goal})\)** | Prior over goals |

### Value Iteration & Policies
```python
# Optimal state‑value function for each candidate goal
V[s] = max_a sum_{s'} T(s, a, s') * (R(s, a, s') + γ * V[s'])
````

Action likelihood under softmax policy:

```python
P(a | s, goal) ∝ exp(Q(s, a, goal) / temperature)
```

---

## 🚀 Getting Started

### Prerequisites

* Python 3.8+
* Node.js 12+ (front‑end build)

### Installation

```bash
# 1 – Clone the repo
git clone https://github.com/ziyimeng22/Online_Goal_Inference_Modeling.git
cd Online_Goal_Inference_Modeling

# 2 – Python deps
pip install -r requirements.txt

# 3 – Front‑end deps
npm install
```

### Running

```bash
# Start Flask + SocketIO server
python server.py
# then open http://localhost:3000 in your browser
```

---

## 📊 Example Usage

```python
from inference import UpdatePosteriorClass

custom_map = {
    "playerPosition": (0, 0),
    "goals":  [(9, 0), (9, 4), (9, 9)],
    "blocks": [(4, 0), (4, 1), (7, 1), (4, 3)]
}

update_posterior = UpdatePosteriorClass(custom_map)

state  = (5, 5)   # position after action
action = (1, 0)   # move right
posterior = update_posterior(state, action)

print(posterior)
# {'G1': 0.28, 'G2': 0.42, 'G3': 0.30}
```

---

## 📂 Project Structure

```
Online_Goal_Inference_Modeling/
├── ValueIteration.py    # Value‑iteration algorithm
├── inference.py         # Core Bayesian inference
├── server.py            # Flask + SocketIO backend
├── package.json         # Node.js deps
├── requirements.txt     # Python deps
├── public/              # Front‑end assets
│   ├── index.html
│   ├── style.css
│   ├── client.js
│   └── assets/
└── .vscode/             # Editor config
```

---

## 🔬 Technical Approach

1. **Policy Computation** – compute optimal policy for each goal (Value Iteration).
2. **Action Likelihood** – score observed actions under each policy.
3. **Posterior Update** – apply Bayes’ rule with softmax rationality.
4. **Temporal Decay** – optional decay on priors to capture changing intent.

<p align="center">
  <img src="https://raw.githubusercontent.com/ziyimeng22/Online_Goal_Inference_Modeling/main/public/assets/algorithm_flow.png"
       alt="Algorithm Workflow" width="700"/>
</p>

---

## 🎮 Interactive Demo

| Color              | Meaning              |
| ------------------ | -------------------- |
| 🟩 green           | goal cells           |
| 🟥 red             | obstacles            |
| 🟦 blue            | player               |
| 🟨 yellow → orange | posterior over goals |

Move around—beliefs update live!

---

## 📚 References

* Baker, C. L., Saxe, R., & Tenenbaum, J. B. (2009). *Action understanding as inverse planning*. **Cognition, 113**(3), 329‑349.
* Zhi‑Xuan, T., Mann, J. J., Silver, T., Tenenbaum, J. B., & Mansinghka, V. K. (2020). *Online Bayesian Goal Inference for Boundedly‑Rational Planning Agents*. **NeurIPS 33**.

---

## 📄 License

Distributed under the **MIT License**.
See [`LICENSE`](LICENSE) for details.

---

## 📧 Contact

**Your Name** · [your.email@example.com](mailto:your.email@example.com)
Project URL → [https://github.com/ziyimeng22/Online\_Goal\_Inference\_Modeling](https://github.com/ziyimeng22/Online_Goal_Inference_Modeling)

<p align="center">
  <a href="https://github.com/ziyimeng22/Online_Goal_Inference_Modeling/stargazers">
    <img src="https://img.shields.io/github/stars/ziyimeng22/Online_Goal_Inference_Modeling?style=social"
         alt="Stars"/>
  </a>
  <a href="https://github.com/ziyimeng22/Online_Goal_Inference_Modeling/network/members">
    <img src="https://img.shields.io/github/forks/ziyimeng22/Online_Goal_Inference_Modeling?style=social"
         alt="Forks"/>
  </a>
  <a href="https://github.com/ziyimeng22/Online_Goal_Inference_Modeling/issues">
    <img src="https://img.shields.io/github/issues/ziyimeng22/Online_Goal_Inference_Modeling?style=social"
         alt="Issues"/>
  </a>
</p>
```
