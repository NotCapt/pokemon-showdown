# Machine Learning Agent Guide — Pokémon Showdown 3v3

This guide explains how to design, train, and submit real Machine Learning algorithms (PyTorch, TensorFlow, Scikit-Learn, Q-Learning) for the PokéDuel 3v3 autonomous battle competition.

---

## 🏗️ Agent Interface Specification

Every submission must be a Python file (`.py`) defining a `PokemonAgent` class with a `decide(self, observation: dict) -> str` method:

```python
class PokemonAgent:
    def __init__(self):
        # Load pre-trained weights, models, or initialize policies
        pass

    def decide(self, observation: dict) -> str:
        # Evaluate observation and return action string
        return "move 1"
```

The portal is an evaluation runner, not a training environment. It calls
`decide()` during a real Pokémon Showdown battle and checks the returned
action. To train an RL policy, build a local training loop around the
Pokémon Showdown simulator (or use your own compatible battle-data pipeline),
then upload the final policy file to the portal. The portal does not expose a
public `reset()`/`step()` training API.

---

## 📊 Observation Data Structure

On each turn, `decide()` receives an `observation` dictionary containing real-time combat telemetry:

```python
{
    "turn": 4,                         # Current turn number
    "team_preview": False,             # True on team preview phase
    "force_switch": False,             # True if active Pokemon fainted and must swap
    "my_active": {
        "name": "Charizard",
        "types": ["Fire", "Flying"],
        "hp_percent": 82,              # Integer 0-100
        "boosts": {"atk": 1, "spe": 0},# Stat modification stages (-6 to +6)
        "condition": "243/297"
    },
    "foe": {
        "name": "Venusaur",
        "types": ["Grass", "Poison"],
        "hp_percent": 55
    },
    "my_team": [
        {"name": "Charizard", "hp_percent": 82, "active": True, "fainted": False},
        {"name": "Pikachu",   "hp_percent": 0,  "active": False, "fainted": True},
        {"name": "Gengar",    "hp_percent": 100,"active": False, "fainted": False}
    ],
    "valid_moves": [
        {
            "index": 1,
            "id": "flamethrower",
            "name": "Flamethrower",
            "type": "Fire",
            "category": "Special",
            "base_power": 90,
            "accuracy": 100,
            "type_multiplier": 2.0,    # Super effective against Grass!
            "stab": True               # Same Type Attack Bonus (1.5x)
        },
        {
            "index": 2,
            "id": "airslash",
            "name": "Air Slash",
            "type": "Flying",
            "category": "Special",
            "base_power": 75,
            "accuracy": 95,
            "type_multiplier": 2.0,
            "stab": True
        }
    ],
    "valid_switches": [
        {
            "index": 3,
            "name": "Gengar",
            "types": ["Ghost", "Poison"],
            "hp_percent": 100,
            "active": False,
            "fainted": False
        }
    ]
}
```

---

## 🎯 Action Output Format

Your `decide` function must return one of the following strings:
- `"move 1"`, `"move 2"`, `"move 3"`, `"move 4"`: Executes the move in the corresponding slot.
- `"switch 2"`, `"switch 3"`: Swaps to the benched teammate at slot index 2 or 3.
- `"team 123"`: Preferred team order during the team preview phase.

---

## 🧠 Sample Algorithms Included

You can find working ML agent implementations in the [`ml_algorithms/`](../ml_algorithms/) directory:

1. **[neural_net_agent.py](../ml_algorithms/neural_net_agent.py)**:
   - Deep Policy Network built in **PyTorch** (`torch.nn.Module`).
   - Encodes continuous battlefield states into an 18-dimensional feature tensor and predicts action logits through an MLP with LayerNorm and ReLU.
2. **[q_learning_agent.py](../ml_algorithms/q_learning_agent.py)**:
   - Tabular/Approximate Reinforcement Learning agent using state space discretization and $Q(s, a)$ expectation weighting.
3. **[decision_tree_agent.py](../ml_algorithms/decision_tree_agent.py)**:
   - Supervised ML policy using **Scikit-Learn's** `DecisionTreeClassifier`.
4. **[template_agent.py](../ml_algorithms/template_agent.py)**:
   - Bare starter boilerplate for developing custom models.

---

## ⚔️ Curated Balanced Pokémon Roster

To ensure fair competition, the platform features a curated tier of **24 competitive Pokémon** (Base Stat Totals between 489 and 600, fully evolved Smogon staples with competitive moves, items, abilities, and EV spreads).

See the dedicated documentation in **[docs/BALANCED_POKEMON_ROSTER.md](BALANCED_POKEMON_ROSTER.md)** for detailed breakdowns of all 24 Pokémon, their competitive roles (Sweepers, Tanks, Wallbreakers, Priority Finishers), movesets, and strategic counterplay.

---

## 🚀 How to Run in the Platform

1. In the platform UI on the right panel, select your **3 Pokémon** for Team 1 and Team 2.
2. In the **ML Algorithm** section for Player 1 and Player 2, click **Choose File** to upload your `.py` agent script (or select one of the built-in sample ML agents).
3. Click **Start Simulation**.
4. If the file is missing `PokemonAgent` or `decide(self, observation)`, click **Show Error** in the portal to see the exact validation message.
5. Watch the battle simulate in the Pokémon Showdown arena on the left and see the plain text winner announced upon completion.

> Deployment note: Netlify forwards uploaded Python agents to the separate Python Agent Service. Configure `PYTHON_SERVICE_URL` and `PYTHON_SERVICE_KEY` in Netlify, and `SERVICE_API_KEY` on the service. The repository includes a Render Free blueprint; an UptimeRobot `/health` monitor can reduce idle sleep. Uploaded agents should use the Python standard library unless the execution service image has been extended with additional packages.
