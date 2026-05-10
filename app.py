from flask import Flask, render_template, request, jsonify
from datetime import datetime
import random

app = Flask(__name__)

# Données simulées en mémoire
data_store = {
    "user": {
        "name": "Koffi Amani",
        "role": "Producteur"
    },
    "balance": 250000,
    "harvests": [],
    "transactions": [
        {
            "amount": 12000,
            "type": "Paiement",
            "date": "07/05/2026 09:18:00"
        },
        {
            "amount": 8500,
            "type": "Paiement",
            "date": "05/05/2026 14:42:00"
        }
    ],
    "deliveries": [
        {
            "reference": "LIV-2401",
            "status": "En transit",
            "date": "08/05/2026 11:20:00"
        },
        {
            "reference": "LIV-2395",
            "status": "Livrée",
            "date": "04/05/2026 16:05:00"
        }
    ],
    "notifications": [
        {
            "title": "Compte vérifié",
            "message": "Votre portefeuille Orange Money est prêt à recevoir et envoyer des paiements.",
            "date": "Aujourd'hui"
        },
        {
            "title": "Marché du cacao",
            "message": "Consultez les prix et la météo avant de planifier votre prochaine vente.",
            "date": "Aujourd'hui"
        }
    ],
    "savings": {
        "available": 75000,
        "credit_limit": 150000,
        "next_due": "18/05/2026"
    }
}


def get_market_weather():
    # Données fictives dynamiques
    base_price = 1500
    variation = random.randint(-50, 80)
    price = base_price + variation

    weather_options = [
        "Ensoleillé",
        "Partiellement nuageux",
        "Temps chaud",
        "Brise légère",
        "Ciel dégagé"
    ]
    weather = random.choice(weather_options)

    return {
        "cocoa_price": price,
        "weather": weather,
        "updated_at": datetime.now().strftime("%H:%M:%S")
    }


def generate_ai_reply(message):
    msg = message.lower()

    if any(word in msg for word in ["prix", "cacao", "marché", "marche"]):
        market = get_market_weather()
        return (
            f"Le prix actuel simulé du cacao est de {market['cocoa_price']} FCFA/kg. "
            f"Je vous conseille de suivre l'évolution du marché avant de vendre une grande quantité."
        )

    if any(word in msg for word in ["météo", "meteo", "pluie", "soleil", "temps"]):
        market = get_market_weather()
        return (
            f"La météo du jour est : {market['weather']}. "
            f"Pensez à bien sécher les fèves au soleil et à protéger les sacs de l'humidité."
        )

    if any(word in msg for word in ["conseil", "engrais", "récolte", "recolte", "champ"]):
        return (
            "Conseil agricole : surveillez l'humidité, triez les cabosses saines, "
            "et stockez les fèves dans un endroit sec et ventilé."
        )

    if any(word in msg for word in ["bonjour", "salut", "bonsoir"]):
        return "Bonjour Koffi Amani, je suis votre assistant Cacao Pay. Je peux vous aider sur les prix, la météo et les conseils agricoles."

    return (
        "Je peux vous aider sur le prix du cacao, la météo et les conseils agricoles. "
        "Essayez par exemple : 'Quel est le prix du cacao ?' ou 'Donne-moi un conseil agricole'."
    )


def build_state_payload():
    market_weather = get_market_weather()
    total_harvest = sum(item["weight"] for item in data_store["harvests"]) if data_store["harvests"] else 0

    return {
        "success": True,
        "user": data_store["user"],
        "balance": data_store["balance"],
        "market_weather": market_weather,
        "harvests": data_store["harvests"][-5:],
        "total_harvest": total_harvest,
        "transactions": data_store["transactions"][-5:],
        "deliveries": data_store["deliveries"][-5:],
        "notifications": data_store["notifications"][-5:],
        "savings": data_store["savings"]
    }


@app.route("/")
def home():
    state = build_state_payload()
    return render_template(
        "index.html",
        user=state["user"],
        balance=state["balance"],
        market_weather=state["market_weather"],
        harvests=state["harvests"],
        transactions=state["transactions"],
        deliveries=state["deliveries"],
        notifications=state["notifications"],
        savings=state["savings"],
        total_harvest=state["total_harvest"]
    )


@app.route("/api/state", methods=["GET"])
def api_state():
    return jsonify(build_state_payload())


@app.route("/api/transaction", methods=["POST"])
def api_transaction():
    payload = request.get_json(silent=True) or {}
    amount = payload.get("amount")

    try:
        amount = int(amount)
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Montant invalide."
        }), 400

    if amount <= 0:
        return jsonify({
            "success": False,
            "message": "Le montant doit être supérieur à 0."
        }), 400

    if amount > data_store["balance"]:
        return jsonify({
            "success": False,
            "message": "Solde insuffisant."
        }), 400

    data_store["balance"] -= amount
    transaction = {
        "amount": amount,
        "type": "Paiement",
        "date": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }
    data_store["transactions"].append(transaction)
    data_store["notifications"].append({
        "title": "Paiement effectué",
        "message": f"Un paiement de {amount} FCFA a été validé avec succès.",
        "date": datetime.now().strftime("%H:%M")
    })

    return jsonify({
        "success": True,
        "message": f"Transaction de {amount} FCFA effectuée avec succès.",
        "new_balance": data_store["balance"],
        "transaction": transaction,
        "transactions": data_store["transactions"][-5:],
        "notifications": data_store["notifications"][-5:]
    })


@app.route("/api/market-weather", methods=["GET"])
def api_market_weather():
    return jsonify({
        "success": True,
        "data": get_market_weather()
    })


@app.route("/api/chat", methods=["POST"])
def api_chat():
    payload = request.get_json(silent=True) or {}
    message = payload.get("message", "").strip()

    if not message:
        return jsonify({
            "success": False,
            "reply": "Veuillez écrire une question."
        }), 400

    reply = generate_ai_reply(message)

    return jsonify({
        "success": True,
        "reply": reply
    })


@app.route("/api/harvest", methods=["POST"])
def api_harvest():
    payload = request.get_json(silent=True) or {}
    weight = payload.get("weight")

    try:
        weight = float(weight)
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Poids invalide."
        }), 400

    if weight <= 0:
        return jsonify({
            "success": False,
            "message": "Le poids doit être supérieur à 0."
        }), 400

    harvest = {
        "weight": weight,
        "date": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }
    data_store["harvests"].append(harvest)
    data_store["notifications"].append({
        "title": "Nouvelle récolte enregistrée",
        "message": f"{weight} kg ont été ajoutés à votre suivi de marchandises.",
        "date": datetime.now().strftime("%H:%M")
    })

    total_harvest = sum(item["weight"] for item in data_store["harvests"])

    return jsonify({
        "success": True,
        "message": f"Récolte de {weight} kg enregistrée.",
        "harvest": harvest,
        "total_harvest": total_harvest,
        "harvests": data_store["harvests"][-5:],
        "notifications": data_store["notifications"][-5:]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
